import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT CodProd, Utilidad1, Utilidad2, Utilidad3 FROM SAPROD WHERE CodProd IN ('8908000942301', '7598252000266')")
for row in cursor.fetchall():
    print(row)
