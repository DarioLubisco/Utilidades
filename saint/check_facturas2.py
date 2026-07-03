import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

print("--- SAFACT ---")
df_fact = pd.read_sql("SELECT NumeroD, TipoFac, Factor, MtoTotal, FechaE FROM SAFACT WHERE NumeroD LIKE '%106048%' OR NumeroD LIKE '%352877%'", conn)
print(df_fact.to_string())

print("\n--- SACOMP ---")
df_comp = pd.read_sql("SELECT NumeroD, TipoCom, Factor, MtoTotal, FechaE FROM SACOMP WHERE NumeroD LIKE '%106048%' OR NumeroD LIKE '%352877%'", conn)
print(df_comp.to_string())
