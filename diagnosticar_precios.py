#!/usr/bin/env python3
"""
Diagnóstico de Precios Farmacéuticos - Saint Enterprise / AMC

Shim ejecutable que delega a diagnostico_precios.cli.

Uso:
    python diagnosticar_precios.py --codprod 7707816985561 --desde 01/01/2026 --hasta 01/08/2026
    python diagnosticar_precios.py --codprod 7707816985561 --desde 01/01/2026 --hasta 01/08/2026 --pretty
    python diagnosticar_precios.py --codprod 7707816985561 --desde 01/01/2026 --hasta 01/08/2026 --apply --confirm 7707816985561
"""
import sys
from pathlib import Path

# Asegurar que Utilidades está en el path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostico_precios.cli import main

if __name__ == "__main__":
    main()
