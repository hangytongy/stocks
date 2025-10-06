## get 50 and 200 MA for nasdaq 100 vs SNP

import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
import numpy as np
import os
from dotenv import load_dotenv
import time 

sns.set()

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_photo(photo_path, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    files = {"photo": open(photo_path, "rb")}
    
    payload = {}
    if "_" in TELEGRAM_CHAT_ID:
        ids = TELEGRAM_CHAT_ID.split("_")
        payload = {
            "chat_id": ids[0],
            "message_thread_id": ids[1],
            "caption": text
        }
    else:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": text
        }

    response = requests.post(url, data=payload, files=files)
    print(response.json())


def get_nasdaq100_from_slickcharts():
    url = "https://www.slickcharts.com/nasdaq100"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Grab table
    table = soup.find("table", {"class": "table"})
    df = pd.read_html(str(table))[0]

    tickers = df["Symbol"].tolist()
    return tickers, df

nasdaq100_tickers, df = get_nasdaq100_from_slickcharts()
print("✅ Nasdaq-100 tickers:", nasdaq100_tickers)


def main():
    # -----------------------------
    # Step 2: Download historical prices
    # -----------------------------
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = datetime.now() - timedelta(days=6*365)
    start_date = start_date.strftime("%Y-%m-%d")


    data = yf.download(nasdaq100_tickers, start=start_date, end=end_date)
    data = data["Close"]


    # S&P 500 index
    sp500 = "^GSPC"
    spx_data = yf.download(sp500, start=start_date, end=end_date)
    spx_data = spx_data["Close"]

    # -----------------------------
    # Step 3: Calculate MAs & breadth
    # -----------------------------
    ma50 = data.rolling(window=50).mean()
    ma200 = data.rolling(window=200).mean()

    # Boolean masks: stock above MA?
    above50 = (data > ma50).sum(axis=1) / len(nasdaq100_tickers) * 100
    above200 = (data > ma200).sum(axis=1) / len(nasdaq100_tickers) * 100

    above50_series = above50.squeeze()   # converts (1510,1) -> (1510,)
    above200_series = above200.squeeze()
    spx_series = spx_data.squeeze()     # if you want to include SP500

    # Combine into a DataFrame
    breadth_df = pd.DataFrame({
        "Above50%": above50_series,
        "Above200%": above200_series,
        "SP500": spx_series
    }, index=data.index)  # keep dates as index


    # -----------------------------
    # Step 4: Plot against SNP
    # -----------------------------

    last_year_df = breadth_df.tail(90)

    # -----------------------------
    # Chart 1: Above50% vs S&P 500
    # -----------------------------
    fig, ax1 = plt.subplots(figsize=(20,10))

    # S&P 500 line
    ax1.plot(last_year_df.index, last_year_df["SP500"], color="black", label="S&P 500")
    ax1.set_ylabel("S&P 500", color="black", fontsize=16)
    ax1.tick_params(axis="y", labelcolor="black", labelsize=14)
    ax1.tick_params(axis="x", labelsize=14)

    # Breadth bars
    colors_50 = np.where(last_year_df["Above50%"] > 85, "red",
                np.where(last_year_df["Above50%"] < 20, "green", "blue"))
    ax2 = ax1.twinx()
    ax2.bar(last_year_df.index, last_year_df["Above50%"], color=colors_50, alpha=0.6, label="% Above 50DMA")
    ax2.set_ylabel("Breadth (%)", color="blue", fontsize=16)
    ax2.tick_params(axis="y", labelcolor="blue", labelsize=14)
    ax2.set_ylim(0,100)

    # Legend and title
    fig.legend(loc="upper left", bbox_to_anchor=(0.1,0.9), fontsize=14)
    plt.title("Nasdaq-100 Breadth (% Above 50DMA) vs S&P 500", fontsize=20)
    plt.savefig("nasdaq100_signal_50MA.png")

    # -----------------------------
    # Chart 2: Above200% vs S&P 500
    # -----------------------------
    fig, ax1 = plt.subplots(figsize=(20,10))

    ax1.plot(last_year_df.index, last_year_df["SP500"], color="black", label="S&P 500")
    ax1.set_ylabel("S&P 500", color="black", fontsize=16)
    ax1.tick_params(axis="y", labelcolor="black", labelsize=14)
    ax1.tick_params(axis="x", labelsize=14)

    colors_200 = np.where(last_year_df["Above200%"] > 85, "red",
                np.where(last_year_df["Above200%"] < 20, "green", "blue"))
    ax2 = ax1.twinx()
    ax2.bar(last_year_df.index, last_year_df["Above200%"], color=colors_200, alpha=0.6, label="% Above 200DMA")
    ax2.set_ylabel("Breadth (%)", color="blue", fontsize=16)
    ax2.tick_params(axis="y", labelcolor="blue", labelsize=14)
    ax2.set_ylim(0,100)

    fig.legend(loc="upper left", bbox_to_anchor=(0.1,0.9), fontsize=14)
    plt.title("Nasdaq-100 Breadth (% Above 200DMA) vs S&P 500", fontsize=20)
    plt.savefig("nasdaq100_signal_200MA.png")

    time.sleep(5)

    send_telegram_photo("nasdaq100_signal_50MA.png", "Nasdaq-100 Breadth (% Above 50DMA) vs S&P 500")
    time.sleep(5)
    send_telegram_photo("nasdaq100_signal_200MA.png", "Nasdaq-100 Breadth (% Above 200DMA) vs S&P 500")

if __name__ == "__main__":
    main()
