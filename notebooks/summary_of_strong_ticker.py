import os
import requests
from utils import * 

tickers_list=pull_large_cap_dataset()
print(tickers_list)

'''
INPUT_CSV  = '../src/data-pipline/large_cap_financials.csv'
OUTPUT_CSV = '../src/data-pipline/large_cap_financials_with_interest_expense.csv'
tickers   = pd.read_csv(INPUT_CSV)["Ticker"].tolist()
df=pd.read_csv(INPUT_CSV)
strong_df = filter_strong_tickers(df)
strong_df.to_csv("../src/data-pipline/summary_strong_large_cap.csv", index=False)
df_filtered = filter_strong_tickers(df)  # filter by your rulesppython

# Step 3 – Count & Compare
summary_table = summarize_filters(df)
print(summary_table)
'''