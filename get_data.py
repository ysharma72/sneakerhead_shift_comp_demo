import shift
import pandas as pd
import datetime as dt
from datetime import timedelta
from time import sleep

def main(trader):
    tickers = trader.get_stock_list()
    check_frequency = 60
    current = trader.get_last_trade_time()
    # start_time = dt.combine(current, dt.time(9, 30, 0))
    # end_time = dt.combine(current, dt.time(4, 0, 0))
    
    start_time = current
    end_time = start_time + timedelta(minutes=1)

    while trader.get_last_trade_time() < start_time:
        print("Waiting for market to open")
        sleep(check_frequency)

    big_df = pd.DataFrame(columns = tickers)

    if trader.request_order_book(tickers):
        big_df.loc[dt.datetime.now()] = get_data(tickers)

    print(big_df)


def get_data(tickers):
    all_curr_data = pd.DataFrame()
    for i in tickers:

        for order in trader.get_order_book(i, shift.OrderBookType.GLOBAL_BID):
            current_data = pd.Series(index=dt.datetime.now())
            current_data["BID PRICE"] = order.price
            current_data["BID VOLUME"] = order.size
            current_data["BID TIME"] = order.time
        for order in trader.get_order_book(i, shift.OrderBookType.GLOBAL_ASK):
            current_data["ASK PRICE"] = order.price
            current_data["ASK VOLUME"] = order.size
            current_data["ASK TIME"] = order.time
            
        # current_data = [BID PRICE, BID VOLUME, BID TIME, ASK PRICE, ASK VOLUME, ASK TIME]

        all_curr_data[i] = current_data
        
        # big_df = [ticker : current_data, ticker : current_data, ..., ticker : current_data]
    return all_curr_data  # --> THIS IS ONE BIG ROW WITH MULTIINDEX (tickers, orderbook columns)
        
        

if __name__ == "__main__":
    with shift.Trader("sneakerhead_test01") as trader:
        trader.connect("initiator.cfg", "7nn7Y1F5aj")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)
        main(trader)
    