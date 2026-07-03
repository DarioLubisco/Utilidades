import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT TOP 10 fecha, dolarbcv FROM dolartoday ORDER BY fecha DESC", conn)
print("--- dolartoday ---")
print(df.to_string())
