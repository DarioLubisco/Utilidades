import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT NumeroD, TipoCom, FechaE, MtoTotal, Factor, MontoMEx FROM SACOMP WHERE FechaE >= '2026-05-01' AND MtoTotal > 1000 AND (MtoTotal / NULLIF(MontoMEx, 0)) > 100", conn)
print("--- Bad SACOMP Invoices ---")
print(df.to_string())
