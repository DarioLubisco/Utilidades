import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
SELECT t.codigo, p.CostAct, p.Precio1, t.precio_actual
FROM [20260501] t
JOIN SAPROD p ON t.codigo = p.CodProd
""")
results = cursor.fetchall()

mismatches = 0
for row in results:
    if abs(row.Precio1 - row.precio_actual) > 0.1:
        mismatches += 1

print(f"Total products in Excel: {len(results)}")
print(f"Products where SAPROD Precio1 DOES NOT match Excel: {mismatches}")
