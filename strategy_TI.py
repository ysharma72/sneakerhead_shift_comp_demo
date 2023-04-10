import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from helper import *
import pandas as pd



def strategyTI(trader: shift.Trader, ticker: str, endtime):

    # Make Dataframe using the above variables as column names
    df = pd.DataFrame(columns=['price', 'bids', 'asks', 'bid_vols', 'ask_vols'])


    initial_pl = trader.get_portfolio_item(ticker).get_realized_pl()

    # strategy parameters
    check_freq = 1  # this iterates every 60 seconds
    order_size = 3  # NOTE: this is 3 lots which is 300 shares.

    # strategy variables        

    while (trader.get_last_trade_time() < endtime):

        sleep(check_freq)
        # cancel unfilled orders from previous time-step
        cancel_orders(trader, ticker)

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


            #Longer term trades
            if rsi > 70 and df.price > vwap_upper:
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"Selling {ticker} at {best_bid}")
                trader.submit_order(order)
            elif rsi < 30 and df.price < vwap_lower:
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"Buying {ticker} at {best_ask}")
                trader.submit_order(order)

            #Trending trades
            trending_buy, trending_sell = False, False
            if ma < 0 and df.price > vwap_upper: #Price is very far above VWAP but moving averages cross down, sell
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"Selling {ticker} at {best_bid}")
                trader.submit_order(order)
                trending_sell = True
            elif ma > 0 and df.price < vwap_lower: #Price is very far below VWAP but moving averages cross up, buy
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"Buying {ticker} at {best_ask}")
                trader.submit_order(order)
                trending_buy = True
            
            if trending_sell and df.price in range(vwap, vwap_[2]):
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.75))
                print(f"Buying {ticker} at {best_ask}")
                trader.submit_order(order)
            if trending_buy and df.price in range(vwap_[0], vwap):
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.75))
                print(f"Selling {ticker} at {best_bid}")
                trader.submit_order(order)

            # NOTE: If you place a sell order larger than your current long position, it will result in a short sale, which
            # requires buying power both for the initial short_sale and to close your short position.For example, if we short
            # sell 1 lot of a stock trading at $100, it will consume 100*100 = $10000 of our buying power. Then, in order to
            # close that position, assuming the price has not changed, it will require another $10000 of buying power, after
            # which our pre short-sale buying power will be restored, minus any transaction costs. Therefore, it requires
            # double the buying power to open and close a short position than a long position.

        

    # cancel unfilled orders and close positions for this ticker
    cancel_orders(trader, ticker)
    close_positions(trader, ticker)

    # Create df from the different lists
    df.to_csv('order_book_data/test_data.csv')

    print(
        f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - initial_pl}")

#Notes

#