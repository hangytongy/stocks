import requests
import time
from datetime import datetime, timedelta
import pytz
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURATION ===
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GOOGLE_SHEET_NAME = "Stock_Watchlist"
GOOGLE_CREDENTIALS_FILE = "your-service-account.json"
CHECK_INTERVAL = 120  # seconds
TIMEZONE = pytz.timezone("Asia/Singapore")

# === CACHED TIMESTAMPS TO AVOID DUPLICATES ===
latest_timestamps = {}

# === Load stock symbols from Google Sheet ===
def get_symbols_from_google_sheet():
    """
    Authenticates with Google Sheets using a service account and
    fetches stock symbols from the first column of the specified sheet.
    """
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        symbols = sheet.col_values(1)[1:] # Skip header row
        return [s.strip().upper() for s in symbols if s.strip()]
    except Exception as e:
        print(f"Error loading symbols from Google Sheet: {e}")
        return []

# === Fetch market cap from Finnhub ===
def get_market_cap(symbol):
    url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data.get("marketCapitalization", 0) * 1e6  # Convert to absolute USD

# === Fetch latest news from Finnhub ===
def get_latest_news_finnhub(symbol):
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = f'https://finnhub.io/api/v1/company-news?symbol={symbol}&from={yesterday}&to={today}&token={FINNHUB_API_KEY}'
    response = requests.get(url)
    return response.json()

# === Fetch latest news from alternative API for small caps ===
def get_latest_news_alt(symbol):
    url = f'https://v2.datalake.sysautomon.xyz/api/search?pageSize=25&symbol={symbol}&sort=date_desc'
    response = requests.get(url)
    data = response.json()
    return  data['data'].get('newsFeed',[])

# === Send Telegram message ===
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# === Format article from Finnhub ===
def format_finnhub_article(article, symbol):
    dt = datetime.fromtimestamp(article['datetime'], tz=TIMEZONE).strftime('%Y-%m-%d %H:%M')
    return f"*${symbol}* \n\n*{article['headline']}*\n{dt}\n[Read more]({article['url']})"

# === Format article from alternative API ===
def format_alt_article(article, symbol):
    dt = datetime.fromtimestamp(article['publication_date'] / 1000, tz=TIMEZONE).strftime('%Y-%m-%d %H:%M')
    headline = article.get("headline", "No Title")
    news = article.get("news", "No News")
    return f"*${symbol}* \n\n*{headline}*\n\n{news}\n\n{dt}\n[Read more](https://app.microcapresearch.com/news-feed?sortType=date&sortOrder=desc&symbol={symbol}&open=true)"

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

                market_cap = get_market_cap(symbol)
                print(f"{symbol} Market Cap: ${market_cap:,.0f}")

                if market_cap < 2_000_000_000:  # Use alternative API
                    news_items = get_latest_news_alt(symbol)
                    if news_items:
                        latest_article = news_items[0]
                        article_time = latest_article['publication_date']//1000
                        if article_time > latest_timestamps[symbol]:
                            message = format_alt_article(latest_article, symbol)
                            send_telegram_message(message)
                            latest_timestamps[symbol] = article_time
                else:  # Use Finnhub
                    news_items = get_latest_news_finnhub(symbol)
                    if news_items:
                        latest_article = max(news_items, key=lambda x: x['datetime'])
                        article_time = latest_article.get("datetime", 0)
                        if article_time > latest_timestamps[symbol]:
                            message = format_finnhub_article(latest_article, symbol)
                            send_telegram_message(message)
                            latest_timestamps[symbol] = article_time

        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

