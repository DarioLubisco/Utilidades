"""Additional investigation before fix."""
import sys
from datetime import date, timedelta
from pathlib import Path

import pyodbc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from util_config import get_connection_string

YESTERDAY = date.today() - timedelta(days=1)
TODAY = date.today()

conn = pyodbc.connect(get_connection_string())
cursor = conn.cursor()

# Invoices/sales with dates after yesterday
for tbl, date_col in [("SAFACT", "FechaE"), ("SACOMP", "FechaE"), ("SAITEMFAC", "FechaE")]:
    cursor.execute(f"""
        SELECT COUNT(*) FROM {tbl} WHERE CONVERT(DATE, {date_col}) > ?
    """, YESTERDAY)
    cnt = cursor.fetchone()[0]
    print(f"{tbl} rows with {date_col} > {YESTERDAY}: {cnt}")
    if cnt:
        cursor.execute(f"""
            SELECT TOP 5 NumeroD, {date_col} FROM {tbl}
            WHERE CONVERT(DATE, {date_col}) > ?
            ORDER BY {date_col} DESC
        """, YESTERDAY)
        for r in cursor.fetchall():
            print(f"  {r}")

# SAITEMCOM/SALOTE with dates > yesterday
for tbl in ["SAITEMCOM", "SALOTE"]:
    cursor.execute(f"SELECT COUNT(*) FROM {tbl} WHERE CONVERT(DATE, FechaE) > ?", YESTERDAY)
    cnt = cursor.fetchone()[0]
    print(f"\n{tbl} with FechaE > {YESTERDAY}: {cnt}")
    if cnt:
        cursor.execute(f"""
            SELECT TOP 5 * FROM {tbl} WHERE CONVERT(DATE, FechaE) > ?
            ORDER BY FechaE DESC
        """, YESTERDAY)
        cols = [d[0] for d in cursor.description]
        for r in cursor.fetchall():
            d = dict(zip(cols, r))
            keys = ['NumeroD','CodItem','NroLote','CodProd','FechaE'] if tbl=='SAITEMCOM' else ['CodProd','NroLote','FechaE']
            print(f"  {{{', '.join(f'{k}: {d.get(k)}' for k in keys if k in d)}}}")

# Check SACONV/SACORTEZ
for tbl in ["SACONV", "SACORTEZ"]:
    try:
        cursor.execute(f"SELECT TOP 3 * FROM {tbl} ORDER BY FechaUC DESC")
        cols = [d[0] for d in cursor.description]
        print(f"\n--- {tbl} latest ---")
        for r in cursor.fetchall():
            d = dict(zip(cols, r))
            print({k: d[k] for k in cols if 'Fecha' in k or 'Mes' in k})
    except Exception as e:
        print(f"{tbl}: {e}")

# Current SACONF key fields
cursor.execute("SELECT MesCurso, MesTran, FechaUC, FechaUP, FechaUV FROM SACONF")
r = cursor.fetchone()
print(f"\n=== SACONF BEFORE ===")
print(f"  MesCurso={r[0]}, MesTran={r[1]}, FechaUC={r[2]}, FechaUP={r[3]}, FechaUV={r[4]}")

conn.close()
