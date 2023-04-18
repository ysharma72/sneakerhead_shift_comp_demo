import pandas as pd
import plotly.express as px
import pandas_ta as ta
import numpy as np
from tqdm import tqdm
import os

# Read in the data
data = {}
ignore_files = ["README.md"]
# Get all files in directory (make sure your relative root is the project repository)
for filename in os.scandir("RAW_DATA"):
    if filename.is_file() and filename.name not in ignore_files:
        df = pd.read_csv("RAW_DATA/" + filename.name, index_col=0, parse_dates=True, header=[0,1])
        name = filename.name.split(".")[0]
        data[name] = df


# df_2018_12_17 = pd.read_csv('RAW_DATA/2018_12_17.csv', index_col=0, header=[0, 1])
# df_2018_12_21 = pd.read_csv('RAW_DATA/2018_12_21.csv', index_col=0, header=[0, 1])
# df_2020_06_12 = pd.read_csv('RAW_DATA/2020_06_12.csv', index_col=0, header=[0, 1])
# df_2020_06_19 = pd.read_csv('RAW_DATA/2020_06_19.csv', index_col=0, header=[0, 1])
# df_2020_06_26 = pd.read_csv('RAW_DATA/2020_06_26.csv', index_col=0, header=[0, 1])
# df_2020_10_30 = pd.read_csv('RAW_DATA/2020_10_30.csv', index_col=0, header=[0, 1])

# # dictionary of all data
# data = {
#     '2018_12_17': df_2018_12_17,
#     '2018_12_21': df_2018_12_21,
#     '2020_06_12': df_2020_06_12,
#     '2020_06_19': df_2020_06_19,
#     '2020_06_26': df_2020_06_26,
#     '2020_10_30': df_2020_10_30
# }

# print(data.keys())

for k in data.keys():
    # Convert index of each dataframe to datetime
    data[k].index = pd.to_datetime(data[k].index)


# 2018-12-17 is secondly vs 5 second data so.... 
# data['2018_12_17'] = data["2018_12_17"].resample('5S').mean()


def VWAP(bid_price, ask_price, bid_vol, ask_vol, multiplier):
    bid_vwap = np.dot(bid_price, bid_vol) / sum(bid_vol)
    ask_vwap = np.dot(ask_price, ask_vol) / sum(ask_vol)
    vwap = (bid_vwap + ask_vwap) / 2
    std = np.sqrt((np.dot(bid_vol, (bid_price - vwap) ** 2) + np.dot(ask_vol, (ask_price - vwap) ** 2)) / (sum(bid_vol) + sum(ask_vol)))
    return [vwap - (multiplier * std), vwap, vwap + (multiplier * std)] #Returns a list of vwap, 2 standard deviations above and below the vwap


for k in tqdm(data.keys()):

    for ticker in tqdm(data[k].columns.levels[0]):
        # if ticker not in ["AAPL", "JPM", "BA", "CVX"]: continue
        # data[k][ticker].drop(columns=['BID TIME', 'ASK TIME'], inplace=True)
        # Create new column for mid price
        data[k][ticker, 'MID PRICE'] = (data[k][ticker, 'BID PRICE'] + data[k][ticker, 'ASK PRICE']) / 2
        data[k][ticker, 'RETURNS'] = data[k][ticker, 'MID PRICE'].pct_change()
        # Create new column for RSI
        data[k][ticker, 'RSI'] = ta.rsi(data[k][ticker, 'MID PRICE'], length=10)
        # Create new columns for MA(9) and MA(21)
        data[k][ticker, 'MA(9)'] = ta.sma(data[k][ticker, 'MID PRICE'], length=9)
        data[k][ticker, 'MA(21)'] = ta.sma(data[k][ticker, 'MID PRICE'], length=21)

        # Initialize VWAP column
        data[k][ticker, "VWAP_LOWER"], data[k][ticker, "VWAP"], data[k][ticker, "VWAP_UPPER"], data[k][ticker, "VWAP_LOWER2"], data[k][ticker, "VWAP_UPPER2"] = np.nan, np.nan, np.nan, np.nan, np.nan
        for i in tqdm(range(len(data[k][ticker]))):
            if i < 1: continue
            # Create new columns for VWAP (1 standard deviation)
            data[k][ticker, "VWAP_LOWER"][i], data[k][ticker, "VWAP"][i], data[k][ticker, "VWAP_UPPER"][i] = VWAP(data[k][ticker, "BID PRICE"][:i], data[k][ticker, "ASK PRICE"][:i], data[k][ticker, "BID VOLUME"][:i], data[k][ticker, "ASK VOLUME"][:i], 1)
            # VWAP for 0.2 std
            data[k][ticker, "VWAP_LOWER2"][i], _, data[k][ticker, "VWAP_UPPER2"][i] = VWAP(data[k][ticker, "BID PRICE"][:i], data[k][ticker, "ASK PRICE"][:i], data[k][ticker, "BID VOLUME"][:i], data[k][ticker, "ASK VOLUME"][:i], 0.2)
    
        # Create new columns for ATR
        #TODO

    # df.dropna(inplace=True)
    
    # Save the data to a csv
    data[k].sort_index(axis=1, inplace=True)
    data[k].to_csv(f'CLEAN_DATA/{k}.csv')