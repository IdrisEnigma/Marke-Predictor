import os, time
from tqdm import tqdm
import pandas as pd
import yfinance as yf
from fastapi import FastAPI
import numpy as np  

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm 
import warnings

# Ignore FutureWarnings
#warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
    
# FastAPI app
app = FastAPI()

# Paths
SAVE_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "src", "data-pipline", "all_SP500_cap_financials_extendS.csv"
)
SP500_SOURCE = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "src", "data-pipline", "all_SP500_cap_financials10.csv"
)

# Ensure folder exists
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

MAX_WORKERS = 10 

# Load tickers from CSV
def load_sp500_tickers():
    if not os.path.exists(SP500_SOURCE):
        raise FileNotFoundError(f"Ticker CSV not found: {SP500_SOURCE}")
    df = pd.read_csv(SP500_SOURCE)
    if 'Ticker' not in df.columns:
        raise ValueError(f"'Ticker' column not found in CSV: {SP500_SOURCE}")
    return df['Ticker'].tolist()

# Check if ticker is valid
def is_valid_ticker(ticker):
    try:
        info = yf.Ticker(ticker).info
        # Example filter: only tickers with marketCap
        return info.get("marketCap") is not None
    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")
        return False

# Fetch financial metrics
import time

def get_interest_expense_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch full income statement (pandas DataFrame)
        income_stmt = stock.financials  # or stock.income_stmt

        # Try multiple possible row names
        for row_name in ["Interest Expense", "InterestExpense", "InterestExpenseNonOperating"]:
            if row_name in income_stmt.index:
                #print(income_stmt.loc[row_name].iloc[0])
                return income_stmt.loc[row_name].iloc[0]

        return None
    except Exception as e:
        #print(f"[ERROR] {ticker}: {e}")
        return None



import yfinance as yf
import numpy as np

def safe(x):
    try:
        return float(x)
    except:
        return None

def get_eps_estimates(ticker):
    """Safest method in 2025 to fetch EPS estimates from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.get_analysis()
        if df is None or df.empty:
            return None, None, None

        eps_row = df.loc["Earnings Estimate"]

        return (
            eps_row.get("2023"),
            eps_row.get("2024"),
            eps_row.get("2025"),
        )
    except:
        return None, None, None


def fetch_metrics(ticker):
    """Fetch all required metrics including balance sheet, estimates, PEG, growth, etc."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return None

        # =======================================================
        # INTEREST EXPENSE – your custom function
        # =======================================================
        interest_expense = get_interest_expense_yahoo(ticker)

        # =======================================================
        # ANNUAL + QUARTERLY FINANCIALS
        # =======================================================
        annual = stock.financials.T
        quarterly = stock.quarterly_financials.T

        current_annual = info.get("totalRevenue")
        prior_year_annual = safe(annual["Total Revenue"].iloc[-2]) if "Total Revenue" in annual and len(annual) >= 2 else None
        three_years_ago_annual = safe(annual["Total Revenue"].iloc[-3]) if "Total Revenue" in annual and len(annual) >= 3 else None

        current_year_q3 = safe(quarterly["Total Revenue"].iloc[-1]) if "Total Revenue" in quarterly and len(quarterly) >= 5 else None
        prior_year_q3 = safe(quarterly["Total Revenue"].iloc[-5]) if "Total Revenue" in quarterly and len(quarterly) >= 5 else None

        qoQ_change = (quarterly["Total Revenue"].iloc[-1] / quarterly["Total Revenue"].iloc[-2] - 1) \
            if "Total Revenue" in quarterly and len(quarterly) >= 2 else None

        historical_cagr_3yr = (current_annual / three_years_ago_annual) ** (1/3) - 1 \
            if current_annual and three_years_ago_annual else None

        # =======================================================
        # ANALYST ESTIMATES
        # =======================================================
        est_2023, est_2024, est_2025 = get_eps_estimates(ticker)

        # =======================================================
        # PEG RATIOS
        # =======================================================
        fwd_pe = info.get("forwardPE")
        trailing_pe = info.get("trailingPE")
        current_eps = info.get("epsTrailingTwelveMonths")

        peg_12 = peg_24 = current_peg = industry_peg = None
        if fwd_pe and current_eps:
            if est_2024:
                g12 = est_2024 / current_eps - 1
                peg_12 = fwd_pe / g12 if g12 else None
            if est_2025:
                g24 = est_2025 / current_eps - 1
                peg_24 = fwd_pe / g24 if g24 else None

        current_peg = (trailing_pe / g12) if trailing_pe and g12 else None
        # industry_peg could be fetched from external source if needed

        # =======================================================
        # BALANCE SHEET METRICS
        # =======================================================
        bs = stock.balance_sheet
        if bs is not None and not bs.empty:
            bs = bs.T  # transpose
            cash = safe(bs.get("Cash And Cash Equivalents", [None])[-1])
            current_assets = safe(bs.get("Total Current Assets", [None])[-1])
            current_liabilities = safe(bs.get("Total Current Liabilities", [None])[-1])
            total_assets = safe(bs.get("Total Assets", [None])[-1])
            total_liabilities = safe(bs.get("Total Liab", [None])[-1])
            equity = safe(bs.get("Total Stockholder Equity", [None])[-1])
            assets_non_current = total_assets - current_assets if total_assets and current_assets else None
            liab_non_current = total_liabilities - current_liabilities if total_liabilities and current_liabilities else None
        else:
            cash = current_assets = current_liabilities = assets_non_current = liab_non_current = equity = None

        current_ratio = current_assets / current_liabilities if current_assets and current_liabilities else None
        debt_equity_ratio = total_liabilities / equity if total_liabilities and equity else None
        roe_py = None
        if equity and prior_year_annual:
            roe_py = prior_year_annual / equity  # rough approximation

        # =======================================================
        # GROWTH
        # =======================================================
        growth_2023 = (prior_year_annual / three_years_ago_annual - 1) if prior_year_annual and three_years_ago_annual else None
        growth_2024 = (current_annual / prior_year_annual - 1) if current_annual and prior_year_annual else None
        growth_2025 = (est_2025 / est_2024 - 1) if est_2025 and est_2024 else None

        # =======================================================
        # FINAL RETURN
        # =======================================================
        return {
            "Ticker": ticker,
            # Revenue
            "Current": current_annual,
            "Prior_Year": prior_year_annual,
            "3_Years_Ago": three_years_ago_annual,
            "Prior_Year_Q3": prior_year_q3,
            "Current_Year_Q3": current_year_q3,
            # Growth
            "QoQ_Change": qoQ_change,
            "Historical_CAGR_3YR": historical_cagr_3yr,
            "Growth_2023": growth_2023,
            "Growth_2024": growth_2024,
            "Growth_2025": growth_2025,
            # Estimates
            "Estimate_2023": est_2023,
            "Estimate_2024": est_2024,
            "Estimate_2025": est_2025,
            # PEG
            "Forward_PEG_12M": peg_12,
            "Forward_PEG_24M": peg_24,
            "Current_PEG": current_peg,
            "Industry_PEG": industry_peg,
            "ROE_PY": roe_py,
            # Balance sheet
            "Cash_Equivalents": cash,
            "Current_Assets": current_assets,
            "Current_Liabilities": current_liabilities,
            "Non_Current_Assets": assets_non_current,
            "Non_Current_Liabilities": liab_non_current,
            "Equity": equity,
            "Current_Ratio": current_ratio,
            "Debt_Equity_Ratio": debt_equity_ratio,
            # Other financials
            "Operating_Margin": info.get("operatingMargins"),
            "Net_Margin": info.get("profitMargins"),
            "ROE": info.get("returnOnEquity"),
            "Total_Debt": info.get("totalDebt"),
            "Total_Cash": info.get("totalCash"),
            "EBITDA": info.get("ebitda"),
            # Custom
            "Interest_Expense": interest_expense,
        }

    except Exception as e:
        return None  # silently fail, no print


def fetch_metrics_with_retry(ticker, retries=3, delay=1):
    for i in range(retries):
        try:
            return fetch_metrics(ticker)
        except Exception as e:
            print(f"[WARN] {ticker} failed, retry {i+1}/{retries}")
            time.sleep(delay)
    print(f"[ERROR] {ticker} failed after {retries} retries")
    return None

from fastapi.responses import JSONResponse

@app.get("/pull_large_cap_dataset")
def pull_large_cap_dataset(save_path: str = SAVE_PATH, max_workers: int = MAX_WORKERS, test: bool = True):
    try:       
        # Ensure folder exists
        folder = os.path.dirname(save_path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        # Step 1 — Load tickers
        tickers = load_sp500_tickers()
        # Step 1a — Take only first 20 for testing
        if test:
            tickers = tickers[:100]#len(tickers)]

        #print(f"[INFO] Testing with {len(tickers)} tickers...")

        # Step 2 — Validate tickers
        valid_tickers = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(is_valid_ticker, t): t for t in tickers}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Validating tickers"):
                ticker = futures[future]
                try:
                    if future.result():
                        valid_tickers.append(ticker)
                except Exception as e:
                    print(f"[ERROR] {ticker}: {e}")

        print(f"[INFO] {len(valid_tickers)} valid tickers found")

        # Step 3 — Fetch financial metrics
        records = []
        for ticker in tqdm(valid_tickers, desc="Fetching metrics"):
            for attempt in range(3):
                try:
                    record = fetch_metrics(ticker)
                    if record:
                        records.append(record)
                    break
                except Exception as e:
                    print(f"[WARN] {ticker} failed attempt {attempt+1}: {e}")
                    time.sleep(1)  # avoid rate limit

        # Step 4 — Save CSV
        df = pd.DataFrame(records)
        df.to_csv(save_path, index=False)
        print(f"[SUCCESS] Dataset saved to: {save_path}")

        return {"status": "success", "total_records": len(records)}

    except Exception as e:
        return {"status": "error", "message": str(e)}
