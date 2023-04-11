import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from helper import *
import pandas as pd


starting_power = 500000
max_alloc = ((starting_power / 4) * 0.99) / 3
max_lots = 5

def strategyTI(trader: shift.Trader, ticker: str, endtime):

    # Make Dataframe using the above variables as column names
    df = pd.DataFrame(columns=['price', 'bids', 'asks', 'bid_vols', 'ask_vols'])


    # strategy parameters
    check_freq = 15  # this iterates every 60 seconds
    order_size = 3  # NOTE: this is 3 lots which is 300 shares.

    # strategy variables  
    trending_buy, trending_sell = False, False
    long_term_buy, long_term_sell = False, False

    while (trader.get_last_trade_time() < endtime):

        sleep(check_freq)

        # try:

        best_price = trader.get_best_price(ticker)

        best_bid = best_price.get_bid_price()
        df.loc[trader.get_last_trade_time(), 'bids'] = best_bid
        # bids.append(best_price.get_bid_price())
        best_ask = best_price.get_ask_price()
        df.loc[trader.get_last_trade_time(), 'asks'] = best_ask
        # asks.append(best_price.get_ask_price())
        bid_vol = best_price.get_bid_size()
        df.loc[trader.get_last_trade_time(), 'bid_vols'] = bid_vol
        # bid_vols.append(best_price.get_bid_size())
        ask_vol = best_price.get_ask_size()
        df.loc[trader.get_last_trade_time(), 'ask_vols'] = ask_vol
        # ask_vols.append(best_price.get_ask_size())
        price = (best_bid + best_ask) / 2
        df.loc[trader.get_last_trade_time(), 'price'] = price
        # price.append((best_bid + best_ask) / 2)
        
        # except Exception as e:
        #     print(f"Error on getting data: {e}")
        #     continue


        # End logging

        if len(df.price) > 20:
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

            
            #Entering longer term trades
            item = trader.get_portfolio_item(ticker)
            current_value_long = item.get_long_shares() * price
            current_value_short = item.get_short_shares() * price
                
            if rsi > 70 and price > vwap_upper and (2*max_alloc > current_value_short and max_lots > item.get_shares()):
                print('LONG TERM RSI SELL ENTRY')
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"TI: Selling {ticker} at {best_bid}")
                trader.submit_order(order)
                long_term_sell = True
            elif rsi < 30 and price < vwap_lower and (max_alloc > current_value_long and max_lots > item.get_shares()):
                print('LONG TERM RSI BUY ENTRY')
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"TI: Buying {ticker} at {best_ask}")
                trader.submit_order(order)
                long_term_buy = True
            
            #Getting out of long term trades
            if long_term_sell and rsi in range(30, 45) and (max_alloc > current_value_long and max_lots > item.get_shares()):
                print('LONG TERM BUYBACK EXIT')
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"TI: Buying {ticker} at {best_ask}")
                trader.submit_order(order)
            
            if long_term_buy and rsi in range(55, 70) and (2*max_alloc > current_value_short and max_lots > item.get_shares()):
                print('LONG TERM SELL EXIT')
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"TI: Selling {ticker} at {best_bid}")
                trader.submit_order(order)
                
            #===========================================================================================================================
    
            #Entering trending trades
            if ma < 0 and price > vwap_upper and (2*max_alloc > current_value_short and max_lots > item.get_shares()):
                print('TRENDING SELL ENTRY')
                #Price is very far above VWAP but moving averages cross down, sell
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"TI: Selling {ticker} at {best_bid}")
                trader.submit_order(order)
                trending_sell = True
            elif ma > 0 and price < vwap_lower and (max_alloc > current_value_long and max_lots > item.get_shares()): #Price is very far below VWAP but moving averages cross up, buy
                print('TRENDING BUY ENTRY')
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"TI: Buying {ticker} at {best_ask}")
                trader.submit_order(order)
                trending_buy = True
            
            # Getting out of trending trades
            if trending_sell and (price > vwap[1] and price < vwap[2]) and (max_alloc > current_value_long and max_lots > item.get_shares()):
                print('TRENDING BUYBACK EXIT')
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"TI: Buying {ticker} at {best_ask}")
                trader.submit_order(order)
                trending_sell = False

            
            if trending_buy and (price > vwap[0] and price < vwap[1]) and (2*max_alloc > current_value_short and max_lots > item.get_shares()):
                print('TRENDING SELL EXIT')
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"TI: Selling {ticker} at {best_bid}")
                trader.submit_order(order)
                trending_buy = False
