import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
import plotly.express as px
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import streamlit as st
import plotly.express as px

load_dotenv()

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5433")
PGUSER = os.getenv("PGUSER", "shady")
PGPASSWORD = os.getenv("PGPASSWORD", "shady")
PGDATABASE = os.getenv("PGDATABASE", "berlin_bi")

engine = create_engine(f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}")


st.set_page_config(page_title="Berlin Weather BI", layout="wide")
engine = create_engine("postgresql+psycopg2://shady:shady@127.0.0.1:5433/berlin_bi")

@st.cache_data(ttl=300)
def load():
    return pd.read_sql(
        "SELECT city, ts, temperature, humidity, pressure, wind_speed, weather_code FROM weather ORDER BY ts",
        engine,
        parse_dates=["ts"]
    )

df = load()
st.title("Berlin Weather - BI Snapshot")

if df.empty:
    st.warning("No data yet. Run: python src/ingest_once.py")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Records", len(df))
    c2.metric("Last temp (C)", f"{df['temperature'].iloc[-1]:.1f}")
    c3.metric("Last humidity (%)", f"{int(df['humidity'].iloc[-1])}")

    fig1 = px.line(df, x="ts", y="temperature", title="Temperature (C)")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(df, x="ts", y="humidity", title="Humidity (%)")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Latest rows")
    st.dataframe(df.tail(10), use_container_width=True)
daily = pd.read_sql("SELECT day, avg_temp, min_temp, max_temp, avg_humidity FROM weather_daily ORDER BY day", engine, parse_dates=["day"])
st.subheader("Daily summary (last 7–8 days)")
if not daily.empty:
    st.line_chart(daily.set_index("day")[["avg_temp"]])
    st.dataframe(daily.tail(10), use_container_width=True)
else:
    st.info("No daily summary yet. It will appear after refresh.")

