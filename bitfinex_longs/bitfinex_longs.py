import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

import os
from dotenv import load_dotenv

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


def longs():
    num_days = 365

    url ="https://s1.bitcoinwisdom.io/period?step=86400&symbol=bitfinexbtcusdlongs&3d_format=&nonce=1763022521"

    response = requests.get(url)

    if response.status_code == 200:

        data = response.json()

        timestamp = [i[0] for i in data]
        longs = [i[3] for i in data]

        data = {
            'timestamp' : timestamp,
            'longs' : longs
        }

        df = pd.DataFrame(data)

        df['time'] = pd.to_datetime(df['timestamp'], unit = 's')

        # Get current time
        now = pd.Timestamp.now()

        # Define cutoff date (365 days ago)
        cutoff = now - pd.Timedelta(days=num_days)

        # Filter only last 365 days
        df_last_year = df[df['time'] >= cutoff]
        
    else:
        print("unable to get data for bitfinex btc longs")
        
    y = df_last_year['longs'] - df_last_year['longs'].iloc[0]
    x = df_last_year['time']

    period_num = str(num_days)+'d'

    btc = yf.download("BTC-USD", period=period_num, interval="1d").reset_index()
    btc = btc[['Date', 'Close']]

    time = btc['Date'].tolist()
    close = btc['Close']['BTC-USD'].tolist()
    btc_df = {
        'time' : time,
        'close': close
    }

    btc_df = pd.DataFrame(btc_df)

    # --- Create figure / primary axis ---
    fig, ax1 = plt.subplots(figsize=(20, 10))

    # --- Green positive area ---
    ax1.fill_between(
        x,
        y,
        where=(y >= 0),
        alpha=0.5,
        label='Longs (Positive)'
    )

    # --- Red negative area ---
    ax1.fill_between(
        x,
        y,
        where=(y < 0),
        alpha=0.5,
        label='Longs (Negative)'
    )

    # Zero-line for clarity
    ax1.axhline(0, color='blue', linewidth=1)

    # Labels for primary axis
    ax1.set_xlabel('Date', fontsize=17)
    ax1.set_ylabel('Longs (Area Chart)', fontsize=17)
    ax1.tick_params(axis='both', labelsize=17)

    # --- Secondary axis (BTC Price) ---
    ax2 = ax1.twinx()
    ax2.plot(btc_df['time'], btc_df['close'], color='black', linewidth=2, label='BTC Price (USD)')
    ax2.set_ylabel('BTC Price (USD)', fontsize=17, color='black')
    ax2.tick_params(axis='y', labelcolor='black', labelsize = 17)

    # --- Title, grid ---
    fig.suptitle(f'Longs vs BTC Price — Last {num_days} Days', fontsize=22)
    ax1.grid(alpha=0.3)

    # --- Combine legends ---
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=14)

    fig.tight_layout()
    plt.savefig('bitfinex_longs.png')

if __name__ == "__main__":
    longs()
    send_telegram_photo('bitfinex_longs.png',"Bitfinex Longs vs BTC Chart")