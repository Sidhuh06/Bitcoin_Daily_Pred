import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from processor import load_recent_data

st.title("BTC Live 3-Min Analysis")

df = load_recent_data("btc_1sec_candles.csv")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["time"],
    y=df["close"],
    mode="lines",
    name="Price"
))

st.plotly_chart(fig, width="stretch")

st.dataframe(df.tail(20))