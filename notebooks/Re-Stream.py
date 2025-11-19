from utils import * 
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor


SP500_SOURCE = "../src/data-pipline/sp500_tickers.csv"# Input CSV with column "Symbol"
SAVE_PATH =    "../src/data-pipline/large_cap_financials.csv"
MAX_WORKERS = 10 
pull_large_cap_dataset()
