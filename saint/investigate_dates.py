"""Read-only investigation of incorrect dates on EnterpriseAdmin_AMC."""
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

print(f"=== Investigation {TODAY.isoformat()} (yesterday={YESTERDAY.isoformat()}) ===\n")

# 1. SACONF date-related columns
cursor.execute("SELECT TOP 1 * FROM SACONF")
cols = [d[0] for d in cursor.description]
row = cursor.fetchone()
print("--- SACONF (date-like columns) ---")
for c, v in zip(cols, row):
    if "fecha" in c.lower() or "date" in c.lower() or "act" in c.lower() or "proc" in c.lower():
        print(f"  {c}: {v}")

# 2. Future dates in SAITEMCOM vs SACOMP header
cursor.execute("""
    SELECT COUNT(*) FROM SAITEMCOM WHERE CONVERT(DATE, FechaE) > ?
""", TODAY)
print(f"\n--- SAITEMCOM with FechaE > today: {cursor.fetchone()[0]} ---")

cursor.execute("""
    SELECT TOP 10 SC.NumeroD, SC.FechaE AS HeaderDate, SI.FechaE AS ItemDate, SI.CodItem
    FROM SACOMP SC
    INNER JOIN SAITEMCOM SI ON SC.NumeroD = SI.NumeroD
    WHERE CONVERT(DATE, SI.FechaE) <> CONVERT(DATE, SC.FechaE)
      AND CONVERT(DATE, SI.FechaE) > ?
    ORDER BY SI.FechaE DESC
""", TODAY)
rows = cursor.fetchall()
print(f"SAITEMCOM mismatched future dates (sample {len(rows)}):")
for r in rows:
    print(f"  {r}")

# 3. Future dates in SALOTE
cursor.execute("SELECT COUNT(*) FROM SALOTE WHERE CONVERT(DATE, FechaE) > ?", TODAY)
print(f"\n--- SALOTE with FechaE > today: {cursor.fetchone()[0]} ---")

cursor.execute("""
    SELECT TOP 10 CodProd, NroLote, FechaE FROM SALOTE
    WHERE CONVERT(DATE, FechaE) > ?
    ORDER BY FechaE DESC
""", TODAY)
for r in cursor.fetchall():
    print(f"  {r}")

# 4. SAITEMCOM with future dates (all, not just mismatched)
cursor.execute("""
    SELECT COUNT(*) FROM SAITEMCOM WHERE CONVERT(DATE, FechaE) > ?
""", TODAY)
cnt = cursor.fetchone()[0]
print(f"\n--- Total SAITEMCOM future FechaE: {cnt} ---")

# 5. Check SAEMPRE / company config for activity dates
for tbl in ["SAEMPRE", "SAUSUARIO", "SASUCURSAL"]:
    try:
        cursor.execute(f"SELECT TOP 1 * FROM {tbl}")
        tcols = [d[0] for d in cursor.description]
        trow = cursor.fetchone()
        date_cols = [c for c in tcols if "fecha" in c.lower() or "act" in c.lower()]
        if date_cols:
            print(f"\n--- {tbl} date columns ---")
            for c in date_cols:
                idx = tcols.index(c)
                print(f"  {c}: {trow[idx]}")
    except Exception as e:
        print(f"\n--- {tbl}: {e} ---")

# 6. Search for tables with FechaAct or similar
cursor.execute("""
    SELECT t.name AS TableName, c.name AS ColumnName
    FROM sys.columns c
    JOIN sys.tables t ON c.object_id = t.object_id
    WHERE c.name LIKE '%FechaAct%' OR c.name LIKE '%FechaCierre%'
       OR c.name LIKE '%FechaProceso%' OR c.name LIKE '%FechaUlt%'
    ORDER BY t.name, c.name
""")
print("\n--- Sys columns matching activity/close date patterns ---")
for r in cursor.fetchall():
    print(f"  {r[0]}.{r[1]}")

# 7. Server date
cursor.execute("SELECT GETDATE() AS ServerNow, CAST(GETDATE() AS DATE) AS ServerToday")
r = cursor.fetchone()
print(f"\n--- SQL Server clock: {r[0]} (date={r[1]}) ---")

conn.close()
