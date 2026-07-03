import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Find all invoices where the header date is different from the item date by more than a day (or item date is in the future)
cursor.execute("""
    SELECT SC.NumeroD, SC.FechaE as HeaderDate, SI.FechaE as ItemDate, SI.CodItem 
    FROM SACOMP SC
    INNER JOIN SAITEMCOM SI ON SC.NumeroD = SI.NumeroD
    WHERE CONVERT(DATE, SC.FechaE) <> CONVERT(DATE, SI.FechaE)
    AND SI.FechaE > '2026-05-05'
""")

rows = cursor.fetchall()
print("Invoices with future item dates:")
for r in rows:
    print(r)

if len(rows) > 0:
    cursor.execute("""
        UPDATE SAITEMCOM
        SET FechaE = (SELECT FechaE FROM SACOMP WHERE NumeroD = SAITEMCOM.NumeroD)
        WHERE FechaE > '2026-05-05'
    """)

    cursor.execute("""
        UPDATE SALOTE
        SET FechaE = (
            SELECT TOP 1 SC.FechaE 
            FROM SAITEMCOM SI
            INNER JOIN SACOMP SC ON SI.NumeroD = SC.NumeroD
            WHERE SI.CodItem = SALOTE.CodProd AND SI.NroLote = SALOTE.NroLote
            ORDER BY SC.FechaE DESC
        )
        WHERE FechaE > '2026-05-05'
    """)

    conn.commit()
    cursor.execute("EXEC UpdatePrices")
    conn.commit()
    print("Fixed all future dates in SAITEMCOM and SALOTE, and updated prices.")

