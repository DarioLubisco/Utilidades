import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
SELECT t.codigo, t.descripcion, t.precio_anterior, p.CostAct, p.Precio1
FROM [20260501] t
JOIN SAPROD p ON t.codigo = p.CodProd
WHERE p.Precio1 > 1000
""")
results = cursor.fetchall()
print(f"Products STILL with exorbitant prices: {len(results)}")
if len(results) > 0:
    for row in results[:5]:
        print(row)
