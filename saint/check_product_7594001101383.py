import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

print("--- SAITEMCOM (Compras) ---")
df_com = pd.read_sql("SELECT TOP 5 NumeroD, FechaE, CodItem, Cantidad, Costo, NroLote FROM SAITEMCOM WHERE CodItem = '7594001101383' ORDER BY FechaE DESC", conn)
print(df_com.to_string())

print("\n--- SALOTE ---")
df_lote = pd.read_sql("SELECT CodProd, NroLote, Costo, FechaE FROM SALOTE WHERE CodProd = '7594001101383' ORDER BY FechaE DESC", conn)
print(df_lote.to_string())

print("\n--- SAITEMFAC (Ventas) ---")
df_fac = pd.read_sql("SELECT TOP 5 NumeroD, FechaE, CodItem, Cantidad, Precio, Costo FROM SAITEMFAC WHERE CodItem = '7594001101383' ORDER BY FechaE DESC", conn)
print(df_fac.to_string())

