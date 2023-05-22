import json
import os
import pandas as pd
import unittest

from datetime import timedelta
from dateutil.parser import parse as parse_dt
from unittest.mock import patch

from bot.trader import Trader


class TestEnd(Exception):
    pass


class Test(unittest.TestCase):
    settings_file = 'tests/settings_for_test.json'

    def __mocked_Indicators(*args, **kwargs):
        """Function to mock Indicators"""
        class Indicators:
            def calc_indicators(self, *args, **kwargs) -> None:
                return

        return Indicators()

    def __mocked_Parser(*args, **kwargs):
        """Function to mock Parser"""
        class Parser:
            def get_table(self, *args, **kwargs) -> pd.DataFrame:
                return pd.read_csv("tests/data_1m_120_rows.csv")

        return Parser()

    class __Mocked_Spot:
        """Spot mock"""
        def __init__(self, *args, **kwargs):
            return

        def exchange_info(self, *args, **kwargs) -> dict:
            return {
                'symbols': [
                    {
                        'filters': [
                            {
                                'filterType': 'LOT_SIZE',
                                'stepSize': 0.000001,
                                'minQty': 0,
                            },
                            {
                                'filterType': 'NOTIONAL',
                                'minNotional': 0,
                            }
                        ]
                    }
                ]
            }

        def user_asset(self, *args, **kwargs) -> dict:
            return [
                {
                    'asset': 'BTC',
                    'free': 1,
                },
                {
                    'asset': 'USDT',
                    'free': 1000,
                }
            ]

        def new_order(self, *args, **kwargs) -> None:
            return

    def __mocked_Strategy(*args, **kwargs):
        """Function to mock Strategy"""
        class Strategy:
            row: int = 0

            def predict(self, *args, **kwargs) -> float:
                self.row += 1
                if self.row > 2000:
                    raise TestEnd("correct")
                if self.row > 1000:
                    return 0
                elif self.row > 500:
                    return 0.9
                else:
                    return -0.9

        return Strategy()

    @patch('bot.trader.datetime')
    @patch('bot.trader.wait_till')
    @patch('bot.trader.Indicators', side_effect=__mocked_Indicators)
    @patch('bot.trader.Parser', side_effect=__mocked_Parser)
    @patch('bot.trader.get_strategy', side_effect=__mocked_Strategy)
    @patch('bot.trader.Spot', new=__Mocked_Spot)
    def test_trade(self, *args, **kwargs):
        """Checks trading"""
        args[4].now.return_value = parse_dt("2023-05-23T08:56:00")
        with open(self.settings_file, 'r') as f:
            settings = json.load(f)['trader']

        with patch.object(self.__Mocked_Spot, 'new_order') as new_order:

            trader = Trader('', '', settings_file_path=self.settings_file)
            try:
                trader.trade()
            except TestEnd:
                pass
            except Exception:
                raise
            else:
                raise "No test end"

            # check new order calls
            self.assertEqual(len(new_order.call_args_list), 1000)
            for i in range(500):
                call_kwargs = new_order.call_args_list[i].kwargs
                self.assertEqual(call_kwargs['quoteOrderQty'], 891)
                symbol = settings['first_asset'] + settings['second_asset']
                self.assertEqual(symbol, 'BTCUSDT')
                self.assertEqual(call_kwargs['side'], 'BUY')
            for i in range(500, 1000):
                call_kwargs = new_order.call_args_list[i].kwargs
                self.assertEqual(call_kwargs['quantity'], 0.891)
                symbol = settings['first_asset'] + settings['second_asset']
                self.assertEqual(symbol, 'BTCUSDT')
                self.assertEqual(call_kwargs['side'], 'SELL')

        # check strategy creating
        self.assertEqual(len(args[0].call_args_list), 1)
        self.assertEqual(
            args[0].call_args_list[0].args[0],
            settings["strategy"]
        )
        # check parser creating
        self.assertEqual(len(args[1].call_args_list), 1)
        # check indicators creating
        self.assertEqual(len(args[2].call_args_list), 1)
        self.assertEqual(
            args[2].call_args_list[0].args[0],
            settings["indicator_window"]
        )
        # check wait_till
        priv_time = args[3].call_args_list[0].args[0] - timedelta(minutes=1)
        for call in args[3].call_args_list:
            self.assertEqual(call.args[0] - priv_time, timedelta(minutes=1))
            priv_time = call.args[0]

        os.remove(settings["log_file"])
