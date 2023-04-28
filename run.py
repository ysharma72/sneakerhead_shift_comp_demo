import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread

from helper import cancel_orders, close_positions
from strategy_TI import *
from strategy_rebate import *
from strategy_rebate2 import *

check_frequency = 5

def main(trader):
    # keeps track of times for the simulation
    
    current = trader.get_last_trade_time()
    # start_time1 = datetime.combine(current, dt.time(9, 30, 0))
    # end_time1 = datetime.combine(current, dt.time(9, 55, 0))
    start_time2 = datetime.combine(current, dt.time(9, 45, 0))
    end_time2 = datetime.combine(current, dt.time(15, 30, 0))
    # start_time2 = current
    # end_time2 = start_time2 + timedelta(minutes=10)

    # while trader.get_last_trade_time() < start_time1:
    #     print("Waiting for market to open")
    #     sleep(check_frequency)

    
    # # we track our overall initial profits/losses value to see how our strategy affects it
    # initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    # threads1 = []

    # # in this example, we simultaneously and independantly run our trading alogirthm on ALL tickers
    # tickers = trader.get_stock_list()

    # print("START")

    
    # for ticker in tickers:
    #     # initializes threads containing the strategy for each ticker
    #     threads1.append(
    #         Thread(target=strategy, args=(trader, ticker, end_time2))
    #     )

    # for thread in threads1:
    #     thread.start()
    #     sleep(1)

    # # wait until endtime is reached
    # while trader.get_last_trade_time() < end_time1:
    #     sleep(check_frequency)

    # # wait for all threads to finish
    # for thread in threads1:
    #     # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
    #     # setting the timeout argument for join() can prevent this
    #     thread.join()

    # # make sure all remaining orders have been cancelled and all positions have been closed
    # for ticker in tickers:
    #     cancel_orders(trader, ticker)
    #     close_positions(trader, ticker)

    
    # # Rebate strategy for Volatile Market

    while trader.get_last_trade_time() < start_time2:
        print("waiting to start at 09:45 AM")
        sleep(check_frequency)

    # we track our overall initial profits/losses value to see how our strategy affects it
    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads2 = []

    # in this example, we simultaneously and independantly run our trading alogirthm on ALL tickers
    # tickers = trader.get_stock_list()
    tickers_rebate = ["JPM", "AAPL", "BA", "CVX"]
    tickers_TI = ["DIS", "JPM", "PG", "WMT"]
    print("START")
    
    for ticker in tickers_TI:
        # initializes threads containing the strategy for each ticker
        threads2.append(
            Thread(target=strategyTI, args=(trader, ticker, end_time2))
        )
        threads2.append(
            Thread(target=cancel_orders, args=(trader, ticker, end_time2))
        )
        # threads2.append(
        #     Thread(target=manage_holdings, args=(trader, ticker, end_time2, -0.002, 0.004))
        # )


    # for ticker in tickers_rebate:
    #     # initializes threads containing the strategy for each ticker
    #     threads2.append(
    #         Thread(target=shortTrades, args=(trader, ticker, end_time2))
    #     )
    #     threads2.append(
    #         Thread(target=longTrades, args=(trader, ticker, end_time2))
    #     )
    #     threads2.append(
    #         Thread(target=cancel_orders, args=(trader, ticker, end_time2))
    #     )
    #     threads2.append(
    #         Thread(target=manage_holdings, args=(trader, ticker, end_time2, -0.002, 0.004))
    #     )
    

    for thread in threads2:
        thread.start()
        sleep(1)

    count_ticks = 0

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time2:

        # Every 30 seconds, log current time
        if count_ticks % 6 == 0:
            print(f"Current time: {trader.get_last_trade_time()}")
            # Print current portfolio summary as well
            print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
            print(
                "%12.2f\t%12d\t%9.2f\t%26s"
                % (
                    trader.get_portfolio_summary().get_total_bp(),
                    trader.get_portfolio_summary().get_total_shares(),
                    trader.get_portfolio_summary().get_total_realized_pl(),
                    trader.get_portfolio_summary().get_timestamp(),
                )
            )

            print("Symbol\t\tShares\t\tPrice\t\tP&L\t\tTimestamp")
            for item in trader.get_portfolio_items().values():
                print(
                    "%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s"
                    % (
                        item.get_symbol(),
                        item.get_shares(),
                        item.get_price(),
                        item.get_realized_pl(),
                        item.get_timestamp(),
                    )
                )

        count_ticks += 1

        sleep(check_frequency)

    # wait for all threads to finish
    for thread in threads2:
        # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
        # setting the timeout argument for join() can prevent this
        thread.join(timeout=check_frequency)

    print("Finished strats, clearing positions now")
    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers_TI:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    # for ticker in tickers_rebate:
    #     cancel_orders(trader, ticker)
    #     close_positions(trader, ticker)

    sleep(check_frequency)

    ordercounts_TI = {}
    ordercounts_rebate = {}
    for ticker in tickers_TI:
        lots = 0
        for order in trader.get_submitted_orders():
            if order.symbol == ticker:
                status = trader.get_order(order.id).status
                if status == shift.Order.Status.FILLED or status == shift.Order.Status.PARTIALLY_FILLED:
                    lots += order.executed_size

        ordercounts_TI[ticker] = lots

    # for ticker in tickers_rebate:
    #     lots = 0
    #     for order in trader.get_submitted_orders():
    #         if order.symbol == ticker:
    #             status = trader.get_order(order.id).status
    #             if status == shift.Order.Status.FILLED or status == shift.Order.Status.PARTIALLY_FILLED:
    #                 lots += order.executed_size

    #     ordercounts_rebate[ticker] = lots

    
    print(f'Order counts TI: {ordercounts_TI}')
    # print(f'Order counts rebate: {ordercounts_rebate}')

    sleep(check_frequency)

    print("END")
    # print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")
    # print(
    #     f"final profits/losses: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")
    # print(f"final shares: {trader.get_portfolio_summary().get_total_shares()}")

    print(f"Current time: {trader.get_last_trade_time()}")
    # Print current portfolio summary as well
    print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
    print(
        "%12.2f\t%12d\t%9.2f\t%26s"
        % (
            trader.get_portfolio_summary().get_total_bp(),
            trader.get_portfolio_summary().get_total_shares(),
            trader.get_portfolio_summary().get_total_realized_pl(),
            trader.get_portfolio_summary().get_timestamp(),
        )
    )

    print("Symbol\t\tShares\t\tPrice\t\tP&L\t\tTimestamp")
    for item in trader.get_portfolio_items().values():
        print(
            "%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s"
            % (
                item.get_symbol(),
                item.get_shares(),
                item.get_price(),
                item.get_realized_pl(),
                item.get_timestamp(),
            )
        )



if __name__ == '__main__':
    with shift.Trader("sneakerhead") as trader:
        trader.connect("initiator.cfg", "7nn7Y1F5aj")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)
        main(trader)
