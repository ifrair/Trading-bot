from bot.dataset_parser import Parser
from bot.indicators import Indicators
from bot.utiles import wait_till, tf_to_minutes, time_to_int

from binance.spot import Spot
from datetime import datetime, timedelta
from multipledispatch import dispatch

import json
import math
import pandas as pd


class Trader:
    __settings_file = "settings.json"
    __first_balance = 0.0
    __second_balance = 0.0
    # money to save (in second asset by default)
    __income = 0.0

    def __init__(
        self,
        api_key: str,
        sec_key: str,
        first_asset: str = "BTC",
        second_asset: str = "USDT",
        tf: str = "1m",
        timezone: int = 0
    ):
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
        self.__update_settings()
        self.__update_symb_precision()

    # function to start infinite loop to trade every timeframe minutes
    def trade(self) -> None:
        def print_state(msg: str = None):
            with open(self.__settings["log_file"], 'a') as f:
                print(
                    msg if msg is not None else
                    f"Time: {start_time}, "
                    f"First: {self.__first_balance}, "
                    f"Second: {self.__second_balance}, "
                    f"Price: {table.iloc[-1]['Close']}, "
                    f"Income: {self.__income}",
                    file=f,
                )

        self.__update_settings()
        self.__update_balances()
        # cleaning logs
        f = open(self.__settings["log_file"], 'w')
        f.close()
        # updating start time
        start_time = datetime.now() + timedelta(minutes=self.__tf_minutes)
        start_time -= timedelta(
            minutes=time_to_int(start_time) // 60000 % self.__tf_minutes,
        )
        start_time -= timedelta(seconds=start_time.second)
        print_state(
            f"Start time: {start_time},"
            f"Timeframe {self.__tf_minutes} mins, "
            f"Simbol {self.symb}"
        )

        wait_till(start_time)
        # getting rows to calculate indicators
        table = self.__parser.get_table(100)

        indicators = Indicators(self.__settings["indicator_window"])
        step = 0
        while True:
            if step % self.__settings["print_friq"] == 0:
                print_state()
            step += 1
            indicators.calc_indicators(table, self.__settings["indicators"])
            self.__update_balances()

            borders = (
                self.__settings["strategy"]["CCI_min"],
                self.__settings["strategy"]["CCI_max"]
            )
            if table.iloc[-1]["CCI"] > borders[1]:
                print_state()
                self.__buy(2)
            elif table.iloc[-1]["CCI"] < borders[0]:
                print_state()
                self.__buy(1)

            start_time += timedelta(minutes=self.__tf_minutes)
            wait_till(start_time)
            table = pd.concat(
                [table, self.__parser.get_table(1)],
                axis=0,
                ignore_index=True
            )[-100:].reset_index(drop=True)

    # updating settings from .json file
    def __update_settings(self) -> None:
        with open(self.__settings_file, 'r') as f:
            self.__settings = json.load(f)["trader"]

    # updating balance making query to market
    def __update_balances(self) -> None:
        assets = self.client.user_asset()
        self.__first_balance = [
            float(asset['free']) for asset in assets
            if asset['asset'] == self.first_asset
        ]
        self.__first_balance = \
            self.__first_balance[0] if len(self.__first_balance) else 0
        self.__second_balance = [
            float(asset['free']) for asset in assets
            if asset['asset'] == self.second_asset
        ]
        self.__second_balance = \
            self.__second_balance[0] if len(self.__second_balance) else 0
        self.__second_balance = max(0, self.__second_balance - self.__income)

    # updating market assets precisions to use in queries
    def __update_symb_precision(self) -> None:
        symbol_info = self.client.exchange_info(symbol=self.symb)
        stepSize = 0.0
        for filter in symbol_info['symbols'][0]['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                stepSize = float(filter['stepSize'])
                self.__min_amount_first = float(filter['minQty'])
            elif filter['filterType'] == 'NOTIONAL':
                self.__min_amount_second = float(filter['minNotional'])
        self.__symbol_precision = int(round(-math.log(stepSize, 10), 0))

        with open(self.__settings["log_file"], 'a') as f:
            print(f'Symbol precision set to {self.__symbol_precision}', file=f)

    # buing to all money
    @dispatch(int)
    def __buy(self, asset_num: int) -> None:
        """
        :param asset_num: 1 if buy first asset else 2
        """
        self.__buy(
            asset_num,
            money=(
                self.__first_balance if asset_num == 2
                else self.__second_balance
            )
        )

    # buing the required amount of asset
    @dispatch(int, float)
    def __buy(self, asset_num: int, money: float) -> None:  # noqa: F811
        """
        :param asset_num: 1 if buy first asset else 2
        :param money: amount of another asset to spend
        """
        def get_income(money: int) -> None:
            income_delta = money * self.__settings["withdrawal_coef"]
            self.__income += income_delta
            money -= income_delta
            money = int(money * pow(10, self.__symbol_precision)) / \
                pow(10, self.__symbol_precision)

        if asset_num == 1:
            money = min(self.__second_balance, money) * \
                (1 - self.__settings["slippage"])
            get_income(money)
            if money < self.__min_amount_second:
                return

            with open(self.__settings["log_file"], 'a') as f:
                print(f"Sell {money} {self.second_asset}", file=f)
            _ = self.client.new_order(
                symbol=self.symb,
                # newClientOrderId="Test_0",
                side='BUY',
                type='MARKET',
                quoteOrderQty=money,
            )
        else:
            money = min(self.__first_balance, money) * \
                (1 - self.__settings["slippage"])
            get_income(money)
            if money < self.__min_amount_first:
                return

            with open(self.__settings["log_file"], 'a') as f:
                print(f"Sell {money} {self.first_asset}", file=f)
            _ = self.client.new_order(
                symbol=self.symb,
                # newClientOrderId="Test_0",
                side='SELL',
                type='MARKET',
                quantity=money,
            )
