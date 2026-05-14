import websocket
import json
import pandas as pd
from datetime import datetime
import threading
import time

# =====================================================
# GLOBAL STORAGE
# =====================================================

current_second = None
prices = []

csv_file = "btc_1sec_candles.csv"

# Create CSV if not exists
try:
    pd.read_csv(csv_file)
except:
    df = pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    df.to_csv(csv_file, index=False)

# =====================================================
# FUNCTION TO SAVE CANDLE
# =====================================================

def save_candle(second, prices):

    if not prices:
        return

    candle = {
        "time": second,
        "open": prices[0],
        "high": max(prices),
        "low": min(prices),
        "close": prices[-1]
    }

    df = pd.DataFrame([candle])
    df.to_csv(csv_file, mode="a", header=False, index=False)

    print("Saved:", candle)

# =====================================================
# WEBSOCKET MESSAGE HANDLER
# =====================================================

def on_message(ws, message):
    global current_second, prices

    data = json.loads(message)

    price = float(data["p"])
    trade_time = datetime.fromtimestamp(data["T"] / 1000)

    second = trade_time.replace(microsecond=0)

    # FIRST TIME
    if current_second is None:
        current_second = second

    # SAME SECOND → accumulate
    if second == current_second:
        prices.append(price)

    else:
        # NEW SECOND → save previous candle
        save_candle(current_second, prices)

        # RESET for new second
        current_second = second
        prices = [price]

# =====================================================
# SOCKET EVENTS
# =====================================================

def on_open(ws):
    print("Connected to Binance")

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, code, msg):
    print("Socket closed")

# =====================================================
# START SOCKET
# =====================================================

def start_socket():
    socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    ws = websocket.WebSocketApp(
        socket,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    start_socket()