from time import sleep

import pandas as pd


class Simulator:

    __free_money = 1000
    __active_money = 1000
    __print_friq = 1000000
    __withdrawal_coef = 0
    __income = 0
    __comission = 1e-3

    def __init__(self, df_x: pd.DataFrame, df_y: pd.DataFrame):
        """
        :param df_x: dataframe with candles
        :param df_y: dataframe with results
        """
        self.params = df_x
        self.result = df_y["Close Delta"]

    def simulate(self) -> None:
        def print_state(buy: int = None):
            print(
                f"Days: {i//12//24}, "
                f"First: {int(self.__active_money)}, "
                f"Second: {int(self.__free_money)}, "
                f"Price: {int(row['Close'])}, "
                f"Income: {self.__income}, "
                f"Volume: {row['Volume usd'] / 10000}, ",
                "" if buy is None else f"Buy: {buy}"
            )

        priv_price = self.params['Close'].iloc[0]

        for i, row in self.params.iterrows():
            if i % self.__print_friq == 0:
                print_state()
                sleep(0.05)

            new_active_money = self.__active_money * row['Close'] / priv_price
            if row['Close'] > priv_price:
                inc_bonus = (new_active_money - self.__active_money) * \
                    self.__withdrawal_coef
                self.__buy(-1 * inc_bonus)
                self.__income += inc_bonus
                self.__free_money -= inc_bonus
            self.__active_money = new_active_money

            money = (self.__free_money + self.__active_money)
            if money <= 0.001:
                print("No money!!!", i, "staps gone.")
                return

            # operations = pd.DataFrame(
            #     columns=['usd', 'cripto', 'buy', 'price']
            # )
            if (row['CCI'] > 100 and self.__active_money > 0):
                print_state(-1 * self.__active_money)
                self.__buy(-1 * self.__active_money)

            elif (row['CCI'] < -100 and self.__free_money > 0):
                print_state(self.__free_money)
                self.__buy(self.__free_money)

            priv_price = row['Close']

    def __buy(self, money: float) -> None:
        """
        :param money: how much crypto to buy
        """
        if money > 0:
            money = min(self.__free_money, money)
            self.__free_money -= money
            self.__active_money += money * (1 - self.__comission)
        else:
            money = max(-self.__active_money, money)
            self.__free_money -= money * (1 - self.__comission)
            self.__active_money += money
