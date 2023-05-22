import json
import pandas as pd

# from sklearn.linear_model import SGDRegressor


class Strategy:
    """pattern strategy class"""
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
        adi = table.iloc[-1]['ADI']
        adi_priv = table.iloc[-2]['ADI']
        adiema = table.iloc[-1]['ADIEMA']
        adiema_priv = table.iloc[-2]['ADIEMA']

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
        cci_min = self.__settings['CCI_min'],
        cci_max = self.__settings['CCI_max'],
        cci = table.iloc[-1]['CCI']

        if cci > cci_max:
            return min(1, cci / 100)
        elif cci < cci_min:
            return max(-1, cci / 100)
        return 0

class SGD_Strategy(Strategy):
    """SGD stratagy"""
    def __init__(self):
        with open('settings.json', 'r') as f:
            self.__settings = json.load(f)['strategist']['SGD']

    def predict(self, table: pd.DataFrame) -> float:
        """
        :param table: dataframe with indicators to make predictions
        """
        pass


def get_strategy(strategy_name: str) -> Strategy:
    """get strategy object by name"""
    strategy_map = {
        "ADI": ADI_Strategy,
        "CCI": CCI_Strategy,
        "ML": SGD_Strategy,
    }
    return strategy_map[strategy_name]()
