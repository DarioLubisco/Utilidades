# Utilidades Saint Enterprise (AMC)

Scripts portables para corregir fechas y cierre de mes en **EnterpriseAdmin_AMC**.

## Conexión

- **SQL Server (ZeroTier):** `10.147.18.192\efficacis3`
- **SQL Server (LAN):** `10.200.8.5\efficacis3` (fallback automático)
- **Credenciales:** variable de entorno `MSSQL_SA_PASSWORD` o archivo `.env` en la raíz de `source` (ver `.env.example`)

### Rutas locales buscadas (en orden)

1. `C:\source`
2. `C:\Users\DARIO LUBISCO\OneDrive\Sistemas\AntigravityBK\source`
3. Variable de entorno `AMC_SOURCE_ROOT`

Opcional: `N8N/synapse_credentials.md` (solo local, gitignored) como respaldo legacy.

## Scripts

| Script | Descripción |
|--------|-------------|
| `fix_saconf_dates_yesterday.py` | Ajusta `SACONF` (FechaUC, FechaUP, MesCurso) a ayer |
| `fix_fechas_futuras_saitemcom_salote.py` | Corrige fechas futuras en compras/lotes + UpdatePrices |
| `fix_dates_facturas.py` | Corrige facturas específicas: `python fix_dates_facturas.py 00106048` |

Scripts de diagnóstico adicionales en `saint/` (checks e investigaciones puntuales).

## Uso

```bash
cd source/Utilidades
python fix_saconf_dates_yesterday.py
```

### Variables de entorno opcionales

- `AMC_SOURCE_ROOT` — ruta a la carpeta source local
- `AMC_USE_ZEROTIER=0` — forzar conexión LAN en lugar de ZeroTier
- `MSSQL_SA_PASSWORD` — override de password SQL

## Copia remota

También desplegado en `10.147.18.4:/root/source/Utilidades` (host DL).
