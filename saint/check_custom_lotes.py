import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT TOP 2 codprod, precio1, CostPror FROM Custom_Lotes WHERE codprod = '8908000942301'")
print("--- Custom_Lotes ---")
for row in cursor.fetchall():
    print(row)
