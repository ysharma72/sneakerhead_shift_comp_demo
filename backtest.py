import datetime as dt
import pandas as pd
import pandas_ta as ta
import plotly.express as px
import os
import numpy as np

data = {}
ignore_files = ["README.md", "2018_12_17.csv", "2018_12_21.csv", "2020_06_12.csv"]
# Get all files in directory (make sure your relative root is the project repository)
for filename in os.scandir("CLEAN_DATA"):
    if filename.is_file() and filename.name not in ignore_files:
        df = pd.read_csv("CLEAN_DATA/" + filename.name, index_col=0, parse_dates=True, header=[0,1])
        name = filename.name.split(".")[0]
        data[name] = df
print(data.keys())

def interactive_plot(df: pd.DataFrame, title: str):
    """Uses Plotly.Express to chart a line graph of numeric data from each column of a dataframe"""
    fig = px.line(title=title)
    for k in df.columns:
        fig.add_scatter(x=df.index, y=df[k], name=k)
    fig.update_traces(showlegend=True)
    fig.show()

# Om's Code Backtest Version

from tqdm import tqdm

starting_power = 700000
max_alloc = ((starting_power / 4) * 0.95) / 3
max_lots = 18
tickers = ["JPM", "AAPL", "BA", "CVX"]
# strategy variables  
trending_buy, trending_sell = False, False
long_term_buy, long_term_sell = False, False


df = data["2020_10_30"]["JPM"]
df["LTPosition"], df["TRPosition"] = 0, 0

for row in range(len(df)):
    if row > 20 and row < 300:  # Last 90 minutes
        # #For stop loss/target
        # atr = np.mean(df.true_range[-14:].values)
        # swing_high = df.price[-14:].values.max()
        # swing_low = df.price[-14:].values.min()
        
        #Entering longer term trades
        
        if df["RSI"].iloc[row] > 70  and df["LTPosition"].iloc[row-1] > -1:
            print(f'LONG TERM RSI SELL ENTRY : {row}')
            df["LTPosition"].iloc[row] = -1
            long_term_sell = True
            
                            
        elif df["RSI"].iloc[row] < 70 and df["LTPosition"].iloc[row-1] < 1:
            print('LONG TERM RSI BUY ENTRY')
            df['LTPosition'].iloc[row] = 1
            long_term_buy = True

        #Getting out of long term trades
        if long_term_sell and df['RSI'].iloc[row] in range(30, 45) and df["LTPosition"].iloc[row-1] == -1:
            print(f'LONG TERM BUYBACK EXIT : {row}')
            df['LTPosition'].iloc[row] = 0
            
        
        if long_term_buy and df['RSI'].iloc[row] in range(55, 70) and df["LTPosition"].iloc[row-1] == 1:
            print(f'LONG TERM SELL EXIT : {row}')
            df['LTPosition'].iloc[row] = 0
            
        #===========================================================================================================================

        #Entering trending trades
        if df["MA(21)"].iloc[row] > df["MA(9)"].iloc[row] and df["TRPosition"].iloc[row-1] > -1:
            print(f'TRENDING SELL ENTRY : {row}')
            #Price is very far above VWAP but moving averages cross down, sell
            df["TRPosition"].iloc[row] = -1
            trending_sell = True
            

        elif df['MA(21)'].iloc[row] < df['MA(9)'].iloc[row] and df['TRPosition'].iloc[row-1] < 1: #Price is very far below VWAP but moving averages cross up, buy
            print(f'TRENDING BUY ENTRY : {row}')
            df['TRPosition'].iloc[row] = 1
            trending_buy = True

        
        # Getting out of trending trades
        if trending_sell and df['TRPosition'].iloc[row-1] == -1:
            print(f'TRENDING BUYBACK EXIT : {row}')
            df['TRPosition'].iloc[row] = 0
            trending_sell = False

        
        if trending_buy and df['TRPosition'].iloc[row-1] == 1:
            print(f'TRENDING SELL EXIT : {row}')
            df['TRPosition'].iloc[row] = 0
            trending_buy = False

# If any positions still not 0, close them at the market price at row 301
if df["LTPosition"].iloc[300] != 0:
    df["LTPosition"].iloc[301] = 0

if df["TRPosition"].iloc[300] != 0:
    df["TRPosition"].iloc[301] = 0


df["Profit"] = (df["RETURNS"] * df["LTPosition"] * (starting_power*0.5)/df["MID PRICE"] + df["RETURNS"] * df["TRPosition"] * (starting_power*0.5)/df["MID PRICE"]).cumsum()
print(df.tail(20))

# Graph it with plotly
interactive_plot(df[["LTPosition", "TRPosition"]], "Gayer Graph")
interactive_plot(df[["Profit", "MID PRICE"]], "Gay Graph")
#interactive_plot(df[["MID PRICE", "VWAP", "VWAP_LOWER", "VWAP_UPPER", "MA(9)", "MA(21)"]], "AAPL")

