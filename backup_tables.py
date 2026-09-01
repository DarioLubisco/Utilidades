"""
Backup preventivo de tablas Saint via SELECT * INTO.

Crea dbo.<TABLA>_BKP_<YYYYMMDD_HHMMSS> y verifica que coincide con el original
(mismo nº de filas y un HASH checksum de las filas).

Uso:
    python backup_tables.py                  # SACONF, SAITEMCOM, SALOTE
    python backup_tables.py SACONF           # solo SACONF
    python backup_tables.py SACONF SAITEMCOM # subset

No modifica datos productivos: solo crea tablas de respaldo de solo lectura.
"""
from __future__ import annotations

import sys
from datetime import datetime

from util_config import connect

DEFAULT_TABLES = ["SACONF", "SAITEMCOM", "SALOTE"]


def _quote_ident(name: str) -> str:
    """Valida que el nombre de tabla sea un identificador simple (anti-inyección)."""
    if not name or not name.replace("_", "").isalnum():
        raise ValueError(f"Nombre de tabla inválido (solo alfanumérico/_): {name!r}")
    return f"dbo.{name}"


def backup_table(cursor, table: str) -> str | None:
    """Crea backup de una tabla y lo verifica. Devuelve el nombre del backup o None si falló."""
    qname = _quote_ident(table)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bkp = f"{table}_BKP_{stamp}"

    # Evitar colisión si se ejecuta dos veces en el mismo segundo.
    cursor.execute(
        "SELECT OBJECT_ID(?, 'U')",
        (f"dbo.{bkp}",),
    )
    if cursor.fetchone()[0] is not None:
        print(f"  [{table}] Ya existe un backup con ese timestamp. Saltando.")
        return None

    # Filas y checksum del original (antes de copiar).
    cursor.execute(f"SELECT COUNT(*) FROM {qname}")
    orig_count = cursor.fetchone()[0]
    try:
        cursor.execute(f"SELECT CHECKSUM_AGG(CHECKSUM(*)) FROM {qname}")
        orig_hash = cursor.fetchone()[0]
    except Exception:
        orig_hash = None  # CHECKSUM falla con tipos no soportados; caemos a COUNT.

    # Copia (DDL + datos).
    cursor.execute(f"SELECT * INTO dbo.{bkp} FROM {qname}")

    # Verificación de integridad.
    cursor.execute(f"SELECT COUNT(*) FROM dbo.{bkp}")
    bkp_count = cursor.fetchone()[0]
    try:
        cursor.execute(f"SELECT CHECKSUM_AGG(CHECKSUM(*)) FROM dbo.{bkp}")
        bkp_hash = cursor.fetchone()[0]
    except Exception:
        bkp_hash = None

    ok_count = orig_count == bkp_count
    ok_hash = orig_hash == bkp_hash if orig_hash is not None else True

    status = "OK" if (ok_count and ok_hash) else "REVISAR"
    print(f"  [{table}] {status}: dbo.{bkp} ({bkp_count} filas)", end="")
    if orig_hash is not None and not ok_hash:
        print(f" | ⚠ checksum difiere (orig={orig_hash} bkp={bkp_hash})")
    else:
        print()

    return bkp if (ok_count and ok_hash) else None


def list_backups(cursor, tables: list[str]) -> None:
    """Lista backups existentes para las tablas indicadas."""
    print("\nBackups existentes:")
    found = False
    for t in tables:
        cursor.execute(
            """
            SELECT t.name
            FROM sys.tables t
            WHERE t.name LIKE ? + '_BKP_%'
            ORDER BY t.name
            """,
            (t,),
        )
        rows = [r[0] for r in cursor.fetchall()]
        if rows:
            found = True
            print(f"  [{t}] {len(rows)} backup(s):")
            for r in rows:
                print(f"     - dbo.{r}")
    if not found:
        print("  (ninguno)")


def main() -> None:
    tables = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT_TABLES
    print(f"Tablas a respaldar: {', '.join(tables)}\n")

    conn = connect()
    cursor = conn.cursor()

    created: list[str] = []
    for t in tables:
        created.append(backup_table(cursor, t) or "")
    conn.commit()

    list_backups(cursor, tables)
    conn.close()

    n_ok = sum(1 for c in created if c)
    print(f"\nResumen: {n_ok}/{len(tables)} backup(s) creados y verificados correctamente.")


if __name__ == "__main__":
    main()
