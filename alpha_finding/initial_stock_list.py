import pandas as pd
import yfinance as yf
from tqdm import tqdm

no_of_tickers = 15

def get_initial_stock_list(no_of_tickers = no_of_tickers):

    # Step 1: Load NASDAQ-listed companies
    url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    df = pd.read_csv(url, sep="|")

    # Clean the data
    df = df[df['Symbol'] != 'File Creation Time:']
    df = df[df['Test Issue'] == 'N']

    # Step 2: Sample 500 random tickers
    sample = df.sample(n=no_of_tickers, random_state=42)[['Symbol', 'Security Name']].reset_index(drop=True)

    # Step 3: Get market cap using yfinance
    market_caps = []

    print(f"Fetching market cap for {no_of_tickers} tickers...")
    for _, row in tqdm(sample.iterrows(), total=no_of_tickers):
        symbol = row['Symbol']
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            market_cap = info.get('marketCap')
            market_caps.append(market_cap)
        except:
            market_caps.append(None)

    # Add market cap to the dataframe
    sample['MarketCap'] = market_caps.fillna(0)   

    # Step 4: Display or save
    print(sample.head())

    # Optional: Save to CSV
    sample.to_csv(f"initial_stock_list_{no_of_tickers}.csv", index=False)

    return sample