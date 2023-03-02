import pandas as pd


def calc_indicators(df: pd.DataFrame, indicators: list, drop_first: bool = False) -> None:
    if "CCI" in indicators:
        calc_CCI(df)

    # index cci
    def calc_CCI(df):
        N = 12
        df['TP'] = (df['Low'] + df['Close'] + df['High']) / 3

        df['SMA'] = df['TP']
        for i in range(1, N):
            df['SMA'] += df['TP'].shift(i).fillna(0)
            df['SMA'].iloc[i-1] /= i
        df['SMA'].iloc[N:] /= N

        df_temp = (df['TP'] - df['SMA'] + 0.1**10).abs()
        df['MAD'] = df_temp
        for i in range(1, N):
            df['MAD'] += df_temp.shift(i).fillna(0)
            df['MAD'].iloc[i-1] /= i
        df['MAD'].iloc[N:] /= N

        df['CCI'] = (df['TP'] - df['SMA']) / df['MAD'] / 0.015

        if drop_first:
            df = df.drop(range(N * 2)).reset_index(drop=True)
