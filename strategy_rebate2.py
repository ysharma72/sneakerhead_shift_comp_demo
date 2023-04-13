import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from helper import *
import pandas as pd

# Theory: Place limit order for short sale at a high ask price so no one else executes it.
# Wait 15 seconds to make sure our short order is in the system
# Place a limit buy order for the same price to buy our own shares from the short position
# Place 2 limit orders that close each other out, farm rebates from them

starting_power = 500000
max_alloc = ((starting_power / 1) * 0.95) / 3
# starting_power / number of tickers
# multiply by 0.99 for some buffer
# divide by 3 so 1 part for long allocation, 2 parts for short allocation
check_freq = 5

def func(trader: shift.Trader, ticker: str, endtime: dt.datetime):
    """
    The rebate farm strategy (this function loops every check_freq seconds)
    Total algo frequency is check_freq + 10 seconds (for order placement)
    """
    df = pd.DataFrame(columns=['Type', 'Price', 'Size'])
    while (trader.get_last_trade_time() < endtime):
        try:

            # ========== INITIALIZE PARAMETERS ========== #

            best_price = trader.get_best_price(ticker)
            # Get ask price, multiply by some percent to make it higher (store this price in a variable)
            best_bid = best_price.get_bid_price()
            best_ask = best_price.get_ask_price()
            limit_price = (best_bid + best_ask) / 2
            # Order size for short is max_alloc / limit_price  (we are putting aside 2 times max_alloc for this though)
            size = int((max_alloc / limit_price) // 100)
            filled_early_s = False

            # ========== SELL ORDER ==========
            
            # Place limit order for short sale at a high ask price so no one else executes it.
            order_s = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, size, limit_price)
            print(f"Selling {size} lots of {ticker} at {limit_price}")
            trader.submit_order(order_s)

            # Wait 2 seconds to make sure our short order is in the system
            sleep(2)

            # ========== CHECK SELL ORDER STATUS ========== #

            # Debug: Check if our short order is in the system
            status_s = trader.get_order(order_s.id).status
            if status_s == shift.Order.Status.PENDING_NEW or status_s == shift.Order.Status.NEW:
                print(f"Good: Short order in system for {size} lots of {ticker} at {limit_price}")
                df.append({'Type': 'Sell', 'Price': limit_price, 'Size': size}, ignore_index=True)
                filled_early_s = False
            else:
                print("Error: Short order already filled or not placed")
                if status_s == shift.Order.Status.FILLED or status_s == shift.Order.Status.PARTIALLY_FILLED:
                    if status_s == shift.Order.Status.PARTIALLY_FILLED: trader.submit_cancellation(order_s)
                    size = order_s.executed_size
                    limit_price = order_s.executed_price
                    print(f'Cuck: Someone filled our order for {size} lots of {ticker} at {limit_price}')
                    filled_early_s = True
                else: 
                    print(f'Short order did not go through to system')
                    continue  # This means the order just didn't go through

            # ========== BUY ORDER ========== #

            # Place a limit buy order for the same price to buy our own shares from the short position
            order_b = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, size, limit_price)
            print(f"Buying {size} lots of {ticker} at {limit_price}")
            trader.submit_order(order_b)

            # Wait 2 seconds to make sure our buy order is in the system
            sleep(2)

            # ========== CHECK BUY ORDER STATUS ========== #

            # Debug: Check if our buy order was put in the system and filled with our short order
            status_b = trader.get_order(order_b.id).status
            status_s = trader.get_order(order_s.id).status

            pending_b = (status_b == shift.Order.Status.PENDING_NEW or status_b == shift.Order.Status.NEW)
            pending_s = (status_s == shift.Order.Status.PENDING_NEW or status_s == shift.Order.Status.NEW)
            filled_b = (status_b == shift.Order.Status.FILLED or status_b == shift.Order.Status.PARTIALLY_FILLED)
            filled_s = (status_s == shift.Order.Status.FILLED or status_s == shift.Order.Status.PARTIALLY_FILLED)

            # Case 1: Buy is filled, Short is filled, Short was not filled earlier
            if filled_b and filled_s and not filled_early_s:
                # This is good, our orders canceled each other out
                limit_price = trader.get_order(order_b.id).executed_price
                size = trader.get_order(order_b.id).executed_size
                # Check how much of the buy order was filled
                print(f"Good: Buy order placed for {size} lots of {ticker} at {limit_price}")
                df.append({'Type': 'Buy', 'Price': limit_price, 'Size': size}, ignore_index=True)
            # Case 2: Buy is filled, Short is filled, Short was filled earlier
            elif filled_b and filled_s and filled_early_s:
                # Also fine, but we need to make sure we close this buy the same time the other party closes our short (how)
                print("Error: Buy order not filled")
                trader.submit_cancellation(order_b)
                continue
            else:
                print("Error: Short order not filled")
                trader.submit_cancellation(order_s)
                continue

        except Exception as e:
            print(e)
            continue

        sleep(check_freq)  # sleep for check_freq seconds before running the function again

    #right here
    df.to_csv(f'order_book_data/{ticker}_rebate.csv')