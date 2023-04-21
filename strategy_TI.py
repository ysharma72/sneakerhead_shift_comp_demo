import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from helper import *
import pandas as pd
import math
import numpy as np


starting_power = 700000
max_alloc = ((starting_power / 4) * 0.95) / 3
max_lots = 18

def strategyTI(trader: shift.Trader, ticker: str, endtime):

    # Make Dataframe using the above variables as column names
    df = pd.DataFrame(columns=['price', 'bids', 'asks', 'bid_vols', 'ask_vols', 'true_range'])


    # strategy parameters
    check_freq = 5  # this iterates every 60 seconds
    last_90min = 300*(60//check_freq)  # 270 minutes from 10 AM - 2:30 PM (before last 90 mins of trading)
    order_size = 3  # NOTE: this is 3 lots which is 300 shares.

    # strategy variables  
    trending_buy, trending_sell = False, False
    long_term_buy, long_term_sell = False, False

    
    high_low = []
    orders = {}
    while (trader.get_last_trade_time() < endtime):

        # Collect data every second (This is to get the highs and lows)
        sleep(1)
        best_price = trader.get_best_price(ticker)
        best_bid = best_price.get_bid_price()
        best_ask = best_price.get_ask_price()
        mid_price = (best_bid + best_ask) / 2
        high_low.append(mid_price)

        
        #add highs and lows to the list

        # Some code
        
        # Run every check_freq seconds
        if len(high_low)%check_freq == 0:
                
            try:

                # Collect data

                best_price = trader.get_best_price(ticker)

                best_bid = best_price.get_bid_price()
                df.loc[trader.get_last_trade_time(), 'bids'] = best_bid

                best_ask = best_price.get_ask_price()
                df.loc[trader.get_last_trade_time(), 'asks'] = best_ask

                bid_vol = best_price.get_bid_size()
                df.loc[trader.get_last_trade_time(), 'bid_vols'] = bid_vol

                ask_vol = best_price.get_ask_size()
                df.loc[trader.get_last_trade_time(), 'ask_vols'] = ask_vol

                price = (best_bid + best_ask) / 2
                df.loc[trader.get_last_trade_time(), 'price'] = price

                # ATR calculation
                
                high = max(high_low)
                low = min(high_low)
                
                if len(df.price) > 2:
                    true_range = max([(high-low), abs(high-df.price[-2:-1].values[0]), abs(low-df.price[-2:-1].values[0])])
                    df.loc[trader.get_last_trade_time(), 'true_range'] = true_range
            
            
            except Exception as e:
                print(f"Error on getting data: {e}")
                continue


            # End logging

            if len(df.price) > 20 and len(df.price) < last_90min:
                high = max(high_low)
                low = min(high_low)
                true_range = max([(high-low), abs(high-df.price[-2:-1].values[0]), abs(low-df.price[-2:-1].values[0])])
                df.loc[trader.get_last_trade_time(), 'true_range'] = true_range
                rsi = RSI(10, df.price)
                df.loc[trader.get_last_trade_time(), 'rsi'] = rsi
                ma = CompareMA(9, 21, df.price)
                df.loc[trader.get_last_trade_time(), 'ma'] = ma
                vwap = VWAP(df.bids, df.asks, df.bid_vols, df.ask_vols, 1)
                df.loc[trader.get_last_trade_time(), 'vwap'] = vwap[1]
                vwap_lower = vwap[0]
                df.loc[trader.get_last_trade_time(), 'lower_vwap'] = vwap_lower
                vwap_upper = vwap[2]
                df.loc[trader.get_last_trade_time(), 'higher_vwap'] = vwap_upper
                vwap_ = VWAP(df.bids, df.asks, df.bid_vols, df.ask_vols, 0.2)

                #For stop loss/target
                atr = np.mean(df.true_range[-14:].values)
                swing_high = df.price[-14:].values.max()
                swing_low = df.price[-14:].values.min()
                
                #Entering longer term trades
                item = trader.get_portfolio_item(ticker)
                current_value_long = item.get_long_shares() * price
                current_value_short = item.get_short_shares() * price

                
                if rsi < 40 and (2*max_alloc > current_value_short and max_lots*100 > abs(item.get_shares())):
                    print('LONG TERM RSI SELL ENTRY')
                    order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, order_size)
                    print(f"TI: Selling {ticker} at {best_bid}")
                    trader.submit_order(order)
                    long_term_sell = True

                    orders[order] = swing_high+atr
                                  

                elif rsi > 60 and (max_alloc > current_value_long and max_lots*100 > abs(item.get_shares())):
                    print('LONG TERM RSI BUY ENTRY')
                    order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, order_size)
                    print(f"TI: Buying {ticker} at {best_ask}")
                    trader.submit_order(order)
                    long_term_buy = True

                    orders[order] = swing_low-atr
                
                #Getting out of long term trades
                if long_term_sell and rsi in range(30, 45) and (max_alloc > current_value_long and max_lots*100 > abs(item.get_shares())):
                    print('LONG TERM BUYBACK EXIT')
                    order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, order_size)
                    print(f"TI: Buying {ticker} at {best_ask}")
                    trader.submit_order(order)
                    
                
                if long_term_buy and rsi in range(55, 70) and (2*max_alloc > current_value_short and max_lots*100 > abs(item.get_shares())):
                    print('LONG TERM SELL EXIT')
                    order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, order_size)
                    print(f"TI: Selling {ticker} at {best_bid}")
                    trader.submit_order(order)
                    
                #===========================================================================================================================
        
                #Entering trending trades
                if ma < 0 and (2*max_alloc > current_value_short and max_lots*100 > abs(item.get_shares())):
                    print('TRENDING SELL ENTRY')
                    #Price is very far above VWAP but moving averages cross down, sell
                    order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, order_size)
                    print(f"TI: Selling {ticker} at {best_bid}")
                    trader.submit_order(order)
                    trending_sell = True
                    
                    orders[order] = price+atr

                elif ma > 0 and (max_alloc > current_value_long and max_lots*100 > abs(item.get_shares())): #Price is very far below VWAP but moving averages cross up, buy
                    print('TRENDING BUY ENTRY')
                    order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, order_size)
                    print(f"TI: Buying {ticker} at {best_ask}")
                    trader.submit_order(order)
                    trending_buy = True

                    orders[order] = price-atr
                
                # Getting out of trending trades
                if trending_sell and price < vwap_[2] and (max_alloc > current_value_long and max_lots*100 > abs(item.get_shares())):
                    print('TRENDING BUYBACK EXIT')
                    order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, order_size)
                    print(f"TI: Buying {ticker} at {best_ask}")
                    trader.submit_order(order)
                    trending_sell = False

                
                if trending_buy and price > vwap_[0] and (2*max_alloc > current_value_short and max_lots*100 > abs(item.get_shares())):
                    print('TRENDING SELL EXIT')
                    order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, order_size)
                    print(f"TI: Selling {ticker} at {best_bid}")
                    trader.submit_order(order)
                    trending_buy = False

            elif len(df.price) > last_90min:
                if trader.get_unrealized_pl(ticker) > 0:
                    order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, order_size)
                    print(f"TI: Selling {ticker} at {best_bid}")
                    trader.submit_order(order)
                else:
                    order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, order_size)
                    print(f"TI: Buying {ticker} at {best_ask}")
                    trader.submit_order(order)

            # Here we are going to check if any of our placed orders became filled, so we can place the stop loss and take profit for them
            for order in trader.get_submitted_orders():
                if order in orders:
                    if order.status == shift.Order.Status.FILLED and order.type == shift.Order.Type.MARKET_BUY:
                        stop_order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, order_size)
                    elif order.status == shift.Order.Status.FILLED and order.type == shift.Order.Type.MARKET_SELL:
                        stop_order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, order_size)
                    else: continue
                
                    trader.submit_order(stop_order)
                    orders.pop(order)

            # add any new orders from this iteration to the dictionary now (append new order and its stop-loss and take-profit orders)


