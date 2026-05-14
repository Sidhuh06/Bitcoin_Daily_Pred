import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv("btc_1sec_candles.csv")
df["time"] = pd.to_datetime(df["time"])

# features
df["return"] = df["close"].pct_change()
df["ma_5"] = df["close"].rolling(5).mean()
df["ma_10"] = df["close"].rolling(10).mean()
df["volatility"] = df["return"].rolling(10).std()

# target
df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

df.dropna(inplace=True)

X = df[["return", "ma_5", "ma_10", "volatility"]]
y = df["target"]

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, "model.pkl")

print("Model saved!")

import joblib

model = joblib.load("model.pkl")

def predict(df):

    X = df[["return", "ma_5", "ma_10", "volatility"]]

    pred = model.predict(X.iloc[[-1]])
    prob = model.predict_proba(X.iloc[[-1]])

    return pred[0], prob[0]