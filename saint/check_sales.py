import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT TOP 10 NumeroD, FechaE, CodItem, Precio, TotalItem FROM SAITEMFAC WHERE CodItem='8908000942301' ORDER BY FechaE DESC", conn)
print("--- Recent Sales for Salbuquit ---")
print(df.to_string())

df_all = pd.read_sql("SELECT TOP 10 NumeroD, FechaE, CodItem, Precio, TotalItem FROM SAITEMFAC WHERE Precio > 1000 ORDER BY FechaE DESC", conn)
print("\n--- Recent Sales with Exorbitant Prices ---")
print(df_all.to_string())
