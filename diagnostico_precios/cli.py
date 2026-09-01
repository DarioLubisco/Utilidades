"""
CLI adapter para diagnóstico de precios farmacéuticos.

Output JSON (default) para AI agents, --pretty para humanos.
Exit codes: 0=clean, 1=findings, 2=error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Agregar padre al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diagnostico_precios.diagnostico import (
    diagnose,
    apply_corrections,
    ResultadoDiagnostico,
)


def _format_pretty(r: ResultadoDiagnostico) -> str:
    """Formato legible para humanos."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"DIAGNÓSTICO DE PRECIOS - {r.codprod}")
    lines.append("=" * 60)

    if r.error:
        lines.append(f"\n❌ ERROR: {r.error}")
        return "\n".join(lines)

    lines.append(f"\nProducto: {r.descripcion}")
    lines.append(f"Costo Actual SAPROD: ${r.cost_act_saprod:,.4f}")
    lines.append(f"Costo Promedio SAPROD: ${r.cost_pro_saprod:,.4f}")
    lines.append(f"Precio1: ${r.precio1_saprod:,.4f}")
    lines.append(f"Precio2: ${r.precio2_saprod:,.4f}")
    lines.append(f"Precio3: ${r.precio3_saprod:,.4f}")

    if not r.hallazgos:
        lines.append("\n✅ No se encontraron errores de precio")
    else:
        lines.append(f"\n⚠️  {len(r.hallazgos)} HALLAZGO(S) ENCONTRADO(S):")
        lines.append("-" * 60)
        for i, h in enumerate(r.hallazgos, 1):
            lines.append(f"\n{i}. [{h.tabla}] {h.campo}")
            lines.append(f"   {h.descripcion}")
            if h.numero_d:
                lines.append(f"   Factura: {h.numero_d}")
            if h.proveedor:
                lines.append(f"   Proveedor: {h.proveedor}")
            if h.nro_lote:
                lines.append(f"   Lote: {h.nro_lote}")

        lines.append(f"\n📋 {len(r.sugerencias)} CORRECCIÓN(ES) SUGERIDA(S):")
        lines.append("-" * 60)
        for i, s in enumerate(r.sugerencias, 1):
            lines.append(f"\n{i}. [{s.tabla}] {s.accion}")
            lines.append(f"   SQL: {s.sql}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Diagnóstico de precios farmacéuticos - Saint Enterprise / AMC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Solo diagnóstico
  python diagnosticar_precios.py --codprod 7707816985561 --desde 01/01/2026 --hasta 01/08/2026

  # Con umbral personalizado
  python diagnosticar_precios.py --codprod 7707816985561 --desde 01/01/2026 --hasta 01/08/2026 --umbral 2.0

  # Aplicar correcciones (requiere confirmación)
  python diagnosticar_precios.py --codprod 7707816985561 --desde 01/01/2026 --hasta 01/08/2026 --apply --confirm 7707816985561
""",
    )

    parser.add_argument("--codprod", required=True, help="Código del producto (SAPROD.CodProd)")
    parser.add_argument("--desde", required=True, help="Fecha inicio (DD/MM/YYYY o YYYY-MM-DD)")
    parser.add_argument("--hasta", required=True, help="Fecha fin (DD/MM/YYYY o YYYY-MM-DD)")
    parser.add_argument("--umbral", type=float, default=1.6, help="Ratio mínimo para detectar error (default: 1.6)")
    parser.add_argument("--json", action="store_true", default=True, help="Output JSON (default)")
    parser.add_argument("--pretty", action="store_true", help="Output legible para humanos")
    parser.add_argument("--apply", action="store_true", help="Aplicar correcciones (requiere --confirm)")
    parser.add_argument("--confirm", metavar="CODPROD", help="Confirmar aplicación (debe coincidir con --codprod)")

    args = parser.parse_args(argv)

    # Validar apply + confirm
    if args.apply and not args.confirm:
        parser.error("--apply requiere --confirm <CODPROD>")
    if args.apply and args.confirm != args.codprod:
        parser.error(f"--confirm debe coincidir con --codprod: esperaba {args.codprod}, recibí {args.confirm}")

    # Ejecutar diagnóstico
    try:
        result = diagnose(args.codprod, args.desde, args.hasta, args.umbral)
    except Exception as e:
        error_result = {
            "status": "error",
            "codprod": args.codprod,
            "error": str(e),
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(2)

    # Aplicar si se pidió
    if args.apply:
        apply_result = apply_corrections(result, args.confirm)
        if not apply_result.get("success"):
            result_dict = result.to_dict()
            result_dict["apply_result"] = apply_result
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
            sys.exit(2)

    # Output
    if args.pretty:
        print(_format_pretty(result))
    else:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    # Exit code
    if result.error:
        sys.exit(2)
    elif result.hallazgos:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
