import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT TOP 5 * FROM [20260501] WHERE codigo = '8908000942301'", conn)
print("--- [20260501] (Old values) ---")
print(df.to_string())
