from bot.analyzer import Analyzer
from bot.drawer import draw_dataset
from bot.dataset_parser import Parser
from bot.exceptions import ResponseError
from bot.indicators import Indicators
from bot.simulator import Simulator
from bot.trader import Trader
from bot.utiles import tf_to_minutes

from binance.error import ClientError
from datetime import datetime, timedelta
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


def analyze():
    """Function to calculate effectiveness of strategy"""
    symb = 'EOS'
    tf = '1m'
    num_rows = 10000
    table = pd.read_csv(f'data/data_{symb}_{tf}.csv').iloc[-num_rows:]
    Indicators().calc_indicators(table, drop_first=True)
    results = Analyzer().analyze(
        table=table,
        strategy_name="CCI",
        commission=1e-3,
    )
    print(
        f"Average profit: {results['avg_profit']}",
        f"Sum order size: {results['orders_size']}",
        f"Number of orders: {results['num_orders']}",
        f"Profit with commission: {results['com_profit']}",
        f"Total profit: {results['total_profit']}",
        f"Time period: {timedelta(minutes=tf_to_minutes(tf)*num_rows)}",
        sep=",\n",
    )


def download_data():
    """Function to download data from market"""
    parser = Parser(
        'EOSUSDT',
        '1m',
        # timezone=settings["timezone"],
        ignore_gaps=True,
    )
    table = parser.get_table("2020-01-01T00:00:00", "2023-05-15T00:00:00")
    # table = parser.get_table("2023-04-12T12:20:00", 1)
    # table = pd.read_csv("data/data_BTC_1d.csv").iloc[:300]
    Indicators().calc_indicators(table, drop_first=True)
    draw_dataset(table)
    table.to_csv('data/data_EOS_1m.csv', index=False)
    return table


def simulate():
    """Function to load data and run simulator"""
    df = pd.read_csv("data/data_EOS_1m.csv")
    Indicators().calc_indicators(df, drop_first=True)
    df_y = df[["Next Close", "Close Delta"]]
    df_x = df.drop(columns=["Next Close", "Close Delta"])
    Simulator(df_x.iloc[-9900:], df_y.iloc[-9900:]).simulate()


def test():
    """Function to run all the tests"""
    loader = unittest.TestLoader()
    start_dir = 'tests/'
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner()
    runner.run(suite)


def trade():
    """Function to start trading"""
    def print_logs(msg: str) -> None:
        with open(settings['log_file'], 'a') as f:
            print(f"{msg}, {datetime.now()}", file=f)

    f = open(settings['log_file'], 'w')
    f.close()

    try:
        with open('creds.txt', 'r') as f:
            api_key = f.readline()
            sec_key = f.readline()
    except IOError:
        api_key = input("Enter api key:\n")
        sec_key = input("Enter secure key:\n")
        with open('creds.txt', 'w') as f:
            print(api_key, sec_key, file=f, sep='\n')

    trader = Trader(
        api_key,
        sec_key,
        timezone=settings['timezone'],
    )
    tries = 1
    while True:
        try:
            print_logs("Start trading")
            trader.trade()

        except ResponseError as e:
            print_logs(f"Parser error:\n{repr(e)}")
        except ClientError as e:
            print_logs(f"Trader error:\n{e.error_code},\n{e.error_message}")
        except Exception as e:
            print_logs(f"Critical error:\n{repr(e)}\nClosing...")
            raise
        tries += 1
        if tries > settings['num_fail_tries']:
            print_logs("Too many tries. Closing...")
            return
        sleep(300)
        print_logs(f"Restartng, Try number: {tries}")


trade()
