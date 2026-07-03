"""
Fix SACONF month-end activity dates on EnterpriseAdmin_AMC.

Context: Month won't close / billing blocked when FechaUP advances past
MesCurso while FechaUC (last activity close) lags behind.

Sets FechaUC and FechaUP to yesterday and advances MesCurso to current month.
"""
import sys
from datetime import date, timedelta, datetime
from pathlib import Path

import pyodbc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from util_config import get_connection_string

YESTERDAY = date.today() - timedelta(days=1)
YESTERDAY_DT = datetime.combine(YESTERDAY, datetime.min.time())
CURRENT_MONTH = int(YESTERDAY.strftime("%Y%m"))
NEXT_MONTH = CURRENT_MONTH + 1 if CURRENT_MONTH % 100 < 12 else CURRENT_MONTH + 89


def main():
    conn = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()

    cursor.execute("SELECT MesCurso, FechaUC, FechaUP FROM SACONF")
    before = cursor.fetchone()
    print("=== BEFORE ===")
    print(f"  MesCurso={before[0]}, FechaUC={before[1]}, FechaUP={before[2]}")

    needs_fix = (
        before[1] is None
        or before[1].date() < YESTERDAY
        or before[2].date() > YESTERDAY
        or before[0] < NEXT_MONTH
    )

    if not needs_fix:
        print("\nNo SACONF date fix needed.")
        conn.close()
        return

    # Advance MesCurso to July 2026 since yesterday closes June
    new_mes_curso = NEXT_MONTH

    cursor.execute("""
        UPDATE SACONF
        SET FechaUC = ?,
            FechaUP = ?,
            MesCurso = ?
    """, (YESTERDAY_DT, YESTERDAY_DT, new_mes_curso))
    rows = cursor.rowcount
    conn.commit()

    cursor.execute("SELECT MesCurso, FechaUC, FechaUP FROM SACONF")
    after = cursor.fetchone()
    print(f"\n=== UPDATE SACONF ({rows} row) ===")
    print(f"  SET FechaUC = '{YESTERDAY_DT}'")
    print(f"  SET FechaUP = '{YESTERDAY_DT}'")
    print(f"  SET MesCurso = {new_mes_curso}")

    print("\n=== AFTER ===")
    print(f"  MesCurso={after[0]}, FechaUC={after[1]}, FechaUP={after[2]}")

    # Verify no future dates remain in transaction tables
    for tbl in ["SAITEMCOM", "SALOTE"]:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl} WHERE CONVERT(DATE, FechaE) > ?", YESTERDAY)
        cnt = cursor.fetchone()[0]
        print(f"  {tbl} with FechaE > yesterday: {cnt}")

    # UpdatePrices only if future-dated lot items exist (exchange rate recalc)
    cursor.execute("SELECT COUNT(*) FROM SAITEMCOM WHERE CONVERT(DATE, FechaE) > ?", date.today())
    future_items = cursor.fetchone()[0]
    if future_items > 0:
        print("\nRunning EXEC UpdatePrices (future SAITEMCOM dates detected)...")
        cursor.execute("EXEC UpdatePrices")
        conn.commit()
        print("  UpdatePrices completed.")
    else:
        print("\nSkipping UpdatePrices (no future SAITEMCOM/SALOTE dates).")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
