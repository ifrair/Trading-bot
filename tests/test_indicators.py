import unittest
import pandas as pd

from bot.indicators import Indicators


class Test(unittest.TestCase):

    table_path = "tests/data_1m_120_rows.csv"

    def test_indicators(self):
        """Checks base requirements"""
        table = pd.read_csv(self.table_path)
        columns_orig = table.columns
        indicators = Indicators()
        indicators.calc_indicators(table, drop_first=True)

        diff = set(Indicators.ind_list).difference(table.columns)
        assert not diff, f"Indicators {list(diff)} are not calculated"
        diff = set(columns_orig).difference(table.columns)
        assert not diff, f"Columns {list(diff)} disappeared"
        assert table.shape[0] > 0 and \
            table.shape[0] <= 120 - 2 * indicators.window, \
            f"{table.shape[0]} rows in table"

        for ind in set(table.columns).difference(columns_orig):
            assert all(val is not None for val in table[ind].values), \
                f"Found None value in {ind} column"

    def __check_indicator(self, ind_name: str, columns_list: list = []):
        """Checks indicators that should be"""
        table = pd.read_csv(self.table_path)
        columns_expected = set(table.columns).union(columns_list)
        Indicators().calc_indicators(table, [ind_name], drop_first=True)

        assert columns_expected == set(table.columns), \
            f"Expected: {columns_expected},\n" \
            f"Real: {set(table.columns)},\n" \
            f"Difference: " \
            f"{set(table.columns).symmetric_difference(columns_expected)},\n"

        return table

    # checks ADI
    def test_ADI(self):
        _ = self.__check_indicator('ADI', ['ADI', 'ADIEMA', 'CLV'])

    def test_CCI(self):
        """Checks CCI"""
        table = self.__check_indicator('CCI', ['CCI', 'TP', 'SMA', 'MAD'])
        assert all(table['CCI'].abs() < 1000)

    def test_MACD(self):
        """Checks MACD"""
        _ = self.__check_indicator('MACD', ['MACD', 'MACDEMA'])

    def test_MFI(self):
        """Checks MFI"""
        table = self.__check_indicator('MFI', ['MFI', 'TP', 'MR'])
        assert all(table['MFI'] >= 0) and all(table['MFI'] <= 100)

    def test_OBV(self):
        """Checks OBV"""
        _ = self.__check_indicator('OBV', ['OBV', 'OBVCA'])

    # checks PVT
    def test_PVT(self):
        _ = self.__check_indicator('PVT', ['PVT', 'PVTCA'])

    # checks RSI
    def test_RSI(self):
        table = self.__check_indicator(
            'RSI',
            ['RSI', 'RS', 'EMA', 'EMAU', 'EMAD']
        )
        assert all(table['RSI'] >= 0) and all(table['RSI'] <= 100)
