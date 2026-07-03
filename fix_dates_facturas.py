"""
Corrige fechas de SAITEMCOM/SALOTE para facturas de compra específicas.
Uso: python fix_dates_facturas.py 00106048 00352877
"""
import sys

from util_config import connect


def main():
    numeros = sys.argv[1:] if len(sys.argv) > 1 else ["00106048", "00352877"]
    placeholders = ",".join("?" * len(numeros))

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        UPDATE SAITEMCOM
        SET FechaE = (SELECT FechaE FROM SACOMP WHERE NumeroD = SAITEMCOM.NumeroD)
        WHERE NumeroD IN ({placeholders})
    """,
        numeros,
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
        WHERE NroLote IN (
            SELECT NroLote FROM SAITEMCOM WHERE NumeroD IN ({placeholders})
        ) AND CodProd IN (
            SELECT CodItem FROM SAITEMCOM WHERE NumeroD IN ({placeholders})
        )
    """,
        numeros + numeros + numeros,
    )

    conn.commit()
    cursor.execute("EXEC UpdatePrices")
    conn.commit()
    conn.close()
    print(f"Fechas corregidas y precios actualizados para: {', '.join(numeros)}")


if __name__ == "__main__":
    main()
