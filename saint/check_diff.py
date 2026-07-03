import pyodbc
import pandas as pd

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)

df = pd.read_sql("SELECT TOP 5 codigo, descripcion, precio_anterior, precio_actual FROM [20260501] WHERE codigo NOT IN ('8908000942301', '7598252000266')", conn)
print("--- [20260501] ---")
print(df.to_string())

df_prod = pd.read_sql("SELECT CodProd, Descrip, CostAct, Precio1 FROM SAPROD WHERE CodProd IN (SELECT TOP 5 codigo FROM [20260501] WHERE codigo NOT IN ('8908000942301', '7598252000266'))", conn)
print("\n--- SAPROD ---")
print(df_prod.to_string())
