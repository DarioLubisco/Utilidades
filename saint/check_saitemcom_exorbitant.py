import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT TOP 10 NumeroD, CodItem, Cantidad, Costo, TotalItem FROM SAITEMCOM WHERE Costo > 100 ORDER BY FechaE DESC", conn)
print("--- SAITEMCOM with exorbitant Costo ---")
print(df.to_string())
