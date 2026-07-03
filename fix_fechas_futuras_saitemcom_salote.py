"""
Corrige fechas futuras en SAITEMCOM y SALOTE, luego ejecuta UpdatePrices.

Evita precios astronómicos cuando CUSTOM_LOTES busca tasa DolarToday en fecha futura.
"""
from datetime import date

from util_config import connect

# Umbral: cualquier fecha posterior a hoy
CUTOFF = date.today().isoformat()


def main():
    conn = connect()
    cursor = conn.cursor()

    print("Escaneando ítems y lotes con fechas futuras en facturas de compra...")

    cursor.execute(
        f"""
        SELECT SC.NumeroD, SC.FechaE as HeaderDate, SI.FechaE as ItemDate, SI.CodItem
        FROM SACOMP SC
        INNER JOIN SAITEMCOM SI ON SC.NumeroD = SI.NumeroD
        WHERE CONVERT(DATE, SC.FechaE) <> CONVERT(DATE, SI.FechaE)
        AND SI.FechaE > '{CUTOFF}'
    """
    )
    rows = cursor.fetchall()

    if not rows:
        print("No se encontraron ítems o lotes con fecha en el futuro.")
        conn.close()
        return

    print(f"Se detectaron {len(rows)} líneas. Procediendo a corregir...")
    for r in rows:
        print(
            f"Factura: {r[0]} | Cabecera: {r[1]} | Item errado: {r[2]} | Producto: {r[3]}"
        )

    cursor.execute(
        f"""
        UPDATE SAITEMCOM
        SET FechaE = (SELECT FechaE FROM SACOMP WHERE NumeroD = SAITEMCOM.NumeroD)
        WHERE FechaE > '{CUTOFF}'
    """
    )

    cursor.execute(
        f"""
        UPDATE SALOTE
        SET FechaE = (
            SELECT TOP 1 SC.FechaE
            FROM SAITEMCOM SI
            INNER JOIN SACOMP SC ON SI.NumeroD = SC.NumeroD
            WHERE SI.CodItem = SALOTE.CodProd AND SI.NroLote = SALOTE.NroLote
            ORDER BY SC.FechaE DESC
        )
        WHERE FechaE > '{CUTOFF}'
    """
    )

    conn.commit()
    print("Fechas corregidas en SAITEMCOM y SALOTE.")

    print("Ejecutando EXEC UpdatePrices...")
    cursor.execute("EXEC UpdatePrices")
    conn.commit()
    print("UpdatePrices completado.")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
