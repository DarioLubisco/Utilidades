import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("""
SELECT c.NumeroD, i.CodItem, i.Descrip1, i.Costo, p.CostAct, p.Precio1
FROM SACOMP c
JOIN SAITEMCOM i ON c.NumeroD = i.NumeroD
JOIN SAPROD p ON i.CodItem = p.CodProd
WHERE c.NumeroD IN ('00106048', '00352877')
""", conn)
print(df.to_string())
