import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd

load_dotenv()  # loads .env into process env

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5433")
PGUSER = os.getenv("PGUSER", "shady")
PGPASSWORD = os.getenv("PGPASSWORD", "shady")
PGDATABASE = os.getenv("PGDATABASE", "berlin_bi")

engine = create_engine(f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}")

df = pd.read_csv("data/raw/berlin_weather.csv")
df.rename(columns={"timestamp": "ts"}, inplace=True)
df.to_sql("weather", engine, if_exists="append", index=False)
print(f"Loaded {len(df)} weather records into PostgreSQL.")

