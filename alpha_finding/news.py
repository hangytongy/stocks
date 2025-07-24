import requests
import time
from datetime import datetime
import pytz
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIGURATION ===
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GOOGLE_SHEET_NAME = "Stock_Watchlist"  # Name of your Google Sheet
GOOGLE_CREDENTIALS_FILE = "your-service-account.json"  # Path to your downloaded JSON key
CHECK_INTERVAL = 60  # seconds
TIMEZONE = pytz.timezone("US/Eastern")  # Change if needed

# === CACHED TIMESTAMPS TO AVOID DUPLICATES ===
latest_timestamps = {}

# === Load stock symbols from Google Sheet ===
def get_symbols_from_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1  # assumes first sheet
    symbols = sheet.col_values(1)[1:]
    return [s.strip().upper() for s in symbols if s.strip()]

# === Fetch latest news from Finnhub ===
def get_latest_news(symbol):
    today = datetime.now().strftime('%Y-%m-%d')
    url = f'https://finnhub.io/api/v1/company-news?symbol={symbol}&from={today}&to={today}&token={FINNHUB_API_KEY}'
    response = requests.get(url)
    return response.json()

# === Send Telegram message ===
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# === Format news article ===
def format_article(article, symbol):
    dt = datetime.fromtimestamp(article['datetime'], tz=TIMEZONE).strftime('%Y-%m-%d %H:%M')
    return f"*{symbol}* - *{article['headline']}*\n{dt}\n[Read more]({article['url']})"

# === Main monitoring loop ===
def main():
    global latest_timestamps
    print("🔍 Real-time multi-stock news watcher started...")
    while True:
        try:
            symbols = get_symbols_from_google_sheet()
            for symbol in symbols:
                if symbol not in latest_timestamps:
                    latest_timestamps[symbol] = 0

                news_items = get_latest_news(symbol)
                if news_items:
                    latest_article = max(news_items, key=lambda x: x['datetime'])
                    article_time = latest_article.get("datetime", 0)
                    if article_time > latest_timestamps[symbol]:
                        message = format_article(latest_article, symbol)
                        send_telegram_message(message)
                        latest_timestamps[symbol] = article_time

        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

