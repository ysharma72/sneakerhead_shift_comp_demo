import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from helper import *


# Portfolio : 1M
# 600K Rebate Strategy, 400K TI Strategy
# Rebates are added on at the end of the day


starting_power = 300000
max_alloc = ((starting_power / 4) * 0.99) / 3
# starting_power / number of tickers
# multiply by 0.99 for some buffer
# divide by 3 so 1 part for long allocation, 2 parts for short allocation
max_lots = 12
check_freq = 1
order_size = 3  # NOTE: this is 3 lots which is 300 shares, so we earn 60 cents per trade.


def longTrades(trader: shift.Trader, ticker: str, endtime):
    # Market Making Rebate Strategy: Earn 20 cents per lot traded
    
    initial_pl = trader.get_portfolio_item(ticker).get_realized_pl()

    # strategy variables
    while (trader.get_last_trade_time() < endtime):
        sleep(check_freq)
        try:
            best_price = trader.get_best_price(ticker)

            best_bid = best_price.get_bid_price()
            best_ask = best_price.get_ask_price()
            ask_vol = best_price.get_ask_size()
            
            if ask_vol == 0: continue

            price = (best_bid + best_ask) / 2
            spread = (best_ask - best_bid)

            # item = trader.get_portfolio_item(ticker)
            # current_value = item.get_long_shares() * price

            if max_alloc > trader.get_portfolio_item(ticker).get_long_shares()*price and max_lots*100 > abs(trader.get_portfolio_item(ticker).get_shares()):
                price = best_bid
                # If spread is this tight, then we should be able to place an order below the best_bid and still get filled
                if spread < 0.02:
                    price -= 0.01
                order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price)
                print(f"Buying {ticker} at {price}")
                trader.submit_order(order)
            else: continue
        except Exception as e:
            print(f"Error in longing {ticker}:", e)
            continue

    print(f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - initial_pl}")
        

def shortTrades(trader: shift.Trader, ticker: str, endtime):
# Market Making Rebate Strategy: Earn 20 cents per lot traded

    
    initial_pl = trader.get_portfolio_item(ticker).get_realized_pl()

    # strategy variables
    while (trader.get_last_trade_time() < endtime):
        
        sleep(check_freq)

        try:
        
            best_price = trader.get_best_price(ticker)

            best_bid = best_price.get_bid_price()
            best_ask = best_price.get_ask_price()
            bid_vol = best_price.get_bid_size()
            if bid_vol == 0:
                continue
            price = (best_bid + best_ask) / 2

            spread = (best_ask - best_bid)

            # item = trader.get_portfolio_item(ticker)
            # current_value = item.get_short_shares() * price
        
            if 2*max_alloc > trader.get_portfolio_item(ticker).get_short_shares()*price and max_lots*100 > abs(trader.get_portfolio_item(ticker).get_shares()):
                price = best_ask
                # If spread is this tight, then we should be able to place an order below the best_bid and still get filled
                if spread < 0.02:
                    price += 0.01
                    
                order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price)
                print(f"Selling {ticker} at {price}")
                trader.submit_order(order)
            else: continue
        except Exception as e:
            print(f"Error in shorting {ticker}:", e)
            continue

    print(f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - initial_pl}")
