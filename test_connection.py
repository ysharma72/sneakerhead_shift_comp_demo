import shift
import datetime as dt
from time import sleep

#list of ip's
'''
155.246.104.62
155.246.104.81
155.246.104.82
155.246.104.83
155.246.104.84
155.246.104.86
'''

if __name__ == '__main__':
    with shift.Trader(f"sneakerhead_test06") as trader:
        trader.connect(f"initiator.cfg", "7nn7Y1F5aj")
        sleep(2)
        print(f"Server Time: {trader.get_last_trade_time()}")
        print(f"Current Time: {dt.datetime.now()}")
        print(f"Combined: {dt.datetime.combine(trader.get_last_trade_time(), dt.time(10, 00, 0))}")