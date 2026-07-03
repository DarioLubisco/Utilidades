import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv

load_dotenv("c:\\source\\Synapse\\.env")

DB_SERVER = os.getenv("DB_SERVER", "10.200.8.5\\efficacis3")
DB_DATABASE = os.getenv("DB_DATABASE", "EnterpriseAdmin_AMC")
DB_USERNAME = os.getenv("DB_USERNAME", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Twinc3pt.")

def get_db_connection():
    available = pyodbc.drivers()
    driver_name = "ODBC Driver 17 for SQL Server"
    if "ODBC Driver 18 for SQL Server" in available:
        driver_name = "ODBC Driver 18 for SQL Server"
    
    conn_str = (
        f"DRIVER={{{driver_name}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def main():
    conn = get_db_connection()
    query = "SELECT codigo, descripcion, costo_anterior, precio_anterior, costo_actual, precio_actual FROM [20260501] ORDER BY precio_anterior DESC"
    df = pd.read_sql(query, conn)
    
    # Format large floats to avoid scientific notation
    # Actually, pandas handles it well in Excel export
    output_path = "c:\\source\\Reporte_Precios_Corregidos_20260501.xlsx"
    df.to_excel(output_path, index=False)
    print(f"Excel file created successfully at: {output_path}")
    conn.close()

if __name__ == "__main__":
    main()
