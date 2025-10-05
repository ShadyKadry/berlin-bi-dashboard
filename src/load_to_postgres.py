from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
PG_USER = os.getenv("PGUSER", "shady")
PG_PASS = os.getenv("PGPASSWORD", "shady")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5433")
PG_DB   = os.getenv("PGDATABASE", "berlin_bi")

engine = create_engine(f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}")

# --- Read & normalize CSV ---
df = pd.read_csv("data/raw/berlin_weather.csv")
df.columns = [c.strip().lower() for c in df.columns]

# map possible timestamp column names -> 'ts'
for cand in ["ts", "timestamp", "time", "datetime"]:
    if cand in df.columns:
        if cand != "ts":
            df = df.rename(columns={cand: "ts"})
        break
else:
    raise RuntimeError(f"No timestamp column found. Have columns: {list(df.columns)}")

# parse datetime as UTC
df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
df = df.dropna(subset=["ts"])

# enforce expected schema keys
expected = {"city","ts","temperature","humidity","pressure","wind_speed","weather_code"}
missing = expected - set(df.columns)
if missing:
    raise RuntimeError(f"Missing columns in CSV: {sorted(missing)}")

# --- UPSERT into Postgres on (city, ts) ---
meta = MetaData()
weather = Table("weather", meta, autoload_with=engine)

rows = df.to_dict(orient="records")

with engine.begin() as conn:
    stmt = insert(weather).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in weather.columns
        if c.name not in ("id", "city", "ts")  # don't overwrite PK parts or surrogate id
    }
    upsert = stmt.on_conflict_do_update(
        index_elements=["city", "ts"],  # matches your UNIQUE(city, ts)
        set_=update_cols
    )
    conn.execute(upsert)

print(f"Upserted {len(df)} weather records into PostgreSQL.")

