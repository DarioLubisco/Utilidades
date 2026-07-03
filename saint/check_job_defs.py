import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=msdb;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
SELECT j.name, s.step_id, s.step_name, s.command
FROM sysjobsteps s
JOIN sysjobs j ON s.job_id = j.job_id
WHERE j.name IN ('UpdatePrices', 'inv_Dlr', 'Consulta_costo_prod')
""")
for row in cursor.fetchall():
    print(f"--- Job: {row[0]}, Step: {row[2]} ---")
    print(row[3][:1000] if row[3] else None)
