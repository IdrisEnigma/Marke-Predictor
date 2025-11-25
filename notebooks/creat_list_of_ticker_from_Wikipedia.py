import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
MAX_WORKERS = 10 
import requests

import pandas as pd
import requests
import pandas as pd
import requests
from io import StringIO

def get_sp500_from_wikipedia():
    """
    Fetch the S&P 500 tickers from Wikipedia with headers to avoid 403.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/142.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Use StringIO to wrap the HTML content
        html_data = StringIO(response.text)
        tables = pd.read_html(html_data)

        # Find the table that contains 'Symbol' column
        df = None
        for table in tables:
            if 'Symbol' in table.columns:
                df = table
                break

        if df is None:
            print("[ERROR] Could not find table with 'Symbol' column")
            return []

        tickers = df['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]  # normalize
        print(f"[INFO] Loaded {len(tickers)} S&P 500 tickers from Wikipedia")
        return tickers

    except Exception as e:
        print(f"[ERROR] Failed to fetch tickers: {e}")
        return []

# Usage
tickers = get_sp500_from_wikipedia()
print(tickers[:20])




'''

def get_sp500_from_nasdaq_web():
    url = "https://www.nasdaq.com/market-activity/index/spx"
    tables = pd.read_html(url)

    # The first table usually contains the components
    df = tables[0]

    # Nasdaq uses 'Symbol' column
    tickers = df["Symbol"].tolist()

    print(f"[INFO] Loaded {len(tickers)} S&P 500 tickers from Nasdaq website")
    return tickers
yahoo_tickers=get_sp500_from_yahoo()
#nasdaq=get_sp500_from_nasdaq_web()
'''
