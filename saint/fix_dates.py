import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
    UPDATE SAITEMCOM
    SET FechaE = (SELECT FechaE FROM SACOMP WHERE NumeroD = SAITEMCOM.NumeroD)
    WHERE NumeroD IN ('00106048', '00352877')
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
    WHERE NroLote IN (
        SELECT NroLote FROM SAITEMCOM WHERE NumeroD IN ('00106048', '00352877')
    ) AND CodProd IN (
        SELECT CodItem FROM SAITEMCOM WHERE NumeroD IN ('00106048', '00352877')
    )
""")

conn.commit()

# Execute the UpdatePrices procedure to recalculate based on the correct exchange rate
cursor.execute("EXEC UpdatePrices")
conn.commit()

print("Dates corrected and prices updated.")
