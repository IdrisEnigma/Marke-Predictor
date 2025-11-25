import os
import requests
import pandas as pd
SP500_SOURCE = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SAVE_PATH = "data/large_cap_dataset.csv"
MAX_WORKERS=10
#----------------------------------------------------------
def preprocess_ticker(ticker):
    """Fix tickers with dots (BRK.B → BRK-B)."""
    return ticker.replace(".", "-").strip()

def is_valid_ticker(ticker):
    """Check if ticker exists in Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        return not data.empty
    except:
        return False

def load_sp500_tickers(source=SP500_SOURCE):
    """Load tickers from CSV and preprocess them."""
    df = pd.read_csv(source)
    tickers = df["Ticker"].apply(preprocess_ticker).tolist()
    print(f"[INFO] Loaded {len(tickers)} S&P 500 tickers")
    return tickers

def get_interest_expense_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch full income statement (pandas DataFrame)
        income_stmt = stock.financials  # or stock.income_stmt

        # Try multiple possible row names
        for row_name in ["Interest Expense", "InterestExpense", "InterestExpenseNonOperating"]:
            if row_name in income_stmt.index:
                print(income_stmt.loc[row_name].iloc[0])
                return income_stmt.loc[row_name].iloc[0]

        return None
    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")
        return None

def fetch_metrics(ticker):
    """Fetch financial metrics for a ticker, using Yahoo Finance for Interest Expense."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.get_info()
        if not info:
            return None

        # Replace interestExpense with your custom function
        interest_expense = get_interest_expense_yahoo(ticker)

        return {
            "Ticker": ticker,
            "Revenue": info.get("totalRevenue"),
            "Operating_Margin": info.get("operatingMargins"),
            "Net_Margin": info.get("profitMargins"),
            "ROE": info.get("returnOnEquity"),
            "Total_Debt": info.get("totalDebt"),
            "Total_Cash": info.get("totalCash"),
            "EBITDA": info.get("ebitda"),
            "Interest_Expense": interest_expense,  # <-- fully replaced
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch {ticker}: {e}")
        return None


# -----------------------------
# Main Pipeline
# -----------------------------

def pull_large_cap_dataset(save_path=SAVE_PATH, max_workers=MAX_WORKERS):
    # Step 1 — Load tickers
    tickers = load_sp500_tickers()

    # Step 2 — Filter valid tickers using multithreading
    print("[INFO] Checking valid tickers...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda t: t if is_valid_ticker(t) else None, tickers))
    valid_tickers = [t for t in results if t]
    print(f"[INFO] {len(valid_tickers)} valid tickers found")

    # Step 3 — Fetch financial metrics for valid tickers (sequentially or threaded if needed)
    print("[INFO] Fetching financial metrics...")
    records = []
    for ticker in valid_tickers:
        record = fetch_metrics(ticker)
        if record:
            records.append(record)

    # Step 4 — Save to CSV
    df = pd.DataFrame(records)
    df.to_csv(save_path, index=False)
    print(f"[SUCCESS] Dataset saved to: {save_path}")
    return df
#----------------------------------------------------------
def filter_strong_tickers(df):
    """
    Filters tickers based on fundamental criteria:
    1. Operating Margin ≥ 0
    2. ROE ≥ 12%
    3. Net Debt / EBITDA ≤ 3
    4. Interest Coverage ≥ 4
    """
    # Ensure numeric columns are filled; replace None/NaN with 0 for calculation
    df = df.copy()
    df["Operating_Margin"] = pd.to_numeric(df["Operating_Margin"], errors="coerce")
    df["ROE"] = pd.to_numeric(df["ROE"], errors="coerce")
    df["Total_Debt"] = pd.to_numeric(df["Total_Debt"], errors="coerce")
    df["Total_Cash"] = pd.to_numeric(df["Total_Cash"], errors="coerce")
    df["EBITDA"] = pd.to_numeric(df["EBITDA"], errors="coerce")
    df["Interest_Expense"] = pd.to_numeric(df["Interest_Expense"], errors="coerce")

    # Calculate Net Debt
    df["Net_Debt"] = df["Total_Debt"] - df["Total_Cash"]

    # Calculate Net Debt / EBITDA
    df["Net_Debt_to_EBITDA"] = df["Net_Debt"] / df["EBITDA"]

    # Calculate Interest Coverage = EBITDA / Interest Expense
    df["Interest_Coverage"] = df["EBITDA"] / df["Interest_Expense"]

    # Apply filters
    filtered_df = df[
        (df["Operating_Margin"] >= 0) &
        (df["ROE"] >= 0.12) &
        (df["Net_Debt_to_EBITDA"] <= 3) &
        (df["Interest_Coverage"] >= 4)
    ].copy()

    print(f"[INFO] {len(filtered_df)} tickers passed the filter criteria")
    return filtered_df
#----------------------------------------------------------
def summarize_filters(df):
    df = df.copy()
    
    # Create necessary columns if missing
    if "Net_Debt_to_EBITDA" not in df.columns:
        df["Net_Debt"] = df["Total_Debt"] - df["Total_Cash"]
        df["Net_Debt_to_EBITDA"] = df["Net_Debt"] / df["EBITDA"]
    if "Interest_Coverage" not in df.columns:
        df["Interest_Coverage"] = df["EBITDA"] / df["Interest_Expense"]
    
    total_companies = len(df)
    
    mask_margin = df["Operating_Margin"] >= 0
    mask_roe = df["ROE"] >= 0.12
    mask_leverage = df["Net_Debt_to_EBITDA"] <= 3
    mask_interest = df["Interest_Coverage"] >= 4
    
    passed_all = df[mask_margin & mask_roe & mask_leverage & mask_interest]
    
    summary = {
        "Metric": [
            "Total Companies",
            "Passed All Filters",
            "Failed Operating Margin",
            "Failed ROE",
            "Failed Leverage (Net Debt/EBITDA)",
            "Failed Interest Coverage"
        ],
        "Count": [
            total_companies,
            len(passed_all),
            len(df[~mask_margin]),
            len(df[~mask_roe]),
            len(df[~mask_leverage]),
            len(df[~mask_interest])
        ]
    }
    
    summary["% of Total"] = [f"{(c/total_companies*100):.1f}%" for c in summary["Count"]]
    return pd.DataFrame(summary)
#----------------------------------------------------------


