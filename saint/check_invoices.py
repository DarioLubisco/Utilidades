import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT NumeroD, TipoFac, FechaE, MtoTotal FROM SAFACT WHERE NumeroD LIKE '%106048%' OR NumeroD LIKE '%352877%'", conn)
print("--- SAFACT ---")
print(df)

df_comp = pd.read_sql("SELECT NumeroD, TipoCom, FechaE, MtoTotal FROM SACOMP WHERE NumeroD LIKE '%106048%' OR NumeroD LIKE '%352877%'", conn)
print("\n--- SACOMP ---")
print(df_comp)
