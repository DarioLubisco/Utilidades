import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT TOP 5 NumeroD, TipoCom, FechaE, MtoTotal, Factor, MontoMEx FROM SACOMP WHERE FechaE < '2026-04-01' ORDER BY FechaE DESC", conn)
print("--- Old SACOMP Invoices (Before April) ---")
print(df.to_string())

df_fact = pd.read_sql("SELECT TOP 5 NumeroD, FechaE, MtoTotal, Factor, MontoMEx FROM SAFACT WHERE FechaE < '2026-04-01' ORDER BY FechaE DESC", conn)
print("\n--- Old SAFACT Invoices (Before April) ---")
print(df_fact.to_string())
