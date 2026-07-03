import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.200.8.5\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("Iniciando escaneo de ítems y lotes con fechas futuras (posteriores a hoy) en facturas cargadas...")

# Encontrar y mostrar todas las facturas donde la fecha del encabezado es diferente a la fecha del item 
# y la fecha del ítem está erróneamente seteada en el futuro (después de 2026-05-05)
cursor.execute("""
    SELECT SC.NumeroD, SC.FechaE as HeaderDate, SI.FechaE as ItemDate, SI.CodItem 
    FROM SACOMP SC
    INNER JOIN SAITEMCOM SI ON SC.NumeroD = SI.NumeroD
    WHERE CONVERT(DATE, SC.FechaE) <> CONVERT(DATE, SI.FechaE)
    AND SI.FechaE > '2026-05-05'
""")

rows = cursor.fetchall()

if len(rows) > 0:
    print(f"Se detectaron {len(rows)} líneas de artículos con fecha en el futuro. Procediendo a corregir...")
    for r in rows:
        print(f"Factura: {r[0]} | Fecha Correcta (Cabecera): {r[1]} | Fecha Errada (Item): {r[2]} | Producto: {r[3]}")

    # Corrección 1: Actualizar la fecha de las líneas de la factura de compra (SAITEMCOM) 
    # para que herede la fecha del encabezado (SACOMP)
    cursor.execute("""
        UPDATE SAITEMCOM
        SET FechaE = (SELECT FechaE FROM SACOMP WHERE NumeroD = SAITEMCOM.NumeroD)
        WHERE FechaE > '2026-05-05'
    """)

    # Corrección 2: Actualizar la fecha de creación del Lote (SALOTE)
    # para que coincida con la fecha correcta recién asignada a la factura.
    # Esto previene que CUSTOM_LOTES busque una tasa de cambio de DolarToday en el futuro (que dará nula y causará precios astronómicos).
    cursor.execute("""
        UPDATE SALOTE
        SET FechaE = (
            SELECT TOP 1 SC.FechaE 
            FROM SAITEMCOM SI
            INNER JOIN SACOMP SC ON SI.NumeroD = SC.NumeroD
            WHERE SI.CodItem = SALOTE.CodProd AND SI.NroLote = SALOTE.NroLote
            ORDER BY SC.FechaE DESC
        )
        WHERE FechaE > '2026-05-05'
    """)

    conn.commit()
    print("Fechas corregidas exitosamente en la base de datos.")

    # Corrección 3: Reejecutar el stored procedure UpdatePrices para que recalcule 
    # el margen y convierta los costos utilizando el tipo de cambio correcto de DolarToday (ya no es nulo).
    print("Recalculando precios en SAPROD a través del Stored Procedure UpdatePrices...")
    cursor.execute("EXEC UpdatePrices")
    conn.commit()
    print("El recálculo de precios ha finalizado con éxito. Los precios astronómicos en SAPROD han sido normalizados.")

else:
    print("No se encontraron ítems o lotes con fecha en el futuro.")
