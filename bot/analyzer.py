from bot.strategist import get_strategy

import pandas as pd


class Analyzer:
    """calculates strategy statistics on dataframe"""
    window = 10

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
        for i in range(self.window-1, table.shape[0]):
            pred = strategy.predict(
                table.iloc[i-self.window+1: i+1]
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

        avg_profit = sum_profit / orders_size if orders_size > 0 else 0
        avg_profit_on_order = (sum_profit - orders_size * commission) / \
            num_orders if num_orders > 0 else 0
        result = {
            # average profit on an all-money order
            'avg_profit': avg_profit,
            # total size of transactions relative to all money
            'orders_size': orders_size,
            # number of completed orders
            'num_orders': num_orders,
            # average profit minus commission on an all-money order
            'com_profit': avg_profit - commission,
            # total profit including commission and compound interest
            'total_profit': pow(
                avg_profit_on_order + 1,
                num_orders,
            ) - 1,
        }
        return result
