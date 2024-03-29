import numpy as np
import pandas as pd

from bot.exceptions import WrongIndicator


class Indicators:
    # all available indicators
    ind_list = ["ADI", "CCI", "MACD", "MFI", "OBV", "PVT", "RSI"]

    eps = 1e-4

    def __init__(self, window: int = 12):
        """
        :param window: size of window to indicators calculation
        """
        self.window = window

    def calc_indicators(
        self,
        df: pd.DataFrame,
        indicators: list = ["ALL"],
        drop_first: bool = False
    ) -> None:
        """
        Adds indicators from list and
        auxiliary indicators for their calculation
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
            df.drop(df.index[: self.window * 4], inplace=True)
            df.reset_index(drop=True, inplace=True)

    # ---------------------------------------------------- Main indicators

    def calc_ADI(self, df: pd.DataFrame) -> None:
        """
        index ADI + ADIEMA + CLV
        :param df: dataframe to calculate indicator
        """
        self.__calc_CLV(df)
        df['ADI'] = df['CLV'].rolling(window=self.window).sum()
        self.__calc_EMA(df, 'ADI')

    def calc_CCI(self, df: pd.DataFrame) -> None:
        """
        index CCI + SMA + MAD + TP
        :param df: dataframe to calculate indicator
        """
        self.__calc_MAD(df)
        df['CCI'] = (df['TP'] - df['SMA']) / (df['MAD'] + self.eps) / 0.015

    def calc_MACD(self, df: pd.DataFrame) -> None:
        """
        index MACD + MACDEMA
        :param df: dataframe to calculate indicator
        """
        self.__calc_EMA(df, 'Close')
        EMA1 = df['CloseEMA'].copy()
        df.drop(['CloseEMA'], axis=1, inplace=True)
        self.__calc_EMA(df, 'Close', self.window * 2)
        df.rename(columns={'CloseEMA': 'MACD'}, inplace=True)
        df['MACD'] = EMA1 - df['MACD']
        self.__calc_EMA(df, 'MACD', self.window * 3 // 4)

    def calc_MFI(self, df: pd.DataFrame) -> None:
        """
        index MFI + TP + MR
        :param df: dataframe to calculate indicator
        """
        self.__calc_MR(df)
        df['MFI'] = 100 - 100 / (1 + df['MR'])

    def calc_OBV(self, df: pd.DataFrame) -> None:
        """
        index OBV + OBVCA
        :param df: dataframe to calculate indicator
        """
        df['OBV'] = 0
        for i in range(self.window):
            close_delta = np.sign(
                df['Close'].shift(i).fillna(0) -
                df['Close'].shift(i + 1).fillna(0)
            )
            df['OBV'] += close_delta * df['Volume coin'].shift(i).fillna(0)
        self.__calc_CA(df, 'OBV')

    def calc_PVT(self, df: pd.DataFrame) -> None:
        """
        index PVT + PVTCA
        :param df: dataframe to calculate indicator
        """
        close_priv = df['Close'].shift(1).fillna(0)
        df_temp = df['Volume coin'] * (df['Close'] - close_priv) / close_priv
        df['PVT'] = df_temp.rolling(window=self.window).sum().fillna(0)
        self.__calc_CA(df, 'PVT')

    def calc_RSI(self, df: pd.DataFrame) -> None:
        """
        index RSI + RS + EMA + EMAU + EMAD
        :param df: dataframe to calculate indicator
        """
        self.__calc_EMAUD(df)
        df['RS'] = df['EMAU'] / (df['EMAD'] + self.eps)
        df['RSI'] = 100 * df['EMAU'] / (df['EMAU'] + df['EMAD'] + self.eps)

    # ---------------------------------------------------- Moving averages

    def __calc_CA(self, df: pd.DataFrame, param_name: str) -> None:
        """
        index *CA
        :param df: dataframe to calculate indicator
        :param param_name: param to calculate camulative avarage
        """
        ca_name = param_name + 'CA'
        rolling = df[param_name].rolling(window=self.window)
        df[ca_name] = rolling.sum().fillna(0)
        df[ca_name] /= self.window

    def __calc_EMA(
        self,
        df: pd.DataFrame,
        param_name: str,
        window: int = None
    ) -> None:
        """
        index *EMA
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
            df[ema_name] += \
                df_temp.shift(shift).fillna(0) * ((1 - alpha) ** shift)
            coef += (1 - alpha) ** shift
        df[ema_name] /= coef

    # ---------------------------------------------------- Auxiliary indicators

    def __calc_CLV(self, df: pd.DataFrame) -> None:
        """
        index CLV
        :param df: dataframe to calculate indicator
        """
        if 'CLV' in df.columns:
            return
        df['CLV'] = df['Volume coin'] * \
            (2 * df['Close'] - df['Low'] - df['High']) / \
            (df['High'] - df['Low'] + self.eps)

    def __calc_EMAUD(self, df: pd.DataFrame) -> None:
        """
        index EMA + EMAU + EMAD
        :param df: dataframe to calculate indicator
        """
        if 'EMA' in df.columns:
            return
        # calc coef
        df['EMA'] = (df['Close'] - df['Close'].shift(1).fillna(0))
        df['EMAU'] = df['EMA']
        df.loc[df['EMAU'] < 0, ['EMAU']] = 0
        df['EMAD'] = -df['EMA']
        df.loc[df['EMAD'] < 0, ['EMAD']] = 0
        for index in ['EMA', 'EMAU', 'EMAD']:
            self.__calc_EMA(df, index)
            df[index] = df[index + 'EMA']
            df.drop([index + 'EMA'], axis=1, inplace=True)

    def __calc_MAD(self, df: pd.DataFrame) -> None:
        """
        index MAD + SMA + TP
        :param df: dataframe to calculate indicator
        """
        if 'MAD' in df.columns:
            return
        self.__calc_SMA(df)
        df_temp = (df['TP'] - df['SMA'] + 0.1**10).abs()
        df['MAD'] = df_temp.rolling(window=self.window).sum().fillna(0)
        df['MAD'] /= self.window

    def __calc_MR(self, df: pd.DataFrame) -> None:
        """
        index MR
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
        PMFS = PMF.rolling(window=self.window).sum().fillna(0)
        NMFS = NMF.rolling(window=self.window).sum().fillna(0)
        df['MR'] = PMFS / np.maximum(NMFS, self.eps)

    def __calc_SMA(self, df: pd.DataFrame) -> None:
        """
        index SMA + TP
        :param df: dataframe to calculate indicator
        """
        if 'SMA' in df.columns:
            return
        self.__calc_TP(df)
        df['SMA'] = df['TP'].rolling(window=self.window).sum().fillna(0)
        df['SMA'] /= self.window

    def __calc_TP(self, df: pd.DataFrame) -> None:
        """
        index TP
        :param df: dataframe to calculate indicator
        """
        if 'TP' in df.columns:
            return
        df['TP'] = (df['Low'] + df['Close'] + df['High']) / 3
