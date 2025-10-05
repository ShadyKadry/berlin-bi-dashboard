from sqlalchemy import create_engine, text
import pandas as pd

df = pd.read_csv("data/raw/berlin_weather.csv")
df = df.rename(columns={"timestamp": "ts"})
df["ts"] = pd.to_datetime(df["ts"], errors="coerce")  # local time ok

engine = create_engine("postgresql+psycopg2://shady:shady@127.0.0.1:5433/berlin_bi")

insert_sql = text("""
INSERT INTO weather (city, ts, temperature, humidity, pressure, wind_speed, weather_code, source)
VALUES (:city, :ts, :temperature, :humidity, :pressure, :wind_speed, :weather_code, 'open-meteo')
ON CONFLICT (ts) DO UPDATE
SET temperature = EXCLUDED.temperature,
    humidity    = EXCLUDED.humidity,
    pressure    = EXCLUDED.pressure,
    wind_speed  = EXCLUDED.wind_speed,
    weather_code= EXCLUDED.weather_code,
    source      = EXCLUDED.source;
""")

with engine.begin() as conn:
    conn.execute(insert_sql, df.to_dict(orient="records"))

print(f"Upserted {len(df)} weather records into PostgreSQL.")
