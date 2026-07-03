import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT TOP 2 * FROM SAITEMCOM WHERE NumeroD = '00106048'")
cols = [desc[0] for desc in cursor.description]
print("--- SAITEMCOM ---")
for row in cursor.fetchall():
    print(dict(zip(cols, row)))
