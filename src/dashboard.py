import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine

# Connect to PostgreSQL
engine = create_engine("postgresql://shady:shady@127.0.0.1:5432/berlin_bi")

# Query aggregated data
df = pd.read_sql("SELECT bezirk, COUNT(*) AS count FROM companies GROUP BY bezirk ORDER BY count DESC", engine)

# Create bar chart
app = dash.Dash(__name__)
fig = px.bar(df, x="bezirk", y="count", title="Companies per Berlin District")

app.layout = html.Div([
    html.H1("Berlin Business Intelligence Dashboard"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run_server(debug=True)
