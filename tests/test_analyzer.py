import json
import pandas as pd
import unittest

from unittest.mock import patch

from bot.analyzer import Analyzer


class Test(unittest.TestCase):
    settings_file = 'tests/settings_for_test.json'

    def __mocked_Strategy(*args, **kwargs):
        """Function to mock Strategy"""
        class Strategy:
            row: int = 0
            def predict(self, *args, **kwargs) -> float:
                self.row += 1
                if self.row > 100:
                    return 0
                elif self.row > 50:
                    return -0.9
                else:
                    return 0.9

        return Strategy()


    @patch('bot.analyzer.get_strategy', side_effect=__mocked_Strategy)
    def test_analyzer(self, *args):
        """test analyzer no profit"""
        table = pd.read_csv("tests/data_1m_120_rows.csv")
        with open(self.settings_file, 'r') as f:
            settings = json.load(f)['trader']
        result = Analyzer().analyze(table, settings['strategy'], 1e-3)
        self.assertEqual(result['avg_profit'], 0)
        self.assertEqual(result['orders_size'], 0)
        self.assertEqual(result['num_orders'], 0)
        self.assertEqual(result['com_profit'], -1e-3)
        self.assertEqual(result['total_profit'], 0)
