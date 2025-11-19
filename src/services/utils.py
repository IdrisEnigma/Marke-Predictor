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
def pull_large_cap_dataset():
    """
    Pulls the large cap dataset from a CSV file.
    """
    INPUT_CSV  = '../src/data-pipline/large_cap_financials.csv'
    df = pd.read_csv(INPUT_CSV)
    print(f"[INFO] Pulled dataset with {len(df)} tickers")
    return df
#----------------------------------------------------------

