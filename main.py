from bot.drawer import draw_dataset
from bot.dataset_parser import Parser
from bot.exceptions import ResponseError
from bot.indicators import Indicators
from bot.simulator import Simulator
from bot.trader import Trader

import creds

from binance.error import ClientError
from datetime import datetime
from time import sleep

import json
import pandas as pd
import unittest
# import warnings
# warnings.filterwarnings("ignore")

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

with open("settings.json", 'r') as f:
    settings = json.load(f)["main"]


# function to download data from market
def download_data():
    parser = Parser(
        'EOSUSDT',
        '15m',
        # timezone=settings["timezone"],
        ignore_gaps=True,
    )
    table = parser.get_table("2020-01-01T00:00:00", "2023-05-15T00:00:00")
    # table = parser.get_table("2023-04-12T12:20:00", 1)
    # table = pd.read_csv("data/data_small.csv").iloc[:300]
    Indicators().calc_indicators(table, drop_first=True)
    draw_dataset(table)
    table.to_csv('data/data_EOSUSDT_15m.csv', index=False)
    return table


# function to load data and run simulator
def simulate():
    df = pd.read_csv("data/data_SOL_5m.csv")
    Indicators().calc_indicators(df, drop_first=True)
    df_y = df[["Next Close", "Close Delta"]]
    df_x = df.drop(columns=["Next Close", "Close Delta"])
    Simulator(df_x.iloc[:4000], df_y.iloc[:4000]).simulate()


# function to run all the tests
def test():
    loader = unittest.TestLoader()
    start_dir = 'tests/'
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner()
    runner.run(suite)


# function to start trading
def trade():
    def print_logs(msg: str) -> None:
        with open(settings["log_file"], 'a') as f:
            print(f"{msg}, {datetime.now()}", file=f)

    f = open(settings["log_file"], 'w')
    f.close()

    trader = Trader(
        creds.api_key,
        creds.sec_key,
        first_asset="BTC",
        second_asset="USDT",
        timezone=settings["timezone"],
    )

    while True:
        try:
            print_logs("Start trading")
            trader.trade()

        except ResponseError as e:
            print_logs(f"Parser error:\n{repr(e)}")
        except ClientError as e:
            print_logs(f"Trader error:\n{e.error_code},\n{e.error_message}")
        except Exception as e:
            print_logs(f"Critical error:\n{repr(e)}")
            raise
        sleep(300)
        print_logs("Restartng")

trade()
