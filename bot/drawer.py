import matplotlib.pyplot as plt
import pandas as pd

def draw_dataset(table_orig: pd.DataFrame, indicators: list = ["ADI", "CCI", "MACD", "MFI", "OBV", "PVT", "RSI"]):
    """
    :param table_orig: dataframe to draw indicators
    :param indicators: list of drawing indicators
    """
    plt.rcParams["figure.figsize"] = (300,4.5)
    table = table_orig.copy()
    table.plot(x='Open time', y=['Close', 'Low', 'High'])

    def to_range(table: pd.DataFrame, column: str, l: int, r: int):
        """
        :param table: table to range
        :param column: column name to range
        :param l: min value
        :param r: max value
        """
        table[column] *= (r - l) / (table[column].max() - table[column].min())
        table[column] += l - table[column].min()

    if 'ADI' in table.columns and 'ADI' in indicators:
        to_range(table, 'Close', table['ADI'].min(), table['ADI'].max())
        ax = table.plot(x='Open time', y=['ADI', 'ADIEMA', 'Close'], title='ADI')

    if 'CCI' in table.columns and 'CCI' in indicators:
        to_range(table, 'Close', -200, 200)
        ax = table.plot(x='Open time', y=['CCI', 'Close'], title='CCI')
        ax.axhline(y=100, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
        ax.axhline(y=0, xmin=-1, xmax=1, color='g', linestyle='--', lw=1)
        ax.axhline(y=-100, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)

    if 'MACD' in table.columns and 'MACD' in indicators:
        to_range(table, 'Close', table['MACD'].min(), table['MACD'].max())
        ax = table.plot(x='Open time', y=['MACD', 'MACDEMA', 'Close'], title='MACD')

    if 'MFI' in table.columns and 'MFI' in indicators:
        to_range(table, 'Close', 0, 100)
        ax = table.plot(x='Open time', y=['MFI', 'Close'], title='MFI')
        ax.axhline(y=100, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
        ax.axhline(y=0, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
        ax.axhline(y=60, xmin=-1, xmax=1, color='g', linestyle='--', lw=1)
        ax.axhline(y=40, xmin=-1, xmax=1, color='g', linestyle='--', lw=1)

    if 'OBV' in table.columns and 'OBV' in indicators:
        to_range(table, 'Close', table['OBV'].min(), table['OBV'].max())
        ax = table.plot(x='Open time', y=['OBV', 'OBVCA', 'Close'], title='OBV')

    if 'PVT' in table.columns and 'PVT' in indicators:
        to_range(table, 'Close', table['PVT'].min(), table['PVT'].max())
        ax = table.plot(x='Open time', y=['PVT', 'PVTCA', 'Close'], title='PVT')

    if 'RSI' in table.columns and 'RSI' in indicators:
        to_range(table, 'Close', 0, 100)
        ax = table.plot(x='Open time', y=['RSI', 'Close'], title='RSI')
        ax.axhline(y=100, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
        ax.axhline(y=0, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
        ax.axhline(y=70, xmin=-1, xmax=1, color='g', linestyle='--', lw=1)
        ax.axhline(y=30, xmin=-1, xmax=1, color='g', linestyle='--', lw=1)

    plt.show()
