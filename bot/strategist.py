import json
import pandas as pd

from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_absolute_error as mae
from sklearn.preprocessing import StandardScaler

from bot.utiles import time_to_int
from bot.indicators import Indicators


class Strategy:
    """pattern strategy class"""
    window: int = 10
    def __init__(self):
        """load settings and fit models here"""
        pass

    def predict(self, table: pd.DataFrame) -> float:
        """
        function makes prediction using table
        prediction is in range (-1, 1) where
        0 - now is normal price
        1 - curent price is too high (sell)
        -1 - curent price is too low (buy)
        :param table: dataframe with indicators to make prediction
        """
        pass


class ADI_Strategy(Strategy):
    """classic ADI stratagy"""
    def predict(self, table: pd.DataFrame) -> float:
        """
        :param table: dataframe with indicators to make predictions
        """
        adi = table['ADI'].iloc[-1]
        adi_priv = table['ADI'].iloc[-2]
        adiema = table['ADIEMA'].iloc[-1]
        adiema_priv = table['ADIEMA'].iloc[-2]

        if adi < adiema and adi_priv < adiema_priv:
            return -1
        elif adi > adiema and adi_priv > adiema_priv:
            return 1
        return 0


class CCI_Strategy(Strategy):
    """classic cci stratagy"""
    def __init__(self):
        with open('settings.json', 'r') as f:
            self.__settings = json.load(f)['strategist']['CCI']

    def predict(self, table: pd.DataFrame) -> float:
        """
        :param table: dataframe with indicators to make predictions
        """
        # print(table)
        cci_min = self.__settings['CCI_min']
        cci_max = self.__settings['CCI_max']
        cci = table['CCI'].iloc[-1]

        if cci > cci_max:
            return min(1, cci / 100)
        elif cci < cci_min:
            return max(-1, cci / 100)
        return 0


class SGD_Strategy(Strategy):
    """SGD stratagy"""
    def __init__(self):
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            self.__settings = settings['strategist']['SGD']
            self.__trading_settings = settings['trader']
        table = pd.read_csv(self.__settings['fit_table'])[-20000: -10000]

        for col in ['Open time', 'Close time', 'Middle time']:
            table[col] = table[col].apply(time_to_int)

        Indicators(
            self.__trading_settings['indicator_window'],
        ).calc_indicators(
            table,
            indicators=self.__trading_settings['indicators'],
            drop_first=True,
        )

        Y_table = table['Close Delta']
        table = table.drop(columns=['Next Close', 'Close Delta']).reset_index(drop=True)

        self.scaler = StandardScaler()
        table = pd.DataFrame(self.scaler.fit_transform(table))
        self.scaler_Y = StandardScaler()
        Y_table = pd.DataFrame(self.scaler_Y.fit_transform(pd.DataFrame(Y_table)))

        self.model = SGDRegressor().fit(
            table,
            Y_table,
        )
        # print(table)
        # print(table, self.model.coef_)
        # print(pd.Series(self.model.predict(table)), Y_table)

    def predict(self, table_orig: pd.DataFrame) -> float:
        """
        :param table: dataframe with indicators to make predictions
        """
        table = table_orig.copy()
        for col in ['Open time', 'Close time', 'Middle time']:
            table[col] = table[col].apply(time_to_int)

        table = pd.DataFrame(self.scaler.transform(table))

        prediction = self.model.predict(table.iloc[-2:-1])[-1]
        result = -prediction * self.__settings['order_size_coef']

        return max(min(result, 1), -1)


def get_strategy(strategy_name: str) -> Strategy:
    """get strategy object by name"""
    strategy_map = {
        "ADI": ADI_Strategy,
        "CCI": CCI_Strategy,
        "SGD": SGD_Strategy,
    }
    return strategy_map[strategy_name]()
