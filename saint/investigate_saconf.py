"""Deep SACONF and month-close investigation."""
import sys
from datetime import date, timedelta
from pathlib import Path

import pyodbc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from util_config import get_connection_string

YESTERDAY = date.today() - timedelta(days=1)

conn = pyodbc.connect(get_connection_string())
cursor = conn.cursor()

print("=== Full SACONF row ===")
cursor.execute("SELECT TOP 1 * FROM SACONF")
cols = [d[0] for d in cursor.description]
row = cursor.fetchone()
for c, v in zip(cols, row):
    print(f"  {c}: {v}")

cursor.execute("""
    SELECT t.name, c.name
    FROM sys.columns c
    JOIN sys.tables t ON c.object_id = t.object_id
    WHERE t.name LIKE 'SA%' AND c.name LIKE 'Fecha%'
    ORDER BY t.name, c.name
""")
print("\n=== SA* tables with Fecha* columns ===")
prev = None
for tbl, col in cursor.fetchall():
    if tbl != prev:
        print(f"\n  {tbl}:")
        prev = tbl
    print(f"    {col}")

for tbl in ["SAFACT", "SAITEMFAC", "SACOMP", "SAITEMCOM", "SAEXIS"]:
    try:
        cursor.execute(f"""
            SELECT COUNT(*) FROM {tbl}
            WHERE CONVERT(DATE, FechaE) > ?
        """, YESTERDAY)
        cnt = cursor.fetchone()[0]
        if cnt:
            cursor.execute(f"""
                SELECT TOP 3 * FROM {tbl}
                WHERE CONVERT(DATE, FechaE) > ?
                ORDER BY FechaE DESC
            """, YESTERDAY)
            print(f"\n=== {tbl}: {cnt} rows with FechaE > yesterday ===")
            tcols = [d[0] for d in cursor.description]
            for r in cursor.fetchall():
                print(dict(zip(tcols, r)))
    except Exception as e:
        print(f"{tbl}: {e}")

print(f"\n=== Target yesterday: {YESTERDAY} ===")
print(f"FechaUC current: {row[cols.index('FechaUC')]}")
print(f"FechaUP current: {row[cols.index('FechaUP')]}")

cursor.execute("""
    SELECT COUNT(*), MIN(FechaE), MAX(FechaE)
    FROM SAITEMCOM
    WHERE FechaE >= '2026-06-01'
""")
print(f"\nSAITEMCOM June+ stats: {cursor.fetchone()}")

cursor.execute("""
    SELECT COUNT(*), MIN(FechaE), MAX(FechaE)
    FROM SALOTE
    WHERE FechaE >= '2026-06-01'
""")
print(f"SALOTE June+ stats: {cursor.fetchone()}")

cursor.execute("""
    SELECT TOP 5 fecha, dolarbcv, Dolartoday, fuente
    FROM dolartoday ORDER BY fecha DESC
""")
print("\n=== dolartoday latest ===")
for r in cursor.fetchall():
    print(f"  {r}")

conn.close()
