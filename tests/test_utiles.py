import unittest

from datetime import datetime

from bot.utiles import tf_to_minutes, time_to_int


class Test(unittest.TestCase):
    def test_utiles(self):
        # tf_to_minutes check
        self.assertEqual(tf_to_minutes("123m"), 123)
        self.assertEqual(tf_to_minutes("15h"), 15 * 60)
        self.assertEqual(tf_to_minutes("100d"), 100 * 24 * 60)

        # time_to_int check
        self.assertEqual(
            time_to_int("2023-01-15T03:50:02"),
            1673754602000,
        )
        self.assertEqual(
            time_to_int(datetime(2020, 10, 11, 5, 2, 33)),
            1602392553000,
        )
