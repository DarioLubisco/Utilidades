"""
Cierre de mes automático Saint (EnterpriseAdmin_AMC) — modo desatendido.

Réplica del flujo recomendado del .BAT "Saint Enterprise - Utilidades AMC"
del escritorio de Dario (DARIO-DESKTOP), sin interacción humana:

    1. Backup de tablas  -> backup_tables.py SACONF SAITEMCOM SALOTE   (opción 4)
    2. Fechas futuras    -> fix_fechas_futuras_saitemcom_salote.py     (opción 2)
    3. Cierre SACONF     -> fix_saconf_dates_yesterday.py              (opción 1)
    4. Post-checks (0 fechas futuras, MesCurso/FechaUC coherentes)
    5. Notificación Telegram (TELEGRAM_AMC_NOTIFICACION_BOT -> ERROR_CHAT_ID)
       + correo (cuenta FarmaciaAmericanaCaracas vía Gmail SMTP app-password)

Los pasos 1-3 son los mismos scripts probados del menú del BAT; son
idempotentes (gate needs_fix / sin filas -> no-op), así que re-ejecutar
no vuelve a cerrar nada ya cerrado.

Credenciales: se resuelven de /home/synapse/source/N8N/synapse.credentials
(DB_PASSWORD -> MSSQL_SA_PASSWORD; TELEGRAM_AMC_NOTIFICACION_BOT;
ERROR_CHAT_ID; GOOGLE_GMAIL_USER + GOOGLE_GMAIL_APP_PASSWORD).
Destino del correo: variable de entorno AMC_ALERT_EMAIL o dario.lubisco@gmail.com.

Uso:
    python3 cierre_mes_automatico.py                # cierre completo + notifica
    python3 cierre_mes_automatico.py --dry-run      # solo lectura: estado y qué haría
    python3 cierre_mes_automatico.py --test-notify  # mensaje PRUEBA (no toca la BD)
"""
from __future__ import annotations

import json
import os
import re
import smtplib
import subprocess
import sys
import traceback
import urllib.request
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = Path(
    os.environ.get("SYNAPSE_CREDENTIALS", "/home/synapse/source/N8N/synapse.credentials")
)
LOG_DIR = BASE_DIR / "logs"
SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 465
DEFAULT_ALERT_EMAIL = "dario.lubisco@gmail.com"

# util_config resuelve la password SQL vía env; alimentarlo ANTES de importarlo.
os.environ.setdefault("AMC_SOURCE_ROOT", "/home/synapse/source")

_CRED_CACHE: dict[str, str] = {}


def cred(name: str) -> str:
    """Lee VARIABLE=valor de synapse.credentials (una sola lectura, cacheado)."""
    if not _CRED_CACHE:
        for line in CREDENTIALS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, _, v = line.partition("=")
                _CRED_CACHE.setdefault(k.strip(), v.strip())
    if name not in _CRED_CACHE or not _CRED_CACHE[name]:
        raise RuntimeError(f"Variable {name} no encontrada en {CREDENTIALS_FILE}")
    return _CRED_CACHE[name]


if not os.environ.get("MSSQL_SA_PASSWORD"):
    try:
        os.environ["MSSQL_SA_PASSWORD"] = cred("DB_PASSWORD")
    except RuntimeError:
        pass  # load_db_password() intentará su propia vía y fallará con mensaje claro

from util_config import connect  # noqa: E402  (importar tras resolver la password)

# Misma fórmula que fix_saconf_dates_yesterday.py (este servidor está en
# America/Caracas, igual que la farmacia).
YESTERDAY = date.today() - timedelta(days=1)
CURRENT_MONTH = int(YESTERDAY.strftime("%Y%m"))
NEXT_MONTH = CURRENT_MONTH + 1 if CURRENT_MONTH % 100 < 12 else CURRENT_MONTH + 89

BACKUP_TABLES = ["SACONF", "SAITEMCOM", "SALOTE"]
BACKUP_OK_RE = re.compile(r"\[(\w+)\] (OK|REVISAR): (dbo\.\S+) \((\d+) filas\)")
BACKUP_SUMMARY_RE = re.compile(r"Resumen: (\d+)/(\d+) backup")


# ────────────────────────── pasos del flujo ──────────────────────────


def run_step(script: str, args: list[str] | None, log) -> str:
    """Ejecuta uno de los scripts del menú y captura su salida."""
    cmd = [sys.executable, script, *(args or [])]
    print(f"\n>>> {script} {' '.join(args or [])}")
    proc = subprocess.run(
        cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=3600
    )
    out = proc.stdout.strip()
    if proc.stderr.strip():
        out += "\n[stderr]\n" + proc.stderr.strip()
    log.write(f"\n===== {script} {' '.join(args or [])} (rc={proc.returncode}) =====\n{out}\n")
    print(out)
    if proc.returncode != 0:
        raise RuntimeError(f"{script} terminó con código {proc.returncode}")
    return out


def postchecks(log) -> tuple[bool, str]:
    """Verificaciones de cierre: fechas futuras en 0 y SACONF coherente."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT MesCurso, FechaUC, FechaUP FROM SACONF")
    mes_curso, fecha_uc, fecha_up = cursor.fetchone()
    futuros: dict[str, int] = {}
    for tbl in BACKUP_TABLES[1:]:
        cursor.execute(
            f"SELECT COUNT(*) FROM {tbl} WHERE CONVERT(DATE, FechaE) > ?", YESTERDAY
        )
        futuros[tbl] = cursor.fetchone()[0]
    conn.close()

    try:
        mes_ok = int(mes_curso) >= NEXT_MONTH
    except (TypeError, ValueError):
        mes_ok = str(mes_curso).strip() >= str(NEXT_MONTH)
    fecha_uc_dia = fecha_uc.date() if hasattr(fecha_uc, "date") else fecha_uc
    fecha_ok = fecha_uc_dia is not None and fecha_uc_dia >= YESTERDAY
    fechas_ok = all(v == 0 for v in futuros.values())

    lines = [
        "=== POST-CHECK ===",
        f"  MesCurso={mes_curso} (esperado >= {NEXT_MONTH}) -> {'OK' if mes_ok else 'FALLO'}",
        f"  FechaUC={fecha_uc} (esperado >= {YESTERDAY}) -> {'OK' if fecha_ok else 'FALLO'}",
        f"  FechaUP={fecha_up}",
    ]
    for tbl, cnt in futuros.items():
        lines.append(f"  {tbl} con FechaE > ayer: {cnt} -> {'OK' if cnt == 0 else 'FALLO'}")
    ok = mes_ok and fecha_ok and fechas_ok
    lines.append(f"  RESULTADO: {'TODO OK' if ok else 'REVISAR'}")
    text = "\n".join(lines)
    log.write(text + "\n")
    print(text)
    return ok, text


# ────────────────────────── notificaciones ──────────────────────────


def notify_telegram(text: str) -> None:
    token = cred("TELEGRAM_AMC_NOTIFICACION_BOT")
    chat_id = cred("ERROR_CHAT_ID")
    payload = json.dumps(
        {"chat_id": chat_id, "text": text[:3900], "disable_web_page_preview": True}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def notify_email(subject: str, body: str) -> None:
    user = cred("GOOGLE_GMAIL_USER")
    password = cred("GOOGLE_GMAIL_APP_PASSWORD")
    to = os.environ.get("AMC_ALERT_EMAIL", DEFAULT_ALERT_EMAIL)
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def notify_all(ok: bool, report: str, errors: list[str]) -> None:
    emoji = "✅" if ok else "❌"
    subject = (
        f"[Saint AMC] Cierre de mes {'OK' if ok else 'CON ERRORES'} — {datetime.now():%d/%m/%Y %H:%M}"
    )
    body = f"{emoji} {subject}\n\n{report}"
    if errors:
        body += "\n\n[avisos de notificación]\n" + "\n".join(errors)
    try:
        notify_telegram(f"{emoji} {subject}\n\n{report[:3500]}")
    except Exception as e:
        errors.append(f"Telegram: {e!r}")
    try:
        notify_email(subject, body)
    except Exception as e:
        errors.append(f"Email: {e!r}")


# ────────────────────────── modos ──────────────────────────


def mode_dry_run() -> int:
    """Solo lectura: estado actual y qué haría la rutina. No escribe ni notifica."""
    print("MODO DRY-RUN (solo lectura; no se escribe nada ni se notifica)")
    print(f"  Ayer (FechaUC objetivo): {YESTERDAY} | MesCurso objetivo: {NEXT_MONTH}\n")
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT MesCurso, MesTran, FechaUC, FechaUP, FechaUV FROM SACONF")
    row = cursor.fetchone()
    print(f"SACONF actual: MesCurso={row[0]}, MesTran={row[1]}, "
          f"FechaUC={row[2]}, FechaUP={row[3]}, FechaUV={row[4]}")
    for tbl in BACKUP_TABLES[1:]:
        cursor.execute(
            f"SELECT COUNT(*) FROM {tbl} WHERE CONVERT(DATE, FechaE) > ?", date.today()
        )
        cnt = cursor.fetchone()[0]
        print(f"{tbl} con FechaE > hoy: {cnt}  "
              f"({'corregiría fechas' if cnt else 'no haría falta corregir'})")
    cursor.execute("SELECT MesCurso, FechaUC FROM SACONF")
    mes, fuc = cursor.fetchone()
    ya = (int(mes) >= NEXT_MONTH) and (fuc is not None and fuc.date() >= YESTERDAY)
    print(f"\nneeds_fix (cierre SACONF): {'NO — ya está cerrado' if ya else 'SÍ — se avanzaría MesCurso y se alinearían fechas'}")
    conn.close()
    return 0


def mode_test_notify() -> int:
    """Envía un mensaje PRUEBA a Telegram y correo. No toca la base de datos."""
    text = (
        "🔧 PRUEBA del cierre automático de mes Saint.\n"
        "Canales Telegram y correo operativos. No se ejecutó ningún cierre."
    )
    errors: list[str] = []
    notify_all(ok=True, report=text, errors=errors)
    if errors:
        print("FALLARON algunos canales:\n" + "\n".join(errors))
        return 2
    print("PRUEBA enviada por Telegram y correo OK.")
    return 0


def mode_run() -> int:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"cierre_mes_{stamp}.log"
    with log_path.open("w", encoding="utf-8") as log:
        report: list[str] = []
        errors: list[str] = []
        ok = False
        try:
            log.write(f"Cierre de mes automático — {datetime.now():%Y-%m-%d %H:%M:%S}\n")

            backup_out = run_step("backup_tables.py", list(BACKUP_TABLES), log)
            m = BACKUP_SUMMARY_RE.search(backup_out)
            made = int(m.group(1)) if m else 0
            total = int(m.group(2)) if m else len(BACKUP_TABLES)
            if made < total:
                raise RuntimeError(
                    f"Backup incompleto ({made}/{total}); se aborta antes de tocar datos."
                )
            report.append("1) Backup verificado:")
            report += [f"   {ln.strip()}" for ln in backup_out.splitlines() if BACKUP_OK_RE.search(ln)]

            fechas_out = run_step("fix_fechas_futuras_saitemcom_salote.py", None, log)
            if "Se detectaron" in fechas_out:
                n = fechas_out.split("Se detectaron")[1].split("líneas")[0].strip()
                report.append(f"2) Fechas futuras corregidas: {n} líneas (+ UpdatePrices)")
            else:
                report.append("2) Fechas futuras: 0 (nada que corregir)")

            cierre_out = run_step("fix_saconf_dates_yesterday.py", None, log)
            for ln in cierre_out.splitlines():
                if ln.strip().startswith(("MesCurso=", "SET ", "UPDATE SACONF")):
                    report.append(f"   {ln.strip()}")
            if "No SACONF date fix needed" in cierre_out:
                report.append("3) Cierre SACONF: no hizo falta (ya estaba cerrado)")

            ok, post_text = postchecks(log)
            report.append("4) " + post_text.replace("\n", "\n   "))
        except Exception as e:
            ok = False
            report.append(f"ERROR: {e}")
            log.write(traceback.format_exc() + "\n")
            print(traceback.format_exc())

        report_str = "\n".join(report)
        log.write(f"\n===== REPORTE FINAL =====\n{report_str}\n")
        notify_all(ok=ok, report=report_str, errors=errors)
        if errors:
            log.write("Fallo notificando: " + "; ".join(errors) + "\n")
            print("Aviso: falló algún canal de notificación:", "; ".join(errors))
        print(f"\nLog completo: {log_path}")
    return 0 if ok else 1


def main() -> int:
    if "--dry-run" in sys.argv:
        return mode_dry_run()
    if "--test-notify" in sys.argv:
        return mode_test_notify()
    return mode_run()


if __name__ == "__main__":
    sys.exit(main())
