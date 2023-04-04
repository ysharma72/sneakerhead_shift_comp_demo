import shift
from time import sleep

with shift.Trader("sneakerhead_test01") as trader:
    trader.connect("initiator.cfg", "7nn7Y1F5aj")
    sleep(1)
    trader.sub_all_order_book()
    sleep(1)
    tickers = trader.get_stock_list()
    if trader.request_order_book(tickers):
        print(trader.get_order_book(tickers[1], shift.OrderBookType.GLOBAL_BID))
    