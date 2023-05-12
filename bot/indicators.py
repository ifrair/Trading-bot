import pandas as pd

class Indicators:

    def __init__(self, window: int = 12):
        self.window = window

    def calc_indicators(self, df: pd.DataFrame, indicators: list, drop_first: bool = False) -> None:
        """
        :param df: dataframe to calculate indicators
        :param indicators: list of needed indicators
        :param drop_first: flag to drop first probably uncorrect columns
        """
        if "CCI" in indicators:
            self.calc_CCI(df)
        if "RSI" in indicators:
            self.calc_RSI(df)
        if drop_first:
            df = df.drop(range(self.window * 2)).reset_index(drop=True)

    # index sma + tp
    def __calc_SMA(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'SMA' in df.columns:
            return
        df['TP'] = (df['Low'] + df['Close'] + df['High']) / 3
        df['SMA'] = df['TP']
        for i in range(1, self.window):
            df['SMA'] += df['TP'].shift(i).fillna(0)
            df['SMA'].iloc[i-1] /= i
        df['SMA'].iloc[self.window:] /= self.window

        df_temp = (df['TP'] - df['SMA'] + 0.1**10).abs()
        df['MAD'] = df_temp
        for i in range(1, self.window):
            df['MAD'] += df_temp.shift(i).fillna(0)
            df['MAD'].iloc[i-1] /= i
        df['MAD'].iloc[self.window:] /= self.window

    # index ema + emau + emad
    def __calc_EMA(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        if 'EMA' in df.columns:
            return
        # calc coef
        alpha = 2 / (1 + self.window)
        df['EMA'] = (df['Close'] - df['Close'].shift(1).fillna(0)) * alpha
        df['EMAU'] = df['EMA']
        df['EMAU'][df['EMAU'] < 0] = 0
        df['EMAD'] = -df['EMA']
        df['EMAD'][df['EMAD'] < 0] = 0
        df_temp = df.copy()
        for shift in range(1, self.window):
            for index in ['EMA', 'EMAU', 'EMAD']:
                df[index] += df_temp[index].shift(shift).fillna(0) * ((1 - alpha) ** shift)

    # index cci
    def calc_CCI(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_SMA(df)
        df['CCI'] = (df['TP'] - df['SMA']) / df['MAD'] / 0.015

    # index rsi + ema
    def calc_RSI(self, df: pd.DataFrame) -> None:
        """
        :param df: dataframe to calculate indicator
        """
        self.__calc_EMA(df)
        df['RSI'] = 100 * df['EMAU'] / (df['EMAU'] + df['EMAD'])
