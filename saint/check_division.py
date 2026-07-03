import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

try:
    cursor.execute("SELECT CodProd FROM SAPROD WHERE CodProd='8908000942301' AND (Precio1 / CostAct) > 50")
    print(cursor.fetchall())
except Exception as e:
    print("Error:", e)
