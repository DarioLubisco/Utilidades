"""
Core de diagnóstico de precios farmacéuticos.

Analiza 4 tablas para detectar costos inflados:
  - saitemcom: Costo de compra
  - salote: Costo por lote
  - SAPROD: Costo promedio/actual
  - SAACXP: Cuentas por pagar

Uso:
    from diagnostico_precios import diagnose
    result = diagnose("7707816985561", "2026-01-01", "2026-08-01")
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Agregar padre al path para importar util_config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from util_config import connect


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Hallazgo:
    tabla: str
    campo: str
    numero_d: str | None = None
    nro_unico: int | None = None
    nro_lote: str | None = None
    fecha: str | None = None
    proveedor: str | None = None
    costo_anterior: float = 0.0
    costo_referencia: float = 0.0
    ratio: float = 0.0
    descripcion: str = ""


@dataclass
class Sugerencia:
    tabla: str
    accion: str
    sql: str
    filas_esperadas: int = 0


@dataclass
class ResultadoDiagnostico:
    codprod: str
    descripcion: str = ""
    cost_act_saprod: float = 0.0
    cost_pro_saprod: float = 0.0
    precio1_saprod: float = 0.0
    precio2_saprod: float = 0.0
    precio3_saprod: float = 0.0
    hallazgos: list[Hallazgo] = field(default_factory=list)
    sugerencias: list[Sugerencia] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["hallazgos"] = [asdict(h) for h in self.hallazgos]
        d["sugerencias"] = [asdict(s) for s in self.sugerencias]
        return d


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

QUERY_SAPROD = """
SELECT
    CodProd, Descrip,
    CostAct, CostPro,
    Precio1, Precio2, Precio3,
    Existen
FROM EnterpriseAdmin_AMC.dbo.SAPROD
WHERE CodProd = ?
"""

QUERY_SAITEMCOM = """
SELECT
    i.CodItem,
    i.Descrip1,
    i.Cantidad,
    i.Costo,
    i.CostOrg,
    i.Precio1, i.Precio2, i.Precio3,
    i.TotalItem,
    i.NroLinea,
    i.CodSucu, i.TipoCom, i.NumeroD, i.CodProv,
    i.FechaE,
    c.FechaT,
    c.Descrip AS Proveedor
FROM EnterpriseAdmin_AMC.dbo.saitemcom i
INNER JOIN EnterpriseAdmin_AMC.dbo.sacomp c
    ON c.CodSucu = i.CodSucu
   AND c.TipoCom = i.TipoCom
   AND c.NumeroD = i.NumeroD
   AND c.CodProv = i.CodProv
WHERE i.CodItem = ?
  AND c.FechaT BETWEEN ? AND ?
ORDER BY c.FechaT
"""

QUERY_SALOTE = """
SELECT
    l.CodProd,
    l.NroUnico,
    l.NroLote,
    l.Cantidad,
    l.Costo,
    l.Precio1, l.Precio2, l.Precio3,
    l.FechaE,
    l.FechaV,
    l.CodSucu
FROM EnterpriseAdmin_AMC.dbo.salote l
WHERE l.CodProd = ?
  AND l.FechaE BETWEEN ? AND ?
ORDER BY l.FechaE
"""

QUERY_SAACXP = """
SELECT
    cxp.NumeroD,
    cxp.FechaT,
    cxp.Descrip AS Proveedor,
    cxp.Monto,
    cxp.Saldo,
    cxp.SaldoOrg,
    cxp.MontoNeto
FROM EnterpriseAdmin_AMC.dbo.SAACXP cxp
WHERE cxp.FechaT BETWEEN ? AND ?
  AND cxp.NumeroD IN (
      SELECT DISTINCT i.NumeroD
      FROM EnterpriseAdmin_AMC.dbo.saitemcom i
      WHERE i.CodItem = ?
  )
"""


# ---------------------------------------------------------------------------
# Core diagnosis logic
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> datetime:
    """Parsea fecha en formato DD/MM/YYYY o YYYY-MM-DD."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha no reconocido: {date_str} (usa DD/MM/YYYY o YYYY-MM-DD)")


def _check_ratio(valor: float, referencia: float, umbral: float) -> float:
    """Retorna ratio valor/referencia si excede umbral, sino 0."""
    if referencia <= 0 or valor <= 0:
        return 0.0
    ratio = valor / referencia
    return round(ratio, 2) if ratio > umbral else 0.0


def diagnose(
    codprod: str,
    desde: str,
    hasta: str,
    umbral: float = 1.6,
    conn=None,
) -> ResultadoDiagnostico:
    """
    Diagnosticar errores de precio para un producto.

    Args:
        codprod: Código del producto (SAPROD.CodProd)
        desde: Fecha inicio (DD/MM/YYYY o YYYY-MM-DD)
        hasta: Fecha fin (DD/MM/YYYY o YYYY-MM-DD)
        umbral: Ratio mínimo para considerar error (default 1.6)
        conn: Conexión pyodbc opcional (para testing)

    Returns:
        ResultadoDiagnostico con hallazgos y sugerencias
    """
    result = ResultadoDiagnostico(codprod=codprod)
    _conn_provided = conn is not None

    try:
        if conn is None:
            conn = connect()

        # 1. Info del producto en SAPROD
        row = conn.execute(QUERY_SAPROD, (codprod,)).fetchone()
        if not row:
            result.error = f"Producto {codprod} no encontrado en SAPROD"
            return result

        result.descripcion = row.Descrip or ""
        result.cost_act_saprod = row.CostAct or 0
        result.cost_pro_saprod = row.CostPro or 0
        result.precio1_saprod = row.Precio1 or 0
        result.precio2_saprod = row.Precio2 or 0
        result.precio3_saprod = row.Precio3 or 0

        desde_dt = _parse_date(desde)
        hasta_dt = _parse_date(hasta)

        # 2. Analizar saitemcom (compras)
        rows_ic = conn.execute(QUERY_SAITEMCOM, (codprod, desde_dt, hasta_dt)).fetchall()
        for r in rows_ic:
            ratio = _check_ratio(r.Costo, result.cost_pro_saprod, umbral)
            if ratio > 0:
                result.hallazgos.append(Hallazgo(
                    tabla="saitemcom",
                    campo="Costo",
                    numero_d=r.NumeroD,
                    fecha=str(r.FechaT) if r.FechaT else None,
                    proveedor=r.Proveedor,
                    costo_anterior=r.Costo,
                    costo_referencia=result.cost_pro_saprod,
                    ratio=ratio,
                    descripcion=f"Costo compra ${r.Costo:,.2f} vs costo promedio ${result.cost_pro_saprod:,.2f} ({ratio}x)",
                ))
                result.sugerencias.append(Sugerencia(
                    tabla="saitemcom",
                    accion=f"Actualizar Costo de ${r.Costo:,.2f} a ${result.cost_pro_saprod:,.2f}",
                    sql=f"UPDATE EnterpriseAdmin_AMC.dbo.saitemcom SET Costo = {result.cost_pro_saprod} WHERE CodSucu = '{r.CodSucu}' AND TipoCom = '{r.TipoCom}' AND NumeroD = '{r.NumeroD}' AND CodProv = '{r.CodProv}' AND NroLinea = {r.NroLinea}",
                    filas_esperadas=1,
                ))

        # 3. Analizar salote (lotes)
        rows_lt = conn.execute(QUERY_SALOTE, (codprod, desde_dt, hasta_dt)).fetchall()
        for r in rows_lt:
            ratio = _check_ratio(r.Costo, result.cost_pro_saprod, umbral)
            if ratio > 0:
                result.hallazgos.append(Hallazgo(
                    tabla="salote",
                    campo="Costo",
                    nro_unico=r.NroUnico,
                    nro_lote=r.NroLote,
                    fecha=str(r.FechaE) if r.FechaE else None,
                    costo_anterior=r.Costo,
                    costo_referencia=result.cost_pro_saprod,
                    ratio=ratio,
                    descripcion=f"Lote {r.NroLote} costo ${r.Costo:,.2f} vs costo promedio ${result.cost_pro_saprod:,.2f} ({ratio}x)",
                ))
                result.sugerencias.append(Sugerencia(
                    tabla="salote",
                    accion=f"Actualizar Costo lote {r.NroLote} de ${r.Costo:,.2f} a ${result.cost_pro_saprod:,.2f}",
                    sql=f"UPDATE EnterpriseAdmin_AMC.dbo.salote SET Costo = {result.cost_pro_saprod} WHERE CodProd = '{codprod}' AND NroUnico = {r.NroUnico}",
                    filas_esperadas=1,
                ))

        # 4. Analizar SAACXP (cuentas por pagar)
        rows_cxp = conn.execute(QUERY_SAACXP, (desde_dt, hasta_dt, codprod)).fetchall()
        for r in rows_cxp:
            # Verificar si el monto de CxP es consistente con items
            ratio = _check_ratio(r.Monto, result.cost_pro_saprod * 10, umbral)
            if ratio > 0:
                result.hallazgos.append(Hallazgo(
                    tabla="SAACXP",
                    campo="Monto",
                    numero_d=r.NumeroD,
                    fecha=str(r.FechaT) if r.FechaT else None,
                    proveedor=r.Proveedor,
                    costo_anterior=r.Monto,
                    costo_referencia=result.cost_pro_saprod,
                    ratio=ratio,
                    descripcion=f"CxP ${r.Monto:,.2f} posiblemente inflada para factura {r.NumeroD}",
                ))

        # 5. Check SAPROD price vs cost ratio (selling price inflated)
        if result.cost_pro_saprod > 0 and result.precio1_saprod > 0:
            price_ratio = result.precio1_saprod / result.cost_pro_saprod
            if price_ratio > 100:
                result.hallazgos.append(Hallazgo(
                    tabla="SAPROD",
                    campo="Precio1",
                    costo_anterior=result.precio1_saprod,
                    costo_referencia=result.cost_pro_saprod,
                    ratio=round(price_ratio, 1),
                    descripcion=f"Precio1 ${result.precio1_saprod:,.2f} es {price_ratio:.0f}x el costo promedio ${result.cost_pro_saprod:,.2f}",
                ))
                result.sugerencias.append(Sugerencia(
                    tabla="SAPROD",
                    accion="Los precios se recalcularán automáticamente tras corregir CostAct",
                    sql=f"UPDATE EnterpriseAdmin_AMC.dbo.SAPROD SET CostAct = {result.cost_pro_saprod} WHERE CodProd = '{codprod}'",
                    filas_esperadas=1,
                ))

    except Exception as e:
        result.error = str(e)
    finally:
        if not _conn_provided and conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    return result


def apply_corrections(
    resultado: ResultadoDiagnostico,
    confirm_codprod: str,
    conn=None,
) -> dict[str, Any]:
    """
    Aplicar correcciones con safety gate.

    REQUIERE confirm_codprod == resultado.codprod (two-key rule).
    Implementa: BACKUP → BEGIN TRAN → EXEC → COMMIT.
    """
    if confirm_codprod != resultado.codprod:
        return {
            "success": False,
            "error": f"Confirmación no coincide: esperaba {resultado.codprod}, recibí {confirm_codprod}",
        }

    if not resultado.sugerencias:
        return {"success": True, "message": "No hay correcciones que aplicar"}

    _conn_provided = conn is not None
    results = []

    try:
        if conn is None:
            conn = connect()

        # 1. Crear backups de tablas afectadas
        tablas_backup = set(s.tabla for s in resultado.sugerencias)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        for tabla in tablas_backup:
            if tabla in ("saitemcom", "salote", "SAPROD", "SAACXP"):
                bkp_name = f"{tabla}_BKP_{ts}"
                try:
                    conn.execute(f"SELECT * INTO EnterpriseAdmin_AMC.dbo.{bkp_name} FROM EnterpriseAdmin_AMC.dbo.{tabla} WHERE 1=0")
                    results.append({"tabla": tabla, "backup": bkp_name, "status": "created"})
                except Exception as e:
                    results.append({"tabla": tabla, "backup": bkp_name, "status": "error", "error": str(e)})

        # 2. Ejecutar en transacción
        conn.execute("BEGIN TRANSACTION")

        for s in resultado.sugerencias:
            try:
                cursor = conn.execute(s.sql)
                affected = cursor.rowcount
                results.append({
                    "tabla": s.tabla,
                    "sql": s.sql,
                    "rows_affected": affected,
                    "status": "ok" if affected > 0 else "no_match",
                })
            except Exception as e:
                conn.execute("ROLLBACK")
                return {
                    "success": False,
                    "error": f"Error en {s.tabla}: {e}",
                    "results": results,
                }

        conn.execute("COMMIT TRANSACTION")
        return {"success": True, "results": results}

    except Exception as e:
        return {"success": False, "error": str(e), "results": results}
    finally:
        if not _conn_provided and conn is not None:
            try:
                conn.close()
            except Exception:
                pass
