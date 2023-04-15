from bot.dataset_parser import Parser
from bot.indicators import calc_indicators
from bot.utiles import wait_till, tf_to_minutes, time_to_int

from binance.spot import Spot

from datetime import datetime, timedelta

import pandas as pd


class Trader:

    __indicators: list = ['CCI']
    __first_balance = 0
    __second_balance = 0
    __print_friq = 1
    # __risk_coef = 1000000
    __withdrawal_coef = 0
    __income = 0
    __comission = 0

    def __init__(
        self,
        api_key: str,
        sec_key: str,
        first_asset: str = "BTC",
        second_asset: str = "USDT",
        tf: str = "1m",
        timezone: int = 0):
        """
        :param api_key: api key to market
        :param sec_key: secure key to market
        :param first_asset: first asset of trading pair
        :param second_asset: second asset of trading pair
        :param tf: candle timeframe
        """
        self.client = Spot(
            api_key,
            sec_key,
            base_url="https://api.binance.com",
            # proxies={ 'https': creds.proxy }
        )
        self.first_asset = first_asset
        self.second_asset = second_asset
        self.symb = first_asset + second_asset
        self.__parser = Parser(self.symb, tf, timezone)
        self.__tf_minutes = tf_to_minutes(tf)

    def trade(self):
        self.__update_balances()

        start_time = datetime.now() + timedelta(minutes=self.__tf_minutes)
        start_time -= timedelta(minutes=time_to_int(start_time) // 60000 % self.__tf_minutes)
        start_time -= timedelta(seconds=start_time.second)
        print(start_time)
        wait_till(start_time)
        table = self.__parser.get_table(100)

        step = 0
        while True:
            step += 1
            calc_indicators(table, self.__indicators)
            self.__update_balances()

            # buy some less
            print(table.tail())

            if step % self.__print_friq == 0:
                print(f'Time: {start_time}, First: {int(self.__first_balance)}, Second: {int(self.__second_balance)}, Price: {int(table.iloc[-1]["Close"])}, Income: {int(self.__income)}')

            start_time += timedelta(minutes=self.__tf_minutes)
            wait_till(start_time)
            table = pd.concat([table, self.__parser.get_table(1)], axis=0, ignore_index=True)[-100:].reset_index(drop=True)

    def __update_balances(self, raise_exc: bool = False):
        # old_first = self.__first_balance
        # old_second = self.__second_balance
        self.__first_balance = 0 # TODO
        self.__second_balance = 0 # TODO
        # if abs(old_first - self.__first_balance) / self.__first_balance > 0.001 or \
        #     abs(old_second - self.__second_balance) / self.__second_balance > 0.001:
        #     raise Exception("Too big difference between calculated and real balances")

    def __buy_first(self, money: float) -> None:
        pass

    def __buy_second(self, money: float) -> None:
        pass
