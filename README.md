# Trading-bot
# Instructions:
## Trading:
To start trading just call the trade function in main.py. \
Enter credentials in console or create creds.txt file and enter api key on the first row and secure key on the second. \
You can controle trading in real time using [settings file](## Settings).
## Testing:
Call test function from main.py to run tests. By adding modules or indicators, add tests to tests folder. \
## Indicators:
To add new indicators:
1) Add calc_{ind_name} function to Indicators and {ind_name} to ind_list. \
2) Add indicator to drawer (optional). \
3) Add test to tests/test_indicators.py (optional). \
4) Add indicator to [settings](## Settings) if used in trader.
## Strategies:
To add strategy:
1) Inherit your strategy class in strategist.py. \
2) Put heavy operations to init (like fit for ML srategies).
3) Add predict function, it returns number in range from -1 (that means that price now is too low) to 1 (too high). 0 means that the order will not be formed. \
4) Add strategy params and indicators to [settings](## Settings) (optional).
5) Test your strategy using Analizer from analizer.py (optional).
## Settings:
All is in settings.json. Please don`t change param names.
### main
log_file - log file name for main logs (like errors). \
num_fail_tries - max number of errors to restart trading. \
timezone - your timezone to make correct requests.
### parser
log_file - log file name for downloading logs. \
batch_size - number of rows to download by one request. \
num_fail_tries - number of retries when connection errors. \
sleep_time - min time between downloading two batches. \
### trader
first_asset - first asset of pair. \
indicators - list of needed indicators for trading. \
indicator_window - window of rows to indicator calculation. \
log_file - log file name for trading logs. \
num_stored_rows - number of rows needed to strategy. \
refresh_friq - number of rows between logging and market settings update. \
second_asset - second asset of pair. \
slippage - small part of money to correct trades. \
strategy - strategy name for trading. \
timeframe - trading timeframe (time between rows) in Binance format. \
withdrawal_coef - amount part of order to be stored as income.
### strategist
Strategies with needed params as dicts. 
