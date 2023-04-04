import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from helper import *

price = []
buying_power = 0

def strategy(trader: shift.Trader, ticker: str, endtime):
    # NOTE: Unlike the following sample strategy, it is highly reccomended that you track and account for your buying power and
    # position sizes throughout your algorithm to ensure both that have adequite captial to trade throughout the simulation and
    # that you are able to close your position at the end of the strategy without incurring major losses.

    initial_pl = trader.get_portfolio_item(ticker).get_realized_pl()

    # strategy parameters
    check_freq = 1
    order_size = 5  # NOTE: this is 5 lots which is 500 shares.

    # strategy variables
    best_price = trader.get_best_price(ticker)
    best_bid = best_price.get_bid_price()
    best_ask = best_price.get_ask_price()
    bid_volume = best_price.get_bid_volume()
    ask_volume = best_price.get_ask_volume()
    price.append((best_bid + best_ask) / 2)

    if len(price > 10):
        rsi = RSI(10, price)
        vwap = VWAP(10, best_bid, best_ask, bid_volume, ask_volume)
        ma = CrossoverMA(20, 60, price)

        if rsi > 70 and ma < 0 and vwap < best_bid:
            order = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_SELL, best_ask, best_bid, 0.15))
            trader.submit_order(order)
        elif rsi < 30 and ma > 0 and vwap > best_ask:
            order = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, order_size, price=calc_order_value(shift.Order.Type.LIMIT_BUY, best_ask, best_bid, 0.15))
            trader.submit_order(order)
        

    while (trader.get_last_trade_time() < endtime):
        # cancel unfilled orders from previous time-step
        cancel_orders(trader, ticker)

        # get necessary data
        best_price = trader.get_best_price(ticker)
        best_bid = best_price.get_bid_price()
        best_ask = best_price.get_ask_price()
        midprice = (best_bid + best_ask) / 2

        # place order
        if (midprice > previous_price):  # price has increased since last timestep
            # we predict price will continue to go up
            order = shift.Order(
                shift.Order.Type.LIMIT_BUY, ticker, order_size)
            trader.submit_order(order)
        elif (midprice < previous_price):  # price has decreased since last timestep
            # we predict price will continue to go down
            order = shift.Order(
                shift.Order.Type.LIMIT_SELL, ticker, order_size)
            trader.submit_order(order)

            # NOTE: If you place a sell order larger than your current long position, it will result in a short sale, which
            # requires buying power both for the initial short_sale and to close your short position.For example, if we short
            # sell 1 lot of a stock trading at $100, it will consume 100*100 = $10000 of our buying power. Then, in order to
            # close that position, assuming the price has not changed, it will require another $10000 of buying power, after
            # which our pre short-sale buying power will be restored, minus any transaction costs. Therefore, it requires
            # double the buying power to open and close a short position than a long position.

        previous_price = midprice
        sleep(check_freq)

    # cancel unfilled orders and close positions for this ticker
    cancel_orders(trader, ticker)
    close_positions(trader, ticker)

    print(
        f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - initial_pl}")