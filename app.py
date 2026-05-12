import os
import streamlit as st
import websocket
import json
import pandas as pd
import sqlite3
import threading
from datetime import datetime
import plotly.graph_objs as go
import torch
from chronos import ChronosPipeline
from streamlit_autorefresh import st_autorefresh

# =====================================================
# CLEAN LOGS (OPTIONAL)
# =====================================================

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =====================================================
# STREAMLIT CONFIG
# =====================================================

st.set_page_config(page_title="Bitcoin AI Dashboard", layout="wide")
st.title("🚀 Bitcoin Live Dashboard + AI Forecast")

# =====================================================
# AUTO REFRESH (THIS IS THE KEY FIX)
# =====================================================

st_autorefresh(interval=5000, key="btc_refresh")

# =====================================================
# DATABASE
# =====================================================

DB_NAME = "live_bitcoin.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS btc_live (
    timestamp TEXT,
    price REAL
)
""")
conn.commit()

# =====================================================
# GLOBAL BUFFER (THREAD SAFE)
# =====================================================

price_buffer = []
lock = threading.Lock()

# =====================================================
# BINANCE WEBSOCKET
# =====================================================

SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@trade"

def on_message(ws, message):
    try:
        data = json.loads(message)

        price = float(data["p"])
        t = datetime.fromtimestamp(data["T"] / 1000)

        row = {"time": t, "price": price}

        with lock:
            price_buffer.append(row)
            if len(price_buffer) > 5000:
                del price_buffer[:1000]

        cursor.execute(
            "INSERT INTO btc_live VALUES (?, ?)",
            (t.strftime("%Y-%m-%d %H:%M:%S"), price)
        )
        conn.commit()

    except Exception as e:
        print("Error:", e)

def on_open(ws):
    print("Connected to Binance")

def on_error(ws, error):
    print("Socket error:", error)

def on_close(ws, code, msg):
    print("Socket closed")

def start_socket():
    ws = websocket.WebSocketApp(
        SOCKET,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# =====================================================
# START SOCKET ONCE
# =====================================================

if "socket_started" not in st.session_state:
    t = threading.Thread(target=start_socket, daemon=True)
    t.start()
    st.session_state.socket_started = True

# =====================================================
# LOAD MODEL
# =====================================================

@st.cache_resource
def load_model():
    return ChronosPipeline.from_pretrained(
        "amazon/chronos-t5-small",
        device_map="cpu"
    )

pipeline = load_model()

# =====================================================
# GET LIVE DATA SAFELY
# =====================================================

with lock:
    data = list(price_buffer)

df = pd.DataFrame(data)

placeholder = st.empty()

# =====================================================
# MAIN LOGIC
# =====================================================

if not df.empty:

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")

    # stable resample
    minute_df = (
        df.set_index("time")
          .resample("1min")
          .last()
          .dropna()
          .reset_index()
    )

    latest_price = minute_df["price"].iloc[-1]

    # =================================================
    # AI FORECAST
    # =================================================

    pred_df = pd.DataFrame()

    try:
        if len(minute_df) >= 60:

            series = torch.tensor(
                minute_df["price"].values,
                dtype=torch.float32
            )

            forecast = pipeline.predict(
                series.unsqueeze(0),
                prediction_length=60
            )

            predictions = forecast[0].median(dim=0).values.numpy()

            future_time = pd.date_range(
                start=minute_df["time"].iloc[-1],
                periods=61,
                freq="min"
            )[1:]

            pred_df = pd.DataFrame({
                "time": future_time,
                "prediction": predictions
            })

    except Exception as e:
        print("Prediction error:", e)

    # =================================================
    # PLOT
    # =================================================

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=minute_df["time"],
        y=minute_df["price"],
        mode="lines",
        name="Live BTC"
    ))

    if not pred_df.empty:
        fig.add_trace(go.Scatter(
            x=pred_df["time"],
            y=pred_df["prediction"],
            mode="lines",
            name="Forecast"
        ))

    fig.update_layout(
        template="plotly_dark",
        height=700,
        title="Bitcoin Live Price + AI Forecast",
        xaxis_title="Time",
        yaxis_title="Price",
        hovermode="x unified"
    )

    # =================================================
    # UI
    # =================================================

    with placeholder.container():

        col1, col2 = st.columns(2)

        col1.metric("BTC/USDT", f"${latest_price:,.2f}")
        col2.metric("Records", len(minute_df))

        st.plotly_chart(fig, width="stretch")

        st.subheader("Latest Data")
        st.dataframe(minute_df.tail(30), width="stretch")

else:
    st.warning("Waiting for live Binance data...")