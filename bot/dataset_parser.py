from bot.exceptions import ResponseError, RequestError
from bot.utiles import tf_to_minutes, time_to_int

from datetime import datetime, timedelta
from multipledispatch import dispatch
# from pandarallel import pandarallel
from time import sleep

import copy
import json
import pandas as pd
import requests
import time


class Parser:

    __settings_file = "settings.json"

    def __init__(
        self,
        symb: str = "BTCUSDT",
        tf: str = "1m",
        timezone: int = 0,
        ignore_gaps: bool = False,
    ):
        """
        :param symb: trading pair
        :param tf: candle timeframe
        """
        self.symb = symb
        self.tf = tf
        self.__tf_minutes = tf_to_minutes(tf)
        self.timezone = timezone
        self.ignore_gaps = ignore_gaps
        self.__update_settings()
        f = open(self.__settings['log_file'], 'w')
        f.close()
        # pandarallel.initialize()

    @dispatch(str, str)
    def get_table(self, start_t: str, end_t: str) -> pd.DataFrame:
        """
        :param start_t: start time
        :param end_t: end time
        """
        return self.get_table(
            start_t,
            (time_to_int(end_t) - 60000 - time_to_int(start_t)) // self.__tf_minutes // 60000
        )

    @dispatch(int)
    def get_table(self, limit: int) -> pd.DataFrame:
        """
        :param limit: num candles from start
        """
        return self.get_table(
            str(datetime.now() - timedelta(minutes=limit*self.__tf_minutes)),
            limit,
        )

    @dispatch(str, int)
    def get_table(self, start_t: str, limit: int) -> pd.DataFrame:
        """
        :param start_t: start time
        :param limit: num candles from start
        """
        with open(self.__settings['log_file'], 'a') as f:
            print("Start time:", start_t, "Limit: ", limit, file=f)
        resp = self.__get_table(time_to_int(start_t) - self.timezone * 60 * 60000, limit)
        resp.sort_values(0, inplace=True, ignore_index = True)

        df = pd.DataFrame()
        df['Open'] = resp[1].apply(lambda x: float(x))
        df['Close'] = resp[4].apply(lambda x: float(x))
        df['Middle'] = (df['Open'] + df['Close']) / 2
        df['Low'] = resp[3].apply(lambda x: float(x))
        df['High'] = resp[2].apply(lambda x: float(x))
        df['Volume coin'] = resp[5].apply(lambda x: float(x))
        df['Volume usd'] = resp[7].apply(lambda x: float(x))
        df['Open time'] = pd.to_datetime(resp[0], unit='ms')
        df['Close time'] = pd.to_datetime(resp[6], unit='ms')
        df['Middle time'] = (df['Close time'] - df['Open time']) / 2 + df['Open time']

        # prediction
        df['Next Close'] = copy.deepcopy(df['Close']).shift(-1)
        df['Next Close'].iloc[-1] = copy.deepcopy(df['Close'].iloc[-1])
        df['Close Delta'] = (df['Next Close'] - df['Close']) / df['Close']

        return df

    def __get_table(self, start_t: int, limit: int) -> pd.DataFrame:
        # round up
        start_t //= (self.__tf_minutes * 60000)
        start_t *= (self.__tf_minutes * 60000)
        with open(self.__settings['log_file'], 'a') as f:
            print("Start from:", start_t, ", Num rows:", limit, file=f)
        res = pd.DataFrame()
        while limit > 0:
            query_second = datetime.now()
            limit_delta = min(self.__settings['batch_size'], limit)
            resp = self.__get_response(start_t, limit_delta)
            res = pd.concat([res, pd.DataFrame(resp.json())], axis=0, ignore_index=True)
            limit -= limit_delta
            start_t += limit_delta * self.__tf_minutes * 60000
            time_delta = datetime.now() - query_second
            with open(self.__settings['log_file'], 'a') as f:
                print(time_delta, limit, file=f)
            time.sleep(max(0, 0.5 - time_delta.microseconds / 1000000))
        return res

    def __get_response(self, start_t: int, limit: int) -> requests.models.Response:
        tries = 5
        secs = 1
        while tries > 0:
            base = "https://api.binance.com"
            path = "/api/v3/klines"
            url = base + path
            params = {
                'symbol': self.symb,
                'limit': str(limit),
                'interval': self.tf,
                'startTime': str(start_t),
                'endTime': str(start_t + limit * self.__tf_minutes * 60000),
            }
            r = requests.get(url, params=params)
            if r.status_code == 200:
                sz = pd.DataFrame(r.json()).shape[0]
                if not self.ignore_gaps and pd.DataFrame(r.json()).shape[0] != limit:
                    raise ResponseError(f'Get klines response size is {sz}, Limit is {limit}')
                return r
            elif r.status_code >= 500:
                error_code = str(r.status_code)
                with open(self.__settings['log_file'], 'a') as f:
                    print(f'\n\n\nERROR!!!!\n{error_code} \n{r.json()}\n\n', file=f)
                sleep(secs)
                secs *= 1.5
                tries -= 1
            else:
                raise RequestError(f'{r.status_code}\n{r.json()}')
        raise ResponseError(f'{error_code}\nNo response from market')

    def __update_settings(self):
        with open(self.__settings_file, 'r') as f:
            self.__settings = json.load(f)["parser"]
