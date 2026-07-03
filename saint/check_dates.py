import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT NumeroD, FechaE FROM SACOMP WHERE NumeroD IN ('00106048', '00352877')")
print(cursor.fetchall())

cursor.execute("SELECT NumeroD, CodItem, FechaE FROM SAITEMCOM WHERE NumeroD IN ('00106048', '00352877')")
print(cursor.fetchall())
