import pandas as pd
import ta
import numpy as np
import yfinance as yf # Import yfinance
import time
import datetime


def get_stock_data_yfinance(tickers, period, interval):
    """
    Downloads historical stock data for multiple tickers using yfinance.
    Returns a dictionary where keys are tickers and values are pandas DataFrames.
    """
    all_stock_data = {}
    failed_downloads = []

    print("--- Starting Data Download (yfinance) ---")
    # yfinance can download multiple tickers at once, which is often more efficient.
    # The result is a MultiIndex DataFrame where the top level is OHLCV and second level is ticker.
    # We will then unstack it or process it to get individual DataFrames.
    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            interval=interval,
            group_by='ticker', # Group columns by ticker (e.g., ('AAPL', 'Close'))
            auto_adjust=True, # Automatically adjust for splits and dividends
            progress=True, # Show download progress
            # Add this if you faced multi-level index issues in the past, though 'group_by' handles it well
            # multi_level_index=False
        )

        # Check if data is empty or if all downloads failed
        if data.empty:
            print("No data downloaded. Check tickers and period/interval.")
            return {}

        # yfinance.download with group_by='ticker' returns a DataFrame with MultiIndex columns:
        # (Ticker, OHLCV), (Ticker, OHLCV), etc.
        # We need to extract individual DataFrames for each ticker.
        for ticker in tickers:
            # Check if the ticker exists in the downloaded data
            if (ticker, 'Close') in data.columns:
                df = data[ticker].copy() # Get data for a single ticker
                # yfinance automatically sets DatetimeIndex and proper column names
                # It often includes 'Adj Close', which is usually preferred.
                # Let's standardize column names for consistency with your previous code
                df.columns = [col.replace(' ', '_') for col in df.columns] # Replace spaces if any
                df.rename(columns={'Adj_Close': 'Close'}, inplace=True) # Use Adj_Close as 'Close'
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']] # Select desired columns

                # Ensure enough data points for indicator calculations
                if len(df) < 15:
                    print(f"Not enough data points ({len(df)}) for {ticker}. Skipping for analysis.")
                    failed_downloads.append(ticker)
                    continue

                all_stock_data[ticker] = df
                print(f"Successfully prepared data for {ticker}.")
            else:
                print(f"No data found for {ticker} (might have failed download or invalid ticker).")
                failed_downloads.append(ticker)

    except Exception as e:
        print(f"An error occurred during yfinance bulk download: {e}")
        print("This might be due to network issues, invalid tickers, or temporary Yahoo Finance service problems.")
        # In a bulk download, it's harder to pinpoint individual failures for rate limits
        # yfinance internally handles some retry logic.
        pass # Allow script to continue even if bulk download fails for some reason

    print("\n--- Data Download Complete (yfinance) ---")
    if failed_downloads:
        print(f"Failed to download/process data for: {', '.join(failed_downloads)}")
    print(f"Successfully downloaded data for {len(all_stock_data)} out of {len(tickers)} tickers.")

    return all_stock_data


def process_stocks(all_stock_data):
    """
    Processes the downloaded stock data to calculate indicators and apply screening conditions.
    """
    results = []
    processed_tickers_count = 0

    print("\n--- Starting Data Processing and Screening ---")
    for ticker, df in all_stock_data.items():
        try:
            processed_tickers_count += 1
            print(f"Processing {ticker} ({processed_tickers_count}/{len(all_stock_data)})...")

            # Ensure 'Close' column is numeric
            df['Close'] = pd.to_numeric(df['Close'])

            # Indicators
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['ROC_5'] = df['Close'].pct_change(5)
            df['RSI_3'] = ta.momentum.RSIIndicator(df['Close'], window=3).rsi()

            # Check for NaN values introduced by indicator calculations
            # For RSI and ROC, early values will be NaN. Ensure enough valid data.
            # We need at least two rows for latest and prev, after NaNs from indicators.
            df_cleaned = df.dropna(subset=['EMA_10', 'ROC_5', 'RSI_3'])
            if len(df_cleaned) < 2:
                print(f"Not enough complete data points after indicator calculation for {ticker}. Skipping.")
                continue

            # Current snapshot - ensure we get the latest non-NaN values from the cleaned DataFrame
            latest = df_cleaned.iloc[-1]
            prev = df_cleaned.iloc[-2]

            # Screener Conditions
            if (
                latest['RSI_3'] > 70
                and latest['Close'] > latest['EMA_10']
                and latest['EMA_10'] > prev['EMA_10']  # EMA trending up
            ):
                results.append({
                    'Ticker': ticker,
                    '5D ROC (%)': round(latest['ROC_5'] * 100, 2),
                    'RSI(3)': round(latest['RSI_3'], 1),
                    'Price vs EMA10': round(latest['Close'] / latest['EMA_10'], 3)
                })

        except Exception as e:
            print(f"Error processing data for {ticker}: {e}")
            # Consider adding ticker to a failed_processing list if desired

    print("\n--- Screening Complete ---")
    return results

def get_confirmed_list(results, total_tickers_considered, top_percentile):
    """
    Filters and ranks the screening results.
    """
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values(by='5D ROC (%)', ascending=False)
        # top 1% of the investible universe after filtering for momentumn by 5D ROC
        # Use total_tickers_considered for percentile calculation
        top_n = max(1, int(total_tickers_considered * top_percentile))
        df_top = df_results.head(top_n).reset_index(drop=True)
    else:
        df_top = pd.DataFrame(columns=['Ticker', '5D ROC (%)', 'RSI(3)', 'Price vs EMA10'])

    return df_top

# === Main Execution ===
def run_momentum_stocks(initial_stock_list):
    # CONFIG (can be moved into main if you want to avoid global vars)
    #TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META', 'GOOGL', 'NFLX', 'SHOP', 'AMD']
    print(f"incoming initial stock list : {initial_stock_list}")
    sample = pd.DataFrame(initial_stock_list)
    sample.rename(columns={"Stock Ticker($)": "Symbol"}, inplace=True)
    TICKERS = sample['Symbol'].tolist()
    PERIOD = '60d' # yfinance period, e.g., '60d', '1y', 'max'
    INTERVAL = '1d' # yfinance interval, e.g., '1d', '1wk', '1mo'
    TOP_PERCENTILE = 0.01

    # 1. Download data
    all_stock_data = get_stock_data_yfinance(TICKERS, PERIOD, INTERVAL)

    # 2. Process data and screen
    momentum_list = process_stocks(all_stock_data)

    # 3. Get confirmed list (top picks)
    # Pass the actual number of tickers for which data was successfully acquired
    top_picks = get_confirmed_list(momentum_list, len(all_stock_data), TOP_PERCENTILE)
    
    print(momentum_list)
    print("---------------------------------------------------")
    print(top_picks)

    return momentum_list

    print("\n--- Script Finished ---")


