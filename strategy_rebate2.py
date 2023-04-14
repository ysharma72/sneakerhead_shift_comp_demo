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

starting_power = 300000
max_alloc = ((starting_power / 4) * 0.95) / 3
# starting_power / number of tickers
# multiply by 0.99 for some buffer
# divide by 3 so 1 part for long allocation, 2 parts for short allocation
check_freq = 1

def func(trader: shift.Trader, ticker: str, endtime: dt.datetime):
    """
    The rebate farm strategy (this function loops every check_freq seconds)
    Total algo frequency is check_freq + 10 seconds (for order placement)
    """
    df = pd.DataFrame(columns=['Type', 'Price', 'Size', 'Status'])
    while (trader.get_last_trade_time() < endtime):
        try:

            # ========== INITIALIZE PARAMETERS ========== #

            best_price = trader.get_best_price(ticker)
            # Get ask price, multiply by some percent to make it higher (store this price in a variable)
            best_bid = best_price.get_bid_price()
            best_ask = best_price.get_ask_price()
            limit_price = (best_bid + best_ask) / 2
            size = int((max_alloc / limit_price) // 100)

            trader.submit_order(shift.Order(shift.Order.Type.LIMIT_BUY, ticker, size, limit_price))
            trader.submit_order(shift.Order(shift.Order.Type.LIMIT_SELL, ticker, size, limit_price))

            '''
            # filled_early_s = False

            # ========== SELL ORDER ==========

            # print("  Price\t\tSize\t  Dest\t\tTime")
            # for order in trader.get_order_book(ticker, shift.OrderBookType.GLOBAL_ASK, 5):
            #     print(
            #         "%7.2f\t\t%4d\t%6s\t\t%19s"
            #         % (order.price, order.size, order.destination, order.time)
            #     )
            
            # Place limit order for short sale at a high ask price so no one else executes it.
            order_s = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, size, limit_price)
            print(f"Selling {size} lots of {ticker} at {limit_price}")
            trader.submit_order(order_s)
           
            # Wait 1 seconds to make sure our short order is in the system
            # sleep(5)

            # ========== CHECK SELL ORDER STATUS ========== #
            """
            # Debug: Check if our short order is in the system
            status_s = trader.get_order(order_s.id).status
            if status_s == shift.Order.Status.PENDING_NEW or status_s == shift.Order.Status.NEW:
                print(f"Good: Short order in system for {size} lots of {ticker} at ${limit_price}")
                filled_early_s = False
            else:
                print("Error: Short order already filled or not placed")
                if status_s == shift.Order.Status.FILLED or status_s == shift.Order.Status.PARTIALLY_FILLED:
                    if status_s == shift.Order.Status.PARTIALLY_FILLED: trader.submit_cancellation(order_s)
                    limit_price = trader.get_order(order_s.id).executed_price
                    size = trader.get_order(order_s.id).executed_size
                    print(f'Cuck: Someone filled our order for {size} lots of {ticker} at ${limit_price}')
                    filled_early_s = True
                else: 
                    print(f'Short order did not go through to system')
                    continue  # This means the order just didn't go through
            df.append({'Type': 'Sell', 'Price': limit_price, 'Size': size, 'Status' : status_s}, ignore_index=True)
            """

            # ========== INITIALIZE PARAMETERS ========== #

            best_price = trader.get_best_price(ticker)
            # Get ask price, multiply by some percent to make it higher (store this price in a variable)
            best_bid = best_price.get_bid_price()
            best_ask = best_price.get_ask_price()
            bid_vol = best_price.get_bid_size()
            if bid_vol == 0: continue
            spread = (best_ask - best_bid)
            limit_price = (best_ask + best_bid)/2
            if spread < 0.02:
                limit_price -= 0.01
            # Order size for short is max_alloc / limit_price  (we are putting aside 2 times max_alloc for this though)
            size = int((max_alloc / limit_price) // 100)

            # ========== BUY ORDER ========== #


            # CHECK ORDER BOOK FIRST

            # print("  Price\t\tSize\t  Dest\t\tTime")
            # for order in trader.get_order_book(ticker, shift.OrderBookType.GLOBAL_BID, 5):
            #     print(
            #         "%7.2f\t\t%4d\t%6s\t\t%19s"
            #         % (order.price, order.size, order.destination, order.time)
            #     )

            # Place a limit buy order for the same price to buy our own shares from the short position
            order_b = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, size, limit_price)
            print(f"Buying {size} lots of {ticker} at {limit_price}")
            trader.submit_order(order_b)

            # Wait 1 seconds to make sure our buy order is in the system
            # sleep(5)

            # ========== CHECK BUY ORDER STATUS ========== #

            # Debug: Check if our buy order was put in the system and filled with our short order
            # status_b = trader.get_order(order_b.id).status
            # status_s = trader.get_order(order_s.id).status

            # pending_b = (status_b == shift.Order.Status.PENDING_NEW or status_b == shift.Order.Status.NEW)
            # pending_s = (status_s == shift.Order.Status.PENDING_NEW or status_s == shift.Order.Status.NEW)
            # filled_b = (status_b == shift.Order.Status.FILLED or status_b == shift.Order.Status.PARTIALLY_FILLED)
            # filled_s = (status_s == shift.Order.Status.FILLED or status_s == shift.Order.Status.PARTIALLY_FILLED)

            # print(f"Buy order status: {status_b}")
            # print(f"Short order status: {status_s}")

            """""""""
            # Case 1: Buy is filled, Short is filled, Short was not filled earlier
            if filled_b and filled_s and not filled_early_s:
                # This is good, our orders canceled each other out
                if status_b == shift.Order.Status.PARTIALLY_FILLED: trader.submit_cancellation(order_b)
                limit_price = trader.get_order(order_b.id).executed_price
                size = trader.get_order(order_b.id).executed_size
                print(f"Good: Buy order placed for {size} lots of {ticker} at ${limit_price}")
                print(f"Buy order status: {status_b}")
                print(f"Short order status: {status_s}")
            # Case 2: Buy is filled, Short is filled, Short was filled earlier
            elif filled_b and filled_s and filled_early_s:
                # Also fine, but we need to make sure we close this buy the same time the other party closes our short (how)
                if status_b == shift.Order.Status.PARTIALLY_FILLED: trader.submit_cancellation(order_b)
                limit_price = trader.get_order(order_b.id).executed_price
                size = trader.get_order(order_b.id).executed_size
                print(f"Warning: Buy order filled for {size} lots of {ticker} at ${limit_price}, but short order filled earlier")
                #TODO
                print(f"Buy order status: {status_b}")
                print(f"Short order status: {status_s}")
            # Case 3: Buy is filled, Short is still not filled
            elif filled_b and pending_s:
                # Now we're stuck in a long position, we should maybe close it instantly to avoid risk?
                if status_b == shift.Order.Status.PARTIALLY_FILLED: trader.submit_cancellation(order_b)
                limit_price = trader.get_order(order_b.id).executed_price
                size = trader.get_order(order_b.id).executed_size
                print(f"Bad: Buy order filled for {size} lots of {ticker} at ${limit_price}, but short order not filled")
                trader.submit_cancellation(order_s)
                close_positions(trader, ticker)
                print("Closed existing position successfully")
                print(f"Buy order status: {status_b}")
                print(f"Short order status: {status_s}")
            # Case 4: Buy is not filled, Short is filled (doesn't matter if it was filled earlier or not)
            elif pending_b and filled_s:
                # We're stuck in a short position, we should close it instantly to avoid risk
                print("Bad: Short order filled, but buy order not filled")
                trader.submit_cancellation(order_b)
                close_positions(trader, ticker)
                print("Closed existing position successfully")
                print(f"Buy order status: {status_b}")
                print(f"Short order status: {status_s}")
            # Case 5: Buy is not filled, Short is not filled
            elif pending_b and pending_s:
                # Why are we here? We should have been filled by now. Just cancel the orders and move on
                print("Warning: Buy order not filled, short order not filled")
                trader.submit_cancellation(order_b)
                trader.submit_cancellation(order_s)
                print(f"Buy order status: {status_b}")
                print(f"Short order status: {status_s}")
            # Case 6: 
            else:
                print("Error: Something went wrong, you missed a case")
                print(f"Buy order status: {status_b}")
                print(f"Short order status: {status_s}")
            df.append({'Type': 'Buy', 'Price': limit_price, 'Size': size, 'Status' : status_b}, ignore_index=True)
            """
            '''

        except Exception as e:
            print(f"Error: {e}")
            continue

        
        # print("\n")
        sleep(check_freq)  # sleep for check_freq seconds before running the function again