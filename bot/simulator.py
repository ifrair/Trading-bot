from time import sleep

import numpy as np
import pandas as pd


class Simulator:

    __free_money = 1000
    __active_money = 1000
    __print_friq = 1000000
    # __risk_coef = 1000000
    __withdrawal_coef = 0
    __income = 0
    __comission = 0.001

    def __init__(self, df_x: pd.DataFrame, df_y: pd.DataFrame):
        """
        :param df_x: dataframe with candles
        :param df_y: dataframe with results
        """
        self.params = df_x
        self.result = df_y["Close Delta"]

    def simulate(self) -> None:
        priv_price = self.params['Close'].iloc[0]

        for i, row in self.params.iterrows():
            if i % self.__print_friq == 0:
                print(f'Days: {i//12//24}, USD: {int(self.__free_money)}, Cripto: {int(self.__active_money)}, Price: {int(row["Close"])}, Income: {int(self.__income)}')
                sleep(0.05)

            new_active_money = self.__active_money * row['Close'] / priv_price
            if row['Close'] > priv_price:
                inc_bonus = (new_active_money - self.__active_money) * self.__withdrawal_coef
                self.__buy(-1 * inc_bonus)
                self.__income += inc_bonus
                self.__free_money -= inc_bonus
            self.__active_money = new_active_money
            # self.__buy((self.__free_money - self.__active_money) / 2)

            money = (self.__free_money + self.__active_money) # *  self.__risk_coef
            if money <= 0:
                print("No money!!!", i, "staps gone.")
                return

            operations = pd.DataFrame(columns=['usd', 'cripto', 'buy', 'price'])
            # if i != 0 and abs(self.params['CCI'].iloc[i-1]) > 100 and abs(row['CCI']) < 100:
            #     self.__buy(-1 * np.sign(row['CCI']) * money)
            #     print(i, self.params['CCI'].iloc[i-1], row['CCI'])

            if (row['CCI'] > 100 and self.__active_money > 0):
                
                print(f'Days: {i//12//24}, Buy: {-1 * self.__active_money}, USD: {int(self.__free_money)}, Cripto: {int(self.__active_money)}, Price: {(row["Close"])}, V: {row["Volume usd"] / 10000}')
                self.__buy(-1 * self.__active_money)

            elif (row['CCI'] < -100 and self.__free_money > 0):

                print(f'Days: {i//12//24}, Buy: {self.__free_money}, USD: {int(self.__free_money)}, Cripto: {int(self.__active_money)}, Price: {(row["Close"])}, V: {row["Volume usd"] / 10000}')
                self.__buy(self.__free_money)
            # elif (row['CCI'] > 100 and self.params['CCI'].iloc[i-1] > 100 and row['CCI'] > self.params['CCI'].iloc[i-1] and row['CCI'] > 0):
            #     self.__buy(-1 * self.__active_money * 0.2)

            # elif (row['CCI'] < -100 and self.params['CCI'].iloc[i-1] < -100 and row['CCI'] < self.params['CCI'].iloc[i-1]):
            #     self.__buy(self.__free_money * 0.2)



            priv_price = row['Close']
            # 1650 25  1790 20  2055 10  705 100

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
