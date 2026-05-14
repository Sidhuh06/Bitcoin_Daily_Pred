import time
from processor import load_recent_data, create_features
import joblib

model = joblib.load("model.pkl")

csv_file = "btc_1sec_candles.csv"

while True:

    try:
        df = load_recent_data(csv_file)

        if len(df) < 20:
            print("Not enough data...")
            time.sleep(30)
            continue

        df = create_features(df)

        X = df[["return", "ma_5", "ma_10", "volatility"]]

        pred = model.predict(X.iloc[[-1]])
        prob = model.predict_proba(X.iloc[[-1]])

        print("Prediction:", "UP" if pred[0] == 1 else "DOWN")
        print("Confidence:", prob[0])

    except Exception as e:
        print("Error:", e)

    # wait 3 minutes
    time.sleep(180)

    