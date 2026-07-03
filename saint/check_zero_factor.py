import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT NumeroD, TipoCom, FechaE, Factor, MtoTotal FROM SACOMP WHERE Factor = 0 OR Factor IS NULL", conn)
print("--- SACOMP with Factor 0 ---")
print(df.to_string())

df2 = pd.read_sql("SELECT NumeroD, TipoFac, FechaE, Factor, MtoTotal FROM SAFACT WHERE Factor = 0 OR Factor IS NULL", conn)
print("\n--- SAFACT with Factor 0 ---")
print(df2.to_string())

# Also check if the user meant SAITEMFAC prices being skyrocketed
df3 = pd.read_sql("SELECT TOP 5 NumeroD, CodItem, Precio, Costo FROM SAITEMFAC WHERE NumeroD IN ('00106048', '00352877')", conn)
print("\n--- SAITEMFAC for 00106048 / 00352877 ---")
print(df3.to_string())
