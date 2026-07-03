"""
Configuración centralizada para utilidades Saint Enterprise / AMC.
Usa ZeroTier para conexiones remotas desde cualquier ubicación.

Fuente de credenciales: carpeta source de la PC de Dario (ZeroTier 10.147.18.43).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# --- ZeroTier (SD-WAN AMC) ---
ZEROTIER_SQL_HOST = "10.147.18.192"       # SRV-DC-AMC (SQL Server Saint)
ZEROTIER_SQL_INSTANCE = "efficacis3"
ZEROTIER_PC_HOST = "10.147.18.43"         # Dario Desktop AMC
ZEROTIER_WEBSERVICES = "10.147.18.204"    # Debian / n8n / Docker

# LAN fallback (solo cuando estás en la red local AMC)
LAN_SQL_HOST = "10.200.8.5"

DB_NAME = "EnterpriseAdmin_AMC"
DB_USER = "sa"

# Rutas locales en la PC de Dario (orden de búsqueda)
LOCAL_SOURCE_CANDIDATES = [
    Path(r"C:\source"),
    Path(r"C:\Users\DARIO LUBISCO\OneDrive\Sistemas\AntigravityBK\source"),
    Path.home() / "OneDrive" / "Sistemas" / "AntigravityBK" / "source",
]

CREDENTIALS_REL = Path("N8N") / "synapse_credentials.md"
GLOBAL_VARS_REL = Path("N8N") / "config" / "global_vars.json"


def find_local_source_root() -> Path | None:
    """Encuentra la carpeta source en esta máquina."""
    env = os.environ.get("AMC_SOURCE_ROOT")
    if env:
        p = Path(env)
        if p.is_dir():
            return p

    for candidate in LOCAL_SOURCE_CANDIDATES:
        if candidate.is_dir() and (candidate / CREDENTIALS_REL).exists():
            return candidate
    return None


def _parse_sql_password_from_md(text: str) -> str | None:
    """Extrae password MSSQL sa del markdown de credenciales."""
    m = re.search(r"\*\*MSSQL\*\*.*?\|\s*`sa`\s*/\s*`([^`]+)`", text, re.DOTALL)
    return m.group(1) if m else None


def load_db_password() -> str:
    """Carga password SQL desde env, archivo local o SSOT markdown."""
    if pw := os.environ.get("MSSQL_SA_PASSWORD"):
        return pw

    root = find_local_source_root()
    if root:
        cred_file = root / CREDENTIALS_REL
        if cred_file.is_file():
            text = cred_file.read_text(encoding="utf-8", errors="replace")
            if pw := _parse_sql_password_from_md(text):
                return pw

    raise RuntimeError(
        "No se encontró MSSQL_SA_PASSWORD. "
        "Define la variable de entorno o crea .env en la raíz de source."
    )


def get_sql_server(use_zerotier: bool = True) -> str:
    """Retorna host\\instancia para pyodbc."""
    host = ZEROTIER_SQL_HOST if use_zerotier else LAN_SQL_HOST
    return f"{host}\\{ZEROTIER_SQL_INSTANCE}"


def get_connection_string(use_zerotier: bool = True) -> str:
    """Cadena ODBC para EnterpriseAdmin_AMC."""
    prefer_zerotier = os.environ.get("AMC_USE_ZEROTIER", "1") != "0"
    if not use_zerotier:
        prefer_zerotier = False

    server = get_sql_server(use_zerotier=prefer_zerotier)
    password = load_db_password()

    # Driver: Windows usa ODBC 17; Linux usa FreeTDS (tdsodbc)
    if sys.platform == "win32":
        driver = "{ODBC Driver 17 for SQL Server}"
        return (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};PWD={password};"
            f"Encrypt=yes;TrustServerCertificate=yes;"
        )

    # Linux/Debian: host sin backslash de instancia; FreeTDS resuelve por puerto
    host_only = ZEROTIER_SQL_HOST if prefer_zerotier else LAN_SQL_HOST
    port = os.environ.get("MSSQL_PORT", "1433")
    return (
        "DRIVER={FreeTDS};"
        f"SERVER={host_only};"
        f"PORT={port};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};PWD={password};"
        "TDS_Version=7.4;"
    )


def connect():
    """Abre conexión pyodbc con fallback LAN si ZeroTier falla."""
    import pyodbc

    for zerotier in (True, False):
        try:
            conn = pyodbc.connect(get_connection_string(use_zerotier=zerotier))
            label = "ZeroTier" if zerotier else "LAN"
            print(f"Conectado via {label}: {get_sql_server(use_zerotier=zerotier)}")
            return conn
        except Exception as e:
            if not zerotier:
                raise
            print(f"ZeroTier falló ({e}); intentando LAN...")
    raise RuntimeError("No se pudo conectar al SQL Server")
