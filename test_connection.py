"""Prueba conexión SQL desde cualquier host."""
from util_config import connect, get_connection_string

if __name__ == "__main__":
    print("Connection string:", get_connection_string())
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT MesCurso, FechaUC, FechaUP FROM SACONF")
    row = cur.fetchone()
    print("SACONF:", row)
    conn.close()
    print("OK")
