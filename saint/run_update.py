import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

try:
    cursor.execute("SELECT COUNT(*) FROM SAPROD p WHERE p.CostAct > 0 AND (p.Precio1 / p.CostAct) > 50")
    print("Match count:", cursor.fetchone()[0])
    
    # Try the update!
    cursor.execute("""
    UPDATE p
    SET 
        p.Precio1 = p.CostAct * 1.30,
        p.Precio2 = p.CostAct * 1.25,
        p.Precio3 = p.CostAct * 1.20
    FROM SAPROD p
    WHERE p.CostAct > 0 AND (p.Precio1 / p.CostAct) > 50;
    """)
    print("Rows updated:", cursor.rowcount)
    conn.commit()
except Exception as e:
    print("Error:", e)
