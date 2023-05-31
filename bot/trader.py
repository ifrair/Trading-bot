from bot.dataset_parser import Parser
from bot.indicators import Indicators
from bot.strategist import get_strategy
from bot.utiles import wait_till, tf_to_minutes, time_to_int

from binance.spot import Spot
from datetime import datetime, timedelta
from multipledispatch import dispatch

import json
import math


class Trader:
    __first_balance = 0.0
    __second_balance = 0.0
    # money to save (in second asset by default)
    __income = 0.0

    def __init__(
        self,
        api_key: str,
        sec_key: str,
        first_asset: str = None,
        second_asset: str = None,
        tf: str = None,
        timezone: int = 0,
        settings_file_path: str = "settings.json",
    ):
        """
        :param api_key: api key to market
        :param sec_key: secure key to market
        :param first_asset: first asset of trading pair
        :param second_asset: second asset of trading pair
        :param tf: candle timeframe
        :param settings_file_path: path for settings.json
        """
        self.client = Spot(
            api_key,
            sec_key,
            base_url="https://api.binance.com",
            # proxies={ 'https': creds.proxy }
        )
        self.__settings_file = settings_file_path
        self.first_asset = first_asset
        self.__is_first_asset_given = (first_asset is not None)
        self.second_asset = second_asset
        self.__is_second_asset_given = (second_asset is not None)
        self.__is_tf_given = (tf is not None)
        if self.__is_tf_given:
            self.tf = tf
            self.__tf_minutes = tf_to_minutes(tf)
        self.__update_settings()
        # cleaning logs
        f = open(self.__settings["log_file"], 'w')
        f.close()
        self.__parser = Parser(self.symb, self.tf, timezone)

    def trade(self) -> None:
        """Function to start infinite loop to trade every timeframe minutes"""
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
        strategy = get_strategy(self.__settings['strategy'])
        indicators = Indicators(self.__settings['indicator_window'])
        table = self.__parser.get_table(1)
        self.__update_symb_precision(
            table.iloc[-1]['Close']
        )

        # updating start time
        start_time = datetime.now() + timedelta(minutes=self.__tf_minutes)
        start_time -= timedelta(
            minutes=time_to_int(start_time) // 60000 % self.__tf_minutes,
        )
        start_time -= timedelta(seconds=start_time.second)

        print_state(
            f"Start time: {start_time}, "
            f"Timeframe: {self.__tf_minutes} mins, "
            f"Simbol: {self.symb}, "
            f"Strategy: {self.__settings['strategy']}"
        )

        step = 0
        while True:
            step += 1
            self.__update_balances()
            if step == 1:
                print_state()
            wait_till(start_time)
            # getting rows to calculate indicators
            table = self.__parser.get_table(
                self.__settings['num_stored_rows']
            )
            indicators.calc_indicators(
                table,
                self.__settings['indicators'],
                drop_first=True
            )

            prediction = strategy.predict(table)
            if prediction > 0:
                self.__buy(2, prediction * self.__first_balance)
            elif prediction < 0:
                self.__buy(1, -prediction * self.__second_balance)

            if step % self.__settings['refresh_friq'] == 0:
                self.__update_symb_precision(table.iloc[-1]['Close'])
                print_state()

            self.__update_settings()

            start_time += timedelta(minutes=self.__tf_minutes)

    def __update_settings(self) -> None:
        """Updating settings from .json file"""
        with open(self.__settings_file, 'r') as f:
            self.__settings = json.load(f)['trader']
        if not self.__is_first_asset_given:
            self.first_asset = self.__settings['first_asset']
        if not self.__is_second_asset_given:
            self.second_asset = self.__settings['second_asset']
        if not self.__is_tf_given:
            self.tf = self.__settings['timeframe']
            self.__tf_minutes = tf_to_minutes(self.tf)
        self.symb = self.first_asset + self.second_asset

    def __update_balances(self) -> None:
        """Updating balance making query to market"""
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

    def __update_symb_precision(self, price: float) -> None:
        """
        Updating market assets precisions to use in queries
        :param price: curent symbol price
        """
        symbol_info = self.client.exchange_info(symbol=self.symb)
        stepSize = 0.0
        self.__min_amount_first = -1
        self.__min_amount_second = -1
        for filter in symbol_info['symbols'][0]['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                stepSize = float(filter['stepSize'])
                minQty = float(filter['minQty'])
                self.__min_amount_first = max(
                    minQty,
                    self.__min_amount_first
                )
                self.__min_amount_second = max(
                    minQty * price * 2,
                    self.__min_amount_second
                )
            elif filter['filterType'] == 'NOTIONAL':
                minNotional = float(filter['minNotional'])
                self.__min_amount_second = max(
                    minNotional,
                    self.__min_amount_second
                )
                self.__min_amount_first = max(
                    minNotional / price * 2,
                    self.__min_amount_first
                )
        self.__symbol_precision = int(round(-math.log(stepSize, 10), 0))

        with open(self.__settings['log_file'], 'a') as f:
            print(
                f"Symbol precision set to {self.__symbol_precision}",
                f"Minimal {self.first_asset} set to "
                f"{self.__min_amount_first}",
                f"Minimal {self.second_asset} set to "
                f"{self.__min_amount_second}",
                file=f,
                sep=',\n'
            )

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
            money *= (1 - self.__settings['slippage'])
            income_delta = money * self.__settings['withdrawal_coef']
            self.__income += income_delta
            money -= income_delta
            precision_coef = pow(10, self.__symbol_precision)
            money = int(money * precision_coef) / precision_coef
            return money

        if asset_num == 1:
            money = min(self.__second_balance, money)
            money = get_income(money)
            if money < self.__min_amount_second:
                return

            with open(self.__settings['log_file'], 'a') as f:
                print(
                    f"Time: {datetime.now()}, ",
                    f"Sell {money} {self.second_asset}",
                    file=f,
                )

            _ = self.client.new_order(
                symbol=self.symb,
                # newClientOrderId="Test_0",
                side='BUY',
                type='MARKET',
                quoteOrderQty=money,
            )
            self.__second_balance -= money
        else:
            money = min(self.__first_balance, money)
            money = get_income(money)
            if money < self.__min_amount_first:
                return

            with open(self.__settings['log_file'], 'a') as f:
                print(
                    f"Time: {datetime.now()}, ",
                    f"Sell {money} {self.first_asset}",
                    file=f,
                )

            _ = self.client.new_order(
                symbol=self.symb,
                # newClientOrderId="Test_0",
                side='SELL',
                type='MARKET',
                quantity=money,
            )
            self.__first_balance -= money
