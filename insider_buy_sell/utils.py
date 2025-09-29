from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import pandas as pd
import requests
import os

load_dotenv()

# === CONFIGURATION ===
GOOGLE_SHEET_NAME = "Stock_Watchlist"
GOOGLE_CREDENTIALS_FILE = "your-service-account.json"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


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
    

def insider_analysis(url):
    # Read all tables
    tables = pd.read_html(url)

    # Find the table with 'Ticker' column
    insider_df = None
    for table in tables:
        cols = [str(c).strip() for c in table.columns]
        if any("Ticker" in c for c in cols):
            insider_df = table.copy()
            insider_df.columns = cols  # clean column names
            break

    if insider_df is not None:
        # Inspect columns
        print("Columns found:", insider_df.columns.tolist())

        # Try to detect the correct columns
        filing_col = next((c for c in insider_df.columns if "Filing" in c), None)
        trade_col = next((c for c in insider_df.columns if "Trade" in c), None)
        ticker_col = next((c for c in insider_df.columns if "Ticker" in c), None)
        qty_col = next((c for c in insider_df.columns if "Qty" in c), None)

        # Convert dates
        if filing_col:
            insider_df[filing_col] = pd.to_datetime(insider_df[filing_col], errors="coerce")
        if trade_col:
            insider_df[trade_col] = pd.to_datetime(insider_df[trade_col], errors="coerce")

        # Clean Qty column
        if qty_col:
            insider_df[qty_col] = insider_df[qty_col].replace('[\$,]', '', regex=True).astype(float)
            insider_df = insider_df[['Filing\xa0Date','Filing\xa0Date','Ticker','Insider\xa0Name','Title','Trade\xa0Type','Price','Qty','ΔOwn']]

        print(insider_df.head())
        return insider_df
    else:
        print("No insider trade table found.")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    chat_id = TELEGRAM_CHAT_ID

    if "_" in chat_id:
        ids = chat_id.split("_")
        payload = {
            "chat_id": ids[0],
            "message_thread_id" : ids[1],
            "text" : text,
            "parse_mode" : "Markdown"
        }
    
    else:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

    requests.post(url, json=payload)