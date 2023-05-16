import numpy as np
import pandas as pd

from bot.exceptions import WrongIndicator

class Indicators:

    # all available indicators
    ind_list = ["ADI", "CCI", "MACD", "MFI", "OBV", "PVT", "RSI"]

    def __init__(self, window: int = 12):
        self.window = window

    # adds indicators from the list and indicators for their calculation
    def calc_indicators(self, df: pd.DataFrame, indicators: list =  ["ALL"], drop_first: bool = False) -> None:
        """
        :param df: dataframe to calculate indicators
        :param indicators: list of needed indicators
        :param drop_first: flag to drop first probably uncorrect columns
        """
        if "ALL" in indicators:
            indicators = self.ind_list.copy()

        diff = set(indicators).difference(set(self.ind_list))
        if diff:
            raise WrongIndicator(f'No such indicators: {list(diff)}')

        for indicator in indicators:
            func_name = f'calc_{indicator}'
            if hasattr(self, func_name):
                getattr(self, func_name)(df)

        if drop_first:
            df.drop(df.index[ : self.window * 4], inplace=True)
            df.reset_index(drop=True, inplace=True)

    # -------------------------------------------------------------------------- Main indicators

    # index ADI + ADIEMA + CLV
    def calc_ADI(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_CLV(df)
        df['ADI'] = 0
        for i in range(self.window):
            df['ADI'] += df['CLV'].shift(i).fillna(0)
        self.__calc_EMA(df, 'ADI')

    # index CCI + SMA + MAD + TP
    def calc_CCI(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_MAD(df)
        df['CCI'] = (df['TP'] - df['SMA']) / df['MAD'] / 0.015

    # index MACD + MACDEMA
    def calc_MACD(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_EMA(df, 'Close')
        EMA1 = df['CloseEMA'].copy()
        df.drop(['CloseEMA'], axis=1, inplace=True)
        self.__calc_EMA(df, 'Close', self.window * 2)
        df.rename(columns={'CloseEMA' : 'MACD'}, inplace=True)
        df['MACD'] = EMA1 - df['MACD']
        self.__calc_EMA(df, 'MACD', self.window * 3 // 4)

    # index MFI + TP + MR
    def calc_MFI(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_MR(df)
        df['MFI'] = 100 - 100 / (1 + df['MR'])

    # index OBV + OBVCA
    def calc_OBV(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        df['OBV'] = 0
        for i in range(self.window):
            close_delta = np.sign(df['Close'].shift(i).fillna(0) - df['Close'].shift(i + 1).fillna(0))
            df['OBV'] += close_delta * df['Volume coin'].shift(i).fillna(0)
        self.__calc_CA(df, 'OBV')

    # index PVT + PVTCA
    def calc_PVT(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        close_priv = df['Close'].shift(1).fillna(0)
        df_temp =  df['Volume coin'] * (df['Close'] - close_priv) / close_priv
        df['PVT'] = 0
        for i in range(self.window):
            df['PVT'] += df_temp.shift(i).fillna(0)
        self.__calc_CA(df, 'PVT')

    # index RSI + RS + EMA + EMAU + EMAD
    def calc_RSI(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_EMAUD(df)
        df['RS'] = df['EMAU'] / (df['EMAD'] + 1e-5)
        df['RSI'] = 100 * df['EMAU'] / (df['EMAU'] + df['EMAD'])

    # -------------------------------------------------------------------------- Moving averages

    # index *CA
    def __calc_CA(self, df: pd.DataFrame, param_name: str) -> None:
        """
        :param df: dataframe to calculate indicator
        :param param_name: param to calculate camulative avarage
        """
        ca_name = param_name + 'CA'
        df[ca_name] = 0
        for i in range(self.window):
            df[ca_name] += df[param_name].shift(i).fillna(0)
        df[ca_name] /= self.window

    # index *EMA
    def __calc_EMA(self, df: pd.DataFrame, param_name: str, window: int = None) -> None:
        """
        :param df: dataframe to calculate indicator
        :param param_name: param to calculate camulative avarage
        """
        if window is None:
            window = self.window
        alpha = 2 / (1 + window)
        ema_name = param_name + 'EMA'
        df_temp = df[param_name]
        df[ema_name] = 0
        coef = 0
        for shift in range(window):
            df[ema_name] += df_temp.shift(shift).fillna(0) * ((1 - alpha) ** shift)
            coef += (1 - alpha) ** shift
        df[ema_name] /= coef


    # -------------------------------------------------------------------------- Auxiliary indicators

    # index CLV
    def __calc_CLV(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'CLV' in df.columns:
            return
        df['CLV'] = df['Volume coin'] * (2 * df['Close'] - df['Low'] - df['High']) / (df['High'] - df['Low'])

    # index EMA + EMAU + EMAD
    def __calc_EMAUD(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'EMA' in df.columns:
            return
        # calc coef
        df['EMA'] = (df['Close'] - df['Close'].shift(1).fillna(0))
        df['EMAU'] = df['EMA']
        df['EMAU'][df['EMAU'] < 0] = 0
        df['EMAD'] = -df['EMA']
        df['EMAD'][df['EMAD'] < 0] = 0
        for index in ['EMA', 'EMAU', 'EMAD']:
            self.__calc_EMA(df, index)
            df[index] = df[index + 'EMA']
            df.drop([index + 'EMA'], axis=1, inplace=True)

    # index MAD + SMA + TP
    def __calc_MAD(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'MAD' in df.columns:
            return
        self.__calc_SMA(df)
        df_temp = (df['TP'] - df['SMA'] + 0.1**10).abs()
        df['MAD'] = df_temp
        for i in range(1, self.window):
            df['MAD'] += df_temp.shift(i).fillna(0)
            df['MAD'].iloc[i-1] /= i
        df['MAD'].iloc[self.window:] /= self.window

    # index MR
    def __calc_MR(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'MR' in df.columns:
            return
        self.__calc_TP(df)
        PMF = df['TP'] * df['Volume coin']
        NMF = PMF.copy()
        TP_delta = df['TP'] - df['TP'].shift(1).fillna(0)
        PMF[TP_delta < 0] = 0
        NMF[TP_delta >= 0] = 0
        PMFS = PMF
        NMFS = NMF
        for i in range(1, self.window):
            PMFS += PMF.shift(i).fillna(0)
            NMFS += NMF.shift(i).fillna(0)
        df['MR'] = PMFS / NMFS

    # index SMA + TP
    def __calc_SMA(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'SMA' in df.columns:
            return
        self.__calc_TP(df)
        df['SMA'] = df['TP']
        for i in range(1, self.window):
            df['SMA'] += df['TP'].shift(i).fillna(0)
            df['SMA'].iloc[i-1] /= i
        df['SMA'].iloc[self.window:] /= self.window

    # index TP
    def __calc_TP(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'TP' in df.columns:
            return
        df['TP'] = (df['Low'] + df['Close'] + df['High']) / 3
