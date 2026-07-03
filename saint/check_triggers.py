import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT name, OBJECT_DEFINITION(object_id) FROM sys.triggers WHERE parent_id = OBJECT_ID('SAPROD')")
for row in cursor.fetchall():
    print(f"--- Trigger: {row[0]} ---")
    print(row[1][:1000]) # Print first 1000 chars
