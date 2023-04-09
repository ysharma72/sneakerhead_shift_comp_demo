import shift
import pandas as pd
import datetime as dt
from datetime import timedelta
from time import sleep
from numpy import random
from threading import Thread

def main(trader):
    tickers = trader.get_stock_list()
    check_frequency = 5
    current = trader.get_last_trade_time()
    start_time = dt.datetime.combine(current, dt.time(9, 30, 0))
    end_time = dt.datetime.combine(current, dt.time(15, 0, 0))
    
    # start_time = current
    # end_time = start_time + timedelta(minutes=1)

    while trader.get_last_trade_time() < start_time or trader.get_last_trade_time() > end_time:
        print("Waiting for market to open")
        sleep(check_frequency)


    print("START")

    lower_columns = ["BID PRICE", "BID VOLUME", "BID TIME", "ASK PRICE", "ASK VOLUME", "ASK TIME"]
    columns = pd.MultiIndex.from_product([tickers, lower_columns])
    current_data = dict.fromkeys(columns)

    big_df = pd.DataFrame(columns=pd.MultiIndex.from_product([tickers, lower_columns]))

    while(trader.get_last_trade_time() < end_time):
        
        if trader.is_connected():
            print(f"connected: {trader.get_last_trade_time()}")
            big_df.loc[trader.get_last_trade_time()] = get_data(tickers, current_data)
        sleep(check_frequency)
        
    print(big_df)
    big_df.to_csv(f'order_book_data/{dt.date.today()}.csv')  # One dataframe per trading day
    


def get_data(tickers, current_data):
    
    for i in tickers:
        for order in trader.get_order_book(i, shift.OrderBookType.GLOBAL_BID):
            current_data[i, "BID PRICE"] = order.price
            current_data[i, "BID VOLUME"] = order.size
            current_data[i, "BID TIME"] = order.time
            # current_data[i, "BID PRICE"] = random.randint(1, 100)
            # current_data[i, "BID VOLUME"] = random.randint(1, 100)
            # current_data[i, "BID TIME"] = random.randint(1, 100)
            
        for order in trader.get_order_book(i, shift.OrderBookType.GLOBAL_ASK):
            current_data[i, "ASK PRICE"] = order.price
            current_data[i, "ASK VOLUME"] = order.size
            current_data[i, "ASK TIME"] = order.time
            # current_data[i, "ASK PRICE"] = random.randint(1, 100)
            # current_data[i, "ASK VOLUME"] = random.randint(1, 100)
            # current_data[i, "ASK TIME"] = random.randint(1, 100)

        # current_data = { (ticker, orderbook_data) : value, ... }
    return current_data  # --> THIS IS ONE BIG dictionary WITH TUPLE KEYS (tickers, orderbook columns)
        
        

if __name__ == "__main__":
    with shift.Trader("sneakerhead_test01") as trader:
        trader.connect("initiator.cfg", "7nn7Y1F5aj")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)
        main(trader)
    