import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
import math
import numpy as np
import pandas_ta as ta

# NOTE: for documentation on the different classes and methods used to interact with the SHIFT system, 
# see: https://github.com/hanlonlab/shift-python/wiki

def cancel_orders(trader, ticker):
    # cancel all the remaining orders
    for order in trader.get_waiting_list():
        if (order.symbol == ticker):
            trader.submit_cancellation(order)
            sleep(1)  # the order cancellation needs a little time to go through


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
    if long_shares > 0:
        print(f"market selling because {ticker} long shares = {long_shares}")
        order = shift.Order(shift.Order.Type.MARKET_SELL,
                            ticker, int(long_shares/100))  # we divide by 100 because orders are placed for lots of 100 shares
        trader.submit_order(order)
        sleep(1)  # we sleep to give time for the order to process

    # close any short positions
    short_shares = item.get_short_shares()
    if short_shares > 0:
        print(f"market buying because {ticker} short shares = {short_shares}")
        order = shift.Order(shift.Order.Type.MARKET_BUY,
                            ticker, int(short_shares/100))
        trader.submit_order(order)
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
    rsi = ta.rsi(close=prices, length=lookback)[-1]

    # rsi is a vector of 

    # delta = prices.diff()
    # up = delta.clip(lower=0)
    # down = -1*delta.clip(upper=0)
    # avg_up = up.ewm(lookback).mean()
    # avg_down = down.ewm(lookback).mean()
    # rs = avg_up/avg_down
    # rsi = (100 - (100/(1+rs)))
    return rsi


def VWAP(bid_price, ask_price, bid_vol, ask_vol):
    
    bid_vwap = sum(bid_price*bid_vol)/sum(bid_vol)
    ask_vwap = sum(ask_price*ask_vol)/sum(ask_vol)
    return (bid_vwap+ask_vwap) / 2


def CrossoverMA(lookback1, lookback2, prices):
    # Check if Slow MA crosses over Fast MA
    ma_f = ta.sma(prices, length=lookback1)
    ma_s = ta.sma(prices, length=lookback2)
    if (ma_f[-1] > ma_s[-1]) and (ma_f[-2:-1].values[0] < ma_s[-2:-1].values[0]):
        return 1  # 1 for buy signal
    elif (ma_f[-1] < ma_s[-1]) and (ma_f[-2:-1].values[0] > ma_s[-2:-1].values[0]):
        return -1  # -1 for sell signal
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