import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

print("--- SAFACT ---")
df_fact = pd.read_sql("SELECT NumeroD, TipoFac, Factor, MtoTotal, FechaE FROM SAFACT WHERE NumeroD IN ('00106048', '00352877', '106048', '352877')", conn)
print(df_fact.to_string())

print("\n--- SAITEMFAC ---")
df_item = pd.read_sql("SELECT NumeroD, TipoFac, CodItem, Cantidad, Factor, Costo, Precio, TotalItem FROM SAITEMFAC WHERE NumeroD IN ('00106048', '00352877', '106048', '352877')", conn)
print(df_item.to_string())
