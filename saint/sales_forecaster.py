import os
import sys
import subprocess
import logging
from datetime import datetime

def auto_install_deps():
    """Auto-Healing: Verifica y restaura dependencias maestras si el entorno Python se actualizo/corrompio."""
    try:
        import pandas
        import sqlalchemy
        import prophet
        import pyodbc
    except ImportError as e:
        print(f"[AUTO-HEALING] Falta una libreria ({e}). Restaurando entorno...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q", "--break-system-packages",
                "pandas", "sqlalchemy", "prophet", "pyodbc"
            ])
            print("[AUTO-HEALING] Dependencias instaladas exitosamente. Reiniciando script...")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as ex:
            print(f"[FATAL] Auto-Healing fallo al instalar dependencias: {ex}")
            sys.exit(1)

auto_install_deps()

import pandas as pd
from sqlalchemy import create_engine, text
from prophet import Prophet


# 1. Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Variables de Conexión
# (De acuerdo a lo proporcionado por el usuario)
DB_SERVER = r"10.200.8.5\efficacis3"
DB_DATABASE = "EnterpriseAdmin_AMC"
DB_USERNAME = "sa"
DB_PASSWORD = "Twinc3pt."
DRIVER = "ODBC Driver 18 for SQL Server"

def get_engine():
    """Genera el motor de conexión SQLAlchemy para SQL Server."""
    connection_string = (
        f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_DATABASE}"
        f"?driver={DRIVER.replace(' ', '+')}"
        "&TrustServerCertificate=yes"
    )
    return create_engine(connection_string, fast_executemany=True)

def ensure_schema_exists(engine):
    """Asegura que el esquema 'Procurement' exista en la base de datos."""
    with engine.begin() as conn:
        conn.execute(text(
            "IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Procurement') "
            "BEGIN "
            "   EXEC('CREATE SCHEMA [Procurement]'); "
            "END"
        ))
    logger.info("Esquema 'Procurement' verificado.")

def extract_sales_data(engine):
    """Extrae y pre-procesa las ventas diarias en USD de CUSTOM_SAEVTA."""
    logger.info("Extrayendo histórico de ventas de CUSTOM_SAEVTA...")
    # Agrupamos por fecha y sumamos el monto en dolares. MtoDolar es varchar, por ende lo casteamos a float.
    # Además, casteamos la fecha a datetime.
    query = """
        SELECT 
            CAST(fecha AS DATE) AS ds,
            SUM(CAST(REPLACE(MtoDolar, ',', '') AS FLOAT)) AS y
        FROM CUSTOM_SAEVTA
        WHERE fecha IS NOT NULL AND MtoDolar IS NOT NULL
        GROUP BY CAST(fecha AS DATE)
        ORDER BY ds ASC
    """
    df = pd.read_sql(query, engine)
    
    # Convertir 'ds' a datetime64[ns] para Prophet
    df['ds'] = pd.to_datetime(df['ds'])
    
    # Rellenar nulos
    df['y'] = df['y'].fillna(0)
    logger.info(f"Histórico extraído: {len(df)} días de ventas.")
    return df

def get_latest_exchange_rate(engine):
    """Obtiene la última tasa de cambio de la tabla dolartoday (columna dolarbcv)."""
    logger.info("Consultando la última tasa de cambio disponible en dolartoday...")
    query = "SELECT TOP 1 dolarbcv FROM dbo.dolartoday ORDER BY fecha DESC"
    with engine.connect() as conn:
        result = conn.execute(text(query)).scalar()
        
    rate = float(result) if result else 0.0
    logger.info(f"Tasa de cambio obtenida (dolarbcv): {rate}")
    return rate

def extract_forecast_events(engine):
    """Extrae los eventos (variables exógenas) de la base de datos."""
    logger.info("Extrayendo variables exógenas (eventos) de forecast_events...")
    query = "SELECT CAST(fecha AS DATE) as ds, tipo_evento, valor FROM EnterpriseAdmin_AMC.Procurement.forecast_events"
    try:
        df_events = pd.read_sql(query, engine)
        if not df_events.empty:
            df_events['ds'] = pd.to_datetime(df_events['ds'])
            logger.info(f"Se encontraron {len(df_events)} eventos exógenos.")
        return df_events
    except Exception as e:
        logger.warning(f"No se pudo consultar forecast_events o la tabla está vacía: {e}")
        return pd.DataFrame(columns=['ds', 'tipo_evento', 'valor'])

def apply_regressors(df, df_events, unique_events):
    """Aplica características de calendario y eventos exógenos a un dataframe."""
    df = df.copy()
    
    # --- 1. Regresor: Quincena / Fin de Mes ---
    # Fuerte impacto de inyección de liquidez en el país
    df['is_quincena'] = df['ds'].apply(
        lambda x: 1.0 if x.day == 15 or x.day == x.days_in_month else 0.0
    )

    # --- 2. Regresores Fiestas / Eventos BD ---
    if not df_events.empty:
        # Hacemos un pivote para que cada tipo de evento sea una columna
        events_pivot = df_events.pivot_table(index='ds', columns='tipo_evento', values='valor', aggfunc='sum').reset_index()
        df = df.merge(events_pivot, on='ds', how='left')
    
    # Rellenar con 0.0 los días sin esos eventos
    for evt in unique_events:
        if evt not in df.columns:
            df[evt] = 0.0
        else:
            df[evt] = df[evt].fillna(0.0)
            
    return df


def forecast_sales(df_hist, df_events, days=180):
    """Ejecuta el algoritmo Prophet para proyectar las ventas futuras."""
    logger.info(f"Entrenando modelo Prophet. Proyectando {days} días...")
    
    # Determinar los tipos únicos de eventos de la BD
    unique_events = df_events['tipo_evento'].unique().tolist() if not df_events.empty else []
    
    # Preparar df_histólico con los regresores
    df_hist_reg = apply_regressors(df_hist, df_events, unique_events)
    
    # Configuramos el modelo
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
    
    # Agregar Feriados (Built-in para Venezuela)
    # Dependiendo de la versión de la librería 'holidays', 'VE' está soportado.
    try:
        model.add_country_holidays(country_name='VE')
    except Exception as e:
        logger.warning("Feriados de VE no soportados directamente por la librería, ignorando feriados built-in.")

    # Añadir regresores al modelo
    model.add_regressor('is_quincena')
    for evt in unique_events:
        model.add_regressor(evt)

    # Entrenar
    model.fit(df_hist_reg)
    
    # Crear marco de fechas futuro
    future = model.make_future_dataframe(periods=days, freq='D')
    
    # Preparar df_future con los mismos regresores
    future_reg = apply_regressors(future, df_events, unique_events)
    
    # Realizar predicción
    forecast = model.predict(future_reg)
    
    # Filtrar solo el periodo futuro (excluir histórico)
    forecast_future = forecast[forecast['ds'] > df_hist['ds'].max()].copy()
    
    # Evitar ventas negativas (piso en 0)
    forecast_future['yhat'] = forecast_future['yhat'].clip(lower=0)
    
    logger.info(f"Proyección generada: {len(forecast_future)} días.")
    return forecast_future[['ds', 'yhat']]


def load_forecast_to_db(engine, df_forecast, exchange_rate):
    """Formatea la salida y la carga en Procurement.sales_forecast."""
    logger.info("Preparando datos para la carga a Base de Datos...")
    
    df_output = pd.DataFrame({
        'fecha_proyeccion': df_forecast['ds'],
        'monto_proyectado_usd': df_forecast['yhat'].round(2),
        'monto_proyectado_ves': (df_forecast['yhat'] * exchange_rate).round(2),
        'fecha_calculo': datetime.now()
    })
    
    logger.info(f"Volcando {len(df_output)} predicciones en la tabla Procurement.sales_forecast...")
    df_output.to_sql(
        name='sales_forecast',
        schema='Procurement',
        con=engine,
        if_exists='replace',
        index=False
    )
    
    # Verificación inmediata
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM Procurement.sales_forecast")).scalar()
        logger.info(f"Carga completada. Filas en tabla: {count}")

def main():
    try:
        engine = get_engine()
        ensure_schema_exists(engine)
        
        df_historico = extract_sales_data(engine)
        
        if df_historico.empty:
            logger.warning("No se encontraron registros de ventas para procesar.")
            return

        exchange_rate = get_latest_exchange_rate(engine)
        if exchange_rate == 0.0:
            logger.warning("No se pudo obtener la tasa de cambio. La proyección en VES será 0.")
            
        df_events = extract_forecast_events(engine)
            
        df_prediccion = forecast_sales(df_historico, df_events, days=180)
        
        load_forecast_to_db(engine, df_prediccion, exchange_rate)
        
        logger.info("Proceso ETL de Forecasting finalizado correctamente.")
    except Exception as e:
        logger.error(f"Error durante la ejecución del proceso: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
