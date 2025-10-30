# app.py
# DISCLAIMER: Educational purposes only — not financial advice.
# Uses Yahoo Finance for live data.

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="1-Week Stock Screener", layout="wide")

st.title("📈 1-Week Stock Screener (Under $50)")
st.caption("Educational tool — not financial advice. Uses Yahoo Finance data.")

# --- User Inputs ---
capital = st.number_input("💰 Total Capital ($)", min_value=100, value=1000, step=100)
num_positions = st.slider("📊 Number of Stocks", 5, 20, 10)
max_price = st.number_input("💵 Max Stock Price ($)", min_value=1.0, value=50.0, step=1.0)
min_volume = st.number_input("📈 Min Avg Daily Volume", min_value=100000, value=500000, step=50000)
run = st.button("🔍 Run Screener")

# --- Helper Function ---
@st.cache_data(ttl=3600)
def fetch_data(tickers):
    end = datetime.now()
    start = end - timedelta(days=15)
    data = yf.download(tickers, start=start, end=end, progress=False, group_by='ticker', threads=True, auto_adjust=True)
    return data

def calc_signals(df):
    df = df.copy()
    df["Return"] = df["Close"].pct_change()
    mom_3d = (df["Close"].iloc[-1] - df["Close"].iloc[-4]) / df["Close"].iloc[-4]
    mom_10d = (df["Close"].iloc[-1] - df["Close"].iloc[-11]) / df["Close"].iloc[-11]
    vol_10d = df["Return"].tail(10).std()
    return mom_3d, mom_10d, vol_10d

# --- Run Screener ---
if run:
    with st.spinner("Fetching live data..."):
        # Small universe for demo
        tickers = ["AAPL","MSFT","AMD","NVDA","INTC","F","T","SOUN","CHPT","PLUG","NOK","BBAI","U","SNAP","DKNG","PYPL","SOFI","UBER","LYFT","MARA","RIOT"]
        data = fetch_data(tickers)

    results = []
    for t in tickers:
        try:
            df = data[t]
            last_close = df["Close"].iloc[-1]
            avg_vol = df["Volume"].tail(10).mean()
            if last_close <= max_price and avg_vol >= min_volume:
                m3, m10, vol = calc_signals(df)
                score = 0.5*m3 + 0.3*m10 - 0.2*vol  # composite score
                results.append([t, last_close, avg_vol, m3, m10, vol, score])
        except Exception:
            continue

    if not results:
        st.error("No stocks matched your filters. Try lowering volume or raising max price.")
    else:
        df_results = pd.DataFrame(results, columns=["Ticker","Price","AvgVol","Mom3D","Mom10D","Vol10D","Score"])
        df_results.sort_values("Score", ascending=False, inplace=True)
        top = df_results.head(num_positions).copy()

        st.subheader("🏆 Top Candidates")
        st.dataframe(top.style.format({"Price":"${:.2f}","AvgVol":"{:.0f}","Mom3D":"{:.2%}","Mom10D":"{:.2%}","Vol10D":"{:.2%}","Score":"{:.4f}"}))

        st.subheader("📦 Suggested Allocation")
        per_slot = capital / num_positions
        top["Shares"] = (per_slot // top["Price"]).astype(int)
        top["Cost"] = top["Shares"] * top["Price"]
        st.dataframe(top[["Ticker","Price","Shares","Cost"]].style.format({"Price":"${:.2f}","Cost":"${:.2f}"}))

        total_invested = top["Cost"].sum()
        st.metric("Total Invested", f"${total_invested:,.2f}")
        st.success("✅ Screener complete! Data refreshes every hour.")
else:
    st.info("Adjust your settings and click **Run Screener** to begin.")
