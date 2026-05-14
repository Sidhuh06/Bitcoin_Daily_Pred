import pandas as pd

# =========================================
# LOAD LAST 3 MIN DATA
# =========================================

def load_recent_data(csv_file):

    df = pd.read_csv(csv_file)

    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"])

    latest_time = df["time"].max()
    start_time = latest_time - pd.Timedelta(minutes=3)

    df = df[df["time"] >= start_time]

    return df


# =========================================
# FEATURE ENGINEERING
# =========================================

def create_features(df):

    df = df.copy()

    df["return"] = df["close"].pct_change()

    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_10"] = df["close"].rolling(10).mean()

    df["volatility"] = df["return"].rolling(10).std()

    df.dropna(inplace=True)

    return df