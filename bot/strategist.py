import json
import pandas as pd

# from sklearn.linear_model import SGDRegressor


class Strategy:
    # load settings and fit models here
    def __init__(self):
        pass

    # function makes prediction using table
    # prediction is in range (-1, 1) where
    # 0 - now is normal price
    # 1 - curent price is too high (sell)
    # -1 - curent price is too low (buy)
    def predict(self, table: pd.DataFrame) -> float:
        """
        :param table: dataframe with indicators to make prediction
        """
        pass


# classic cci stratagy
class CCI_Strategy(Strategy):
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
    def __init__(self):
        with open('settings.json', 'r') as f:
            self.__settings = json.load(f)['strategist']['SGD']

    def predict(self, table: pd.DataFrame) -> float:
        pass


def get_strategy(strategy_name: str) -> Strategy:
    strategy_map = {
        "CCI": CCI_Strategy,
        "ML": SGD_Strategy,
    }
    return strategy_map[strategy_name]()
