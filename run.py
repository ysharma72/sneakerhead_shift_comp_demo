import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread

from helper import cancel_orders, close_positions
from strategy1 import strategy

def main(trader):
    # keeps track of times for the simulation
    check_frequency = 60
    current = trader.get_last_trade_time()
    start_time1 = datetime.combine(current, dt.time(9, 30, 0))
    end_time1 = datetime.combine(current, dt.time(9, 55, 0))
    start_time2 = datetime.combine(current, dt.time(10, 0, 0))
    end_time2 = datetime.combine(current, dt.time(3, 45, 0))
    # start_time = current
    # end_time = start_time + timedelta(minutes=1)

    while trader.get_last_trade_time() < start_time1:
        print("Waiting for market to open")
        sleep(check_frequency)

    
    # we track our overall initial profits/losses value to see how our strategy affects it
    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads1 = []

    # in this example, we simultaneously and independantly run our trading alogirthm on ALL tickers
    tickers = shift.trader.get_stock_list()

    print("START")

    
    for ticker in tickers:
        # initializes threads containing the strategy for each ticker
        threads1.append(
            Thread(target=strategy, args=(trader, ticker, end_time2))
        )

    for thread in threads1:
        thread.start()
        sleep(1)

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time2:
        sleep(check_frequency)

    # wait for all threads to finish
    for thread in threads1:
        # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
        # setting the timeout argument for join() can prevent this
        thread.join()

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    
    # Rebate strategy for Volatile Market

    while trader.get_last_trade_time() < end_time1:
        print("Trading on high volatility market time")
        sleep(check_frequency)

    # we track our overall initial profits/losses value to see how our strategy affects it
    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads2 = []

    # in this example, we simultaneously and independantly run our trading alogirthm on ALL tickers
    tickers = shift.trader.get_stock_list()

    print("START")

    
    for ticker in tickers:
        # initializes threads containing the strategy for each ticker
        threads2.append(
            Thread(target=strategy, args=(trader, ticker, end_time2))
        )

    for thread in threads2:
        thread.start()
        sleep(1)

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time2:
        sleep(check_frequency)

    # wait for all threads to finish
    for thread in threads2:
        # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
        # setting the timeout argument for join() can prevent this
        thread.join()

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    print("END")
    print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")
    print(
        f"final profits/losses: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")


if __name__ == '__main__':
    with shift.Trader("sneakerhead_test07") as trader:
        trader.connect("initiator.cfg", "7nn7Y1F5aj")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)

        main(trader)
