from bot.drawer import draw_dataset
from bot.dataset_parser import Parser
from bot.exceptions import ResponseError
from bot.indicators import calc_indicators
from bot.simulator import Simulator
from bot.trader import Trader

import creds

from time import sleep

import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

import warnings
warnings.filterwarnings("ignore")

timezone = 3

def download_data():
    table = Parser('BTCUSDT', '5m', ignore_gaps=True).get_table("2019-06-01T00:00:00", "2020-09-01T00:00:00")
    # table = Parser('BTCUSDT', '1m', timezone).get_table("2023-04-12T12:20:00", 1)
    table.to_csv('data/data_BTCUSDT_5m.csv', index=False)
    # table.to_csv('data.csv', mode='a', index=False)
    # table.iloc[:50000].to_csv('data/data_small.csv', index=False)
    # table[['Open', 'Close', 'Middle', 'Low', 'High', 'Volume usd', 'CCI']].to_csv('data.csv')
    # table[['Next Close']].to_csv('Y.csv')
    print(table)
    # draw_dataset(table)
    return table

def simulate():
    df = pd.read_csv("data/data.csv")
    calc_indicators(df, ['CCI'])
    df_y = df[["Next Close", "Close Delta"]]
    df_x = df.drop(columns=["Next Close", "Close Delta"])

    # for i in range(10):
    #     print(df_x["CCI"].corr(df_y["Close Delta"].shift(-i)))
    # df_x["CCI"].plot.hist(bins=30).show()

    Simulator(df_x.iloc[:], df_y.iloc[:]).simulate()

def trade():
    # df = pd.read_csv("data/data.csv")
    # calc_indicators(df, ['CCI'])
    while True:
        try:
            Trader(
                creds.api_key,
                creds.sec_key,
                first_asset="BTC",
                second_asset="USDT",
                timezone=timezone,
            ).trade()

        except ResponseError as exc:
            print(repr(exc))
        sleep(300)

download_data()

# from binance.spot import Spot

# from binance.error import ClientError
# from binance.spot import Spot
# import pandas as pd
# from pandas import DataFrame

# import creds

# pd.set_option('display.max_rows', 500)
# pd.set_option('display.max_columns', 500)
# pd.set_option('display.width', 1000)

# cl = Spot(
#     creds.api_key,
#     creds.sec_key,
#     base_url="https://api.binance.com",
#     # proxies={ 'https': creds.proxy }
# )

# symbol = 'BTCUSDT'

# try:
#     # r = cl.exchange_info(symbol)
#     # print(r)

#     # r = cl.new_order(
#     #     symbol=symbol,
#     #     newClientOrderId="MacOS_test_1",
#     #     side='SELL',
#     #     type='MARKET',
#     #     quantity=0.002,
#     # )
#     x = cl.trade_fee()
#     for s in x:
#         if s['takerCommission'] == "0":
#             print(s)

#     # print(r)

#     print("----------------------")
#     df = DataFrame(cl.get_orders(symbol, recvWindow=59000))
#     print(df.head(10))
# except ClientError as e:
#     print(e.error_code, e.error_message)
