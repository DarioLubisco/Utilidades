#!/bin/bash
# Ejecuta utilidades Saint Enterprise desde 10.147.18.4 (o cualquier host con ZeroTier)
cd "$(dirname "$0")"
export AMC_USE_ZEROTIER=1
export AMC_SOURCE_ROOT="${AMC_SOURCE_ROOT:-/root/source}"

case "${1:-help}" in
  saconf)   python3 fix_saconf_dates_yesterday.py ;;
  fechas)   python3 fix_fechas_futuras_saitemcom_salote.py ;;
  facturas) shift; python3 fix_dates_facturas.py "$@" ;;
  test)     python3 test_connection.py ;;
  *)
    echo "Uso: $0 {saconf|fechas|facturas|test}"
    echo "  saconf   - Corrige SACONF (cierre de mes)"
    echo "  fechas   - Corrige fechas futuras SAITEMCOM/SALOTE"
    echo "  facturas - Corrige facturas: $0 facturas 00106048 00352877"
    echo "  test     - Prueba conexión SQL via ZeroTier"
    ;;
esac
