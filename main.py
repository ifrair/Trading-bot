from drawer import draw_dataset
from parser import Parser

import pandas as pd
import warnings
warnings.filterwarnings("ignore")


table = Parser('BTCUSDT', '1m').get_table("2020-01-01T00:00:00", "2020-01-30T00:00:00")
table.to_csv('data.csv', index=False)
# table.to_csv('data.csv', mode='a', index=False)
# table[['Open', 'Close', 'Middle', 'Low', 'High', 'Volume usd', 'CCI']].to_csv('data.csv')
# table[['Next Close']].to_csv('Y.csv')
# print(table)

# table = pd.read_csv("data.csv")
# draw_dataset(table)
