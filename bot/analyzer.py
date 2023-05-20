from bot.strategist import get_strategy

import pandas as pd


class Analyzer:
    """calculates strategy statistics on dataframe"""
    def analyze(
        self,
        table: pd.DataFrame,
        strategy_name: str,
        commission: float,
    ) -> dict:
        """
        :param table: dataframe with all required info
        :param strategy_name: trading strategy name
        :param commission: comission percentage in order (from 0 to 1)
        """
        strategy = get_strategy(strategy_name)
        amount = 0.0
        sum_profit = 0
        orders_size = 0
        avg_price = 0
        num_orders = 0
        for i in range(99, table.shape[0]):
            pred = strategy.predict(
                table.iloc[i-99: i+1].reset_index(drop=True)
            )
            price = table['Close'].iloc[i]
            if pred < 0 and amount < 1:
                num_orders += 1
                sz = -pred * (1 - amount)
                orders_size += sz
                avg_price += price * sz
                amount += sz
            elif pred > 0 and amount > 0:
                num_orders += 1
                sz = pred * amount
                buy_price = avg_price / amount
                orders_size += sz
                sum_profit += sz * (price - buy_price) / buy_price
                avg_price -= sz * buy_price
                amount -= sz

        result = {
            # average profit on an all-money order
            'avg_profit': sum_profit / orders_size,
            # total size of transactions relative to all money
            'orders_size': orders_size,
            # number of completed orders
            'num_orders': num_orders,
            # average profit minus commission on an all-money order
            'com_profit': sum_profit / orders_size - commission,
            # total profit including commission and compound interest
            'total_profit': pow(
                (sum_profit - orders_size * commission) / num_orders + 1,
                num_orders
            ) - 1,
        }
        return result
