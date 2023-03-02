from dateutil.parser import parse as dt_parse
from datetime import datetime
from multipledispatch import dispatch
from pandarallel import pandarallel

import copy
import numpy as np
import pandas as pd
import requests
import time


class Parser:

    __batch_size: int = 1000

    def __init__(self, symb: str = "BTCUSDT", tf: str = "1m") :
        """
        :param symb: trading pair
        :param tf: candle timeframe
        """
        self.symb = symb
        self.tf = tf
        coef_mapping = {
            "m": 1,
            "h": 60,
            "d": 60 * 24,
            "w": 60 * 24 * 7,
            "M": 60 * 24 * 30,
        }
        self.__tf_minutes = int(tf[:-1]) * coef_mapping[tf[-1]]
        pandarallel.initialize()

    @dispatch(str, str)
    def get_table(self, start_t: str, end_t: str) -> pd.DataFrame:
        """
        :param start_t: start time
        :param end_t: end time
        """
        return self.get_table(
            start_t,
            (Parser.__time_to_int(end_t) - 60000 - Parser.__time_to_int(start_t)) // self.__tf_minutes // 60000
        )

    @dispatch(str, int)
    def get_table(self, start_t: str, limit: int) -> pd.DataFrame:
        """
        :param start_t: start time
        :param limit: num candles from start
        """
        resp = self.__get_table(Parser.__time_to_int(start_t), limit)
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
        df['Close Delta'] = df['Next Close'] - df['Close']

        # index cci
        N = 12
        df['TP'] = (df['Low'] + df['Close'] + df['High']) / 3

        def calc_sma(time):
            return df[df['Open time'] <= time].tail(N)['TP'].mean()

        def calc_mad(time):
            rows = df[df['Open time'] <= time].tail(N)
            return (rows['TP'] - rows['SMA'] + 0.1**10).abs().mean()

        query_second = datetime.now()
        df['SMA'] = df['Open time'].parallel_apply(lambda time: calc_sma(time))
        df['MAD'] = df['Open time'].parallel_apply(lambda time: calc_mad(time))
        df['CCI'] = df.parallel_apply(lambda row: (row['TP'] - row['SMA']) / row['MAD'] / 0.015 , axis=1)
        print(datetime.now() - query_second)
        #time.sleep(100000)
        return df

    def __get_table(self, start_t: int, limit: int) -> pd.DataFrame:
        print("Start from:", start_t, ", Num rows:", limit)
        res = pd.DataFrame()
        while limit > 0:
            query_second = datetime.now()
            limit_delta = min(self.__batch_size, limit)
            resp = self.__get_response(start_t, limit_delta)
            res = pd.concat([res, pd.DataFrame(resp.json())], axis=0, ignore_index=True)
            limit -= limit_delta
            start_t += limit_delta * self.__tf_minutes * 60000
            time_delta = datetime.now() - query_second
            print(time_delta, limit)
            time.sleep(max(0, 0.5 - time_delta.microseconds / 1000000))
        return res

    def __time_to_int(time: str) -> int:
        dt = dt_parse(time)
        epoch = datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds() * 1000)

    def __get_response(self, start_t: int, limit: int) -> requests.models.Response:
        base = "https://fapi.binance.com"
        path = "/fapi/v1/klines"
        url = base + path
        params = {
            'symbol': self.symb,
            'limit': str(self.__batch_size),
            'interval': self.tf,
            'startTime': str(start_t),
            'endTime': str(start_t + limit * self.__tf_minutes * 60000),
        }
        r = requests.get(url, params=params)
        if r.status_code != 200:
            print(r)
            exit(0)
        return r
