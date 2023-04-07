import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
import math
import numpy as np
import pandas as pd
import pandas_ta as ta

# NOTE: for documentation on the different classes and methods used to interact with the SHIFT system, 
# see: https://github.com/hanlonlab/shift-python/wiki

check_frequency = 5
max_bp = 1000000


def cancel_orders(trader: shift.Trader, ticker: str, end_time=None):

    if end_time is not None:
        while trader.get_last_trade_time() < end_time:            
            sleep(check_frequency)
            # cancel all the remaining orders
            for order in trader.get_submitted_orders():
                if order.symbol == ticker:
                    if (trader.get_last_trade_time() - order.timestamp) < timedelta(seconds=30):
                        continue
                    status = trader.get_order(order.id).status
                    if status != shift.Order.Status.REJECTED and status != shift.Order.Status.FILLED:
                        print(f'Cancelling pending orders for: {ticker}')
                        trader.submit_cancellation(order)
    else:
        for order in trader.get_submitted_orders():
                if order.symbol == ticker:
                    status = trader.get_order(order.id).status
                    if status != shift.Order.Status.REJECTED and status != shift.Order.Status.FILLED:
                        print(f'Final cancel orders for: {ticker}')
                        trader.submit_cancellation(order)

    


def close_positions(trader, ticker):
    # NOTE: The following orders may not go through if:
    # 1. You do not have enough buying power to close your short postions. Your strategy should be formulated to ensure this does not happen.
    # 2. There is not enough liquidity in the market to close your entire position at once. You can avoid this either by formulating your
    #    strategy to maintain a small position, or by modifying this function to close ur positions in batches of smaller orders.

    # close all positions for given ticker
    print(f"running close positions function for {ticker}")

    item = trader.get_portfolio_item(ticker)

    # close any long positions
    long_shares = item.get_long_shares()
    while long_shares != 0:
        print(f"market selling because {ticker} long shares = {long_shares}")
        order = shift.Order(shift.Order.Type.MARKET_SELL,
                            ticker, 1)  # we divide by 100 because orders are placed for lots of 100 shares
        trader.submit_order(order)
        item = trader.get_portfolio_item(ticker)
        long_shares = item.get_long_shares()
        sleep(1)  # we sleep to give time for the order to process

    # close any short positions
    short_shares = item.get_short_shares()
    while short_shares != 0:
        print(f"market buying because {ticker} short shares = {short_shares}")
        order = shift.Order(shift.Order.Type.MARKET_BUY,
                            ticker, 1)
        trader.submit_order(order)
        item = trader.get_portfolio_item(ticker)
        short_shares = item.get_short_shares()
        sleep(1)


def calc_order_value(type, best_ask, best_bid, spread_percent):
    spread = (best_ask - best_bid)
    offset = math.ceil(spread * spread_percent)
    if type == shift.Order.Type.LIMIT_BUY:
        return best_bid + offset
    else:
        return best_ask - offset



## Technical Indicators

# Strategy

def RSI(lookback, prices):
    # prices = pd.Series(prices)
    rsi = ta.rsi(close=prices, length=lookback)
    rsi = rsi[-1]

    # rsi is a vector of 

    # delta = prices.diff()
    # up = delta.clip(lower=0)
    # down = -1*delta.clip(upper=0)
    # avg_up = up.ewm(lookback).mean()
    # avg_down = down.ewm(lookback).mean()
    # rs = avg_up/avg_down
    # rsi = (100 - (100/(1+rs)))
    return rsi

def RSI_conv_div(lookback, prices):
    
    #Returns 1 if bullish and -1 if bearish

    rsi = RSI(lookback, prices)

    # Check for bullish convergence or bearish divergence
    half_window = int(lookback/2)
    half_rsi = rsi[-half_window:]
    half_prices = prices[-half_window:]
    is_increasing = half_prices.is_monotonic_increasing
    is_decreasing = half_prices.is_monotonic_decreasing
    if is_increasing and half_rsi.is_monotonic_decreasing:
        return 1
    elif is_decreasing and half_rsi.is_monotonic_increasing:
        return -1



def VWAP(bid_price, ask_price, bid_vol, ask_vol, multiplier):
    bid_vwap = np.dot(bid_price, bid_vol) / sum(bid_vol)
    ask_vwap = np.dot(ask_price, ask_vol) / sum(ask_vol)
    vwap = (bid_vwap + ask_vwap) / 2
    std = np.sqrt((np.dot(bid_vol, (bid_price - vwap) ** 2) + np.dot(ask_vol, (ask_price - vwap) ** 2)) / (sum(bid_vol) + sum(ask_vol)))
    return [vwap - (multiplier * std), vwap, vwap + (multiplier * std)] #Returns a list of vwap, 2 standard deviations above and below the vwap



def CompareMA(lookback1, lookback2, prices):
    # Check if Slow MA crosses over Fast MA
    # prices = pd.Series(prices)
    ma_f = ta.sma(prices, length=lookback1)
    ma_s = ta.sma(prices, length=lookback2)
    if (ma_f[len(ma_f)-1] > ma_s[len(ma_s)-1]):
        return 1  # 1 for uptrend confirmation
    elif (ma_f[len(ma_f)-1] < ma_s[len(ma_s)-1]):
        return -1  # -1 for downtrend confirm
    else: return 0  # otherwise, no signal


def BETA(lookback, prices1, prices2):
    # Rolling correlation
    prices1 = prices1[-lookback:]
    prices2 = prices2[-lookback:]
    returns1 = np.log1p(prices1.pct_change().dropna())
    returns2 = np.log1p(prices2.pct_change().dropna())
    covmat = np.cov(returns1, returns2)
    lowkey_beta_but_not_beta = covmat[0, 1]/covmat[0, 0]
    return lowkey_beta_but_not_beta