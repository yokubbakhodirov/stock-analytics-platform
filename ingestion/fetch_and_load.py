import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load database URL from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found. "
        "Create a .env file with your Supabase connection string. "
        "See README.md for setup instructions."
    )

# Connect to Supabase
engine = create_engine(DATABASE_URL)

# List of tickers to fetch — matches exactly what we inserted in companies table
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'JNJ', 'PFE', 'JPM', 'BAC', 'XOM', 'CVX', 'AMZN']

def fetch_and_load():
    print("Starting data fetch...")
    
    for ticker in TICKERS:
        print(f"Fetching {ticker}...")
        
        # Fetch last 1 year of daily price data
        stock = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
        
        if stock.empty:
            print(f"No data for {ticker}, skipping.")
            continue
        
        # Clean up the dataframe
        stock = stock.reset_index()
        stock.columns = ['date', 'close', 'high', 'low', 'open', 'volume']
        stock['ticker'] = ticker
        stock = stock[['ticker', 'date', 'open', 'close', 'high', 'low', 'volume']]
        
        # Load into Supabase — skip duplicates
        stock.to_sql(
            'stock_prices',
            engine,
            if_exists='append',
            index=False,
            method='multi'
        )
        
        print(f"{ticker} loaded — {len(stock)} rows")
    
    print("All done!")

if __name__ == "__main__":
    fetch_and_load()