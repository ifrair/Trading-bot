from bot.dataset_parser import Parser
from bot.indicators import calc_indicators
from bot.utiles import wait_till, tf_to_minutes, time_to_int

from binance.spot import Spot

from datetime import datetime, timedelta

import json
import math
import pandas as pd


class Trader:

    __log_file = "log_trader.txt"
    __settings_file = "settings_trader.txt"
    __indicators: list = ['CCI']
    __first_balance = 0.0
    __second_balance = 0.0
    __print_friq = 1
    __slippage = 0.01
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
        f = open(self.__log_file, 'w')
        f.close()

    def trade(self):
        def print_state():
            with open(self.__log_file, 'a') as f:
                    print(
                        f'Time: {start_time}, First: {self.__first_balance}, '\
                        f'Second: {self.__second_balance}, Price: {table.iloc[-1]["Close"]}, '\
                        f'Income: {self.__income}', file=f)

        self.__update_balances()
        self.__update_symb_precision()
        start_time = datetime.now() + timedelta(minutes=self.__tf_minutes)
        start_time -= timedelta(minutes=time_to_int(start_time) // 60000 % self.__tf_minutes)
        start_time -= timedelta(seconds=start_time.second)
        with open(self.__log_file, 'a') as f:
            print(f"Start time: {start_time}, Timeframe {self.__tf_minutes} mins, Simbol {self.symb}", file=f)
        wait_till(start_time)
        table = self.__parser.get_table(100)

        step = 0
        while True:
            if step % self.__print_friq == 0:
                print_state()
            step += 1
            calc_indicators(table, self.__indicators)
            self.__update_balances()

            if table.iloc[-1]["CCI"] > 1:
                print_state()
                self.__buy_all(2)
            elif table.iloc[-1]["CCI"] < -1:
                print_state()
                self.__buy_all(1)

            start_time += timedelta(minutes=self.__tf_minutes)
            wait_till(start_time)
            table = pd.concat([table, self.__parser.get_table(1)], axis=0, ignore_index=True)[-100:].reset_index(drop=True)

    def __update_balances(self, raise_exc: bool = False):
        assets = self.client.user_asset()
        self.__first_balance = [float(asset['free']) for asset in assets if asset['asset'] == self.first_asset]
        self.__first_balance = self.__first_balance[0] if len(self.__first_balance) else 0
        self.__second_balance = [float(asset['free']) for asset in assets if asset['asset'] == self.second_asset]
        self.__second_balance = self.__second_balance[0] if len(self.__second_balance) else 0

    def __update_symb_precision(self):
        symbol_info = self.client.exchange_info(symbol=self.symb)
        stepSize = 0.0
        for filter in symbol_info['symbols'][0]['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                stepSize = float(filter['stepSize'])
        self.__symbol_precision = int(round(-math.log(stepSize, 10), 0))
        with open(self.__log_file, 'a') as f:
            print(f'Symbol precision set to {self.__symbol_precision}', file=f)

    def __buy_all(self, asset_num: int) -> None:
        self.__buy(asset_num, money=(self.__first_balance if asset_num == 2 else self.__second_balance))

    def __buy(self, asset_num: int, money: float) -> None:
        if asset_num == 1:
            money = min(self.__second_balance, money) * (1 - self.__slippage)
            money = round(money, self.__symbol_precision)
            with open(self.__log_file, 'a') as f:
                print(f"Sell {money} {self.second_asset}", file=f)
            r = self.client.new_order(
                symbol=self.symb,
                # newClientOrderId="Test_0",
                side='BUY',
                type='MARKET',
                quoteOrderQty=money,
            )
        else:
            money = min(self.__first_balance, money) * (1 - self.__slippage)
            money = round(money, self.__symbol_precision)
            with open(self.__log_file, 'a') as f:
                print(f"Sell {money} {self.first_asset}", file=f)
            r = self.client.new_order(
                symbol=self.symb,
                # newClientOrderId="Test_0",
                side='SELL',
                type='MARKET',
                quantity=money,
            )
