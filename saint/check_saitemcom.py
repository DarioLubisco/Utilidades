import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT CodItem, Descrip1, Cantidad, Costo, TotalItem FROM SAITEMCOM WHERE NumeroD = '00106048'", conn)
print("--- SAITEMCOM for 00106048 ---")
print(df.to_string())
