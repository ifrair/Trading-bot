import unittest

from dateutil.parser import parse as parse_dt
from unittest.mock import patch

from bot.dataset_parser import Parser
from bot.exceptions import RequestError, ResponseError
from bot.utiles import tf_to_minutes


class Test(unittest.TestCase):
    """Function to mock requests"""
    def __mocked_response(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

        if 'https://api.binance.com' in args[0]:
            # fail of server
            if kwargs["params"]["symbol"] == "fail_500":
                return MockResponse([], 500)
            # fail of request
            if kwargs["params"]["symbol"] == "fail_300":
                return MockResponse([], 300)
            return MockResponse(
                # filling with random values
                [
                    [
                        1499040000000,      # Kline open time
                        "0.01634790",       # Open price
                        "0.80000000",       # High price
                        "0.01575800",       # Low price
                        "0.01577100",       # Close price
                        "148976.11427815",  # Volume
                        1499644799999,      # Kline Close time
                        "2434.19055334",    # Quote asset volume
                        308,                # Number of trades
                        "1756.87402397",    # Taker buy base asset volume
                        "28.46694368",      # Taker buy quote asset volume
                        "0"                 # Unused field, ignore.
                    ]
                ],
                200
            )

        return MockResponse(None, 404)

    @patch('bot.dataset_parser.sleep')
    @patch('bot.dataset_parser.datetime')
    @patch('bot.dataset_parser.requests.get', side_effect=__mocked_response)
    def test_get_table(self, send_request_mock, now_mock, _):
        """Checks correct get_table request"""
        now_mock.now.return_value = parse_dt("2023-01-20T00:00:00")

        for tf in ['1m', '5m', '1h']:
            parser = Parser('SOLUSDT', tf, ignore_gaps=True)
            for args in [
                ["2023-01-15T00:00:00", "2023-01-20T00:00:00"],
                [5 * 24 * 60 // tf_to_minutes(tf)]
            ]:
                table = parser.get_table(*args)
                self.assertEqual(
                    table.shape[0],
                    len(send_request_mock.call_args_list),
                    f"{tf}, {args}"
                )

                sum_limit = sum(
                    int(call[1]['params']['limit'])
                    for call in send_request_mock.call_args_list
                )
                self.assertEqual(
                    sum_limit,
                    5 * 24 * 60 // tf_to_minutes(tf),
                    f"{tf}, {args}"
                )

                priv_time = "1673740800000"
                for call in send_request_mock.call_args_list:
                    self.assertEqual(
                        priv_time,
                        call[1]['params']['startTime'],
                        f"{tf}, {args}"
                    )
                    priv_time = call[1]['params']['endTime']
                self.assertEqual(priv_time, "1674172800000", f"{tf}, {args}")

                send_request_mock.call_args_list = []

    @patch('bot.dataset_parser.sleep')
    @patch('bot.dataset_parser.requests.get', side_effect=__mocked_response)
    def test_exc(self, send_request_mock, _):
        """checks fail get_table request"""
        # no response
        parser = Parser('fail_500', '1m', ignore_gaps=True)
        try:
            _ = parser.get_table("2023-01-15T00:00:00", "2023-01-15T00:01:00")
        except ResponseError:
            pass
        else:
            raise "No crush"
        self.assertEqual(len(send_request_mock.call_args_list), 5)

        # dont ignore gaps
        parser = Parser('SOLUSDT', '1m', ignore_gaps=False)
        try:
            _ = parser.get_table("2023-01-15T00:00:00", 123)
        except RequestError:
            pass
        else:
            raise "Gaps ignored"

        # wrong request
        parser = Parser('fail_300', '1m', ignore_gaps=True)
        try:
            _ = parser.get_table(10)
        except RequestError:
            pass
        else:
            raise "No crush"
