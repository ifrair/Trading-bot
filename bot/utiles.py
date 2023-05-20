from datetime import datetime, timedelta
from dateutil.parser import parse as dt_parse
from multipledispatch import dispatch
from time import sleep


@dispatch(str)
def time_to_int(time: str) -> int:
    """Convert from time to microseconds from epoch"""
    dt = dt_parse(time)
    return time_to_int(dt)


@dispatch(datetime)
def time_to_int(time: datetime) -> int:  # noqa: F811
    """Convert from time to microseconds from epoch"""
    epoch = datetime.utcfromtimestamp(0)
    return int((time - epoch).total_seconds() * 1000)


def tf_to_minutes(tf: str) -> int:
    """Converts from timeframe to minute number"""
    coef_mapping = {
        "m": 1,
        "h": 60,
        "d": 60 * 24,
        "w": 60 * 24 * 7,
        "M": 60 * 24 * 30,
    }
    return int(tf[:-1]) * coef_mapping[tf[-1]]


def wait_till(end_time: datetime) -> None:
    """
    Waits untill the moment
    :param end_time: wait till time
    """
    delta = end_time - datetime.now() + timedelta(milliseconds=1)
    if delta > timedelta(0):
        sleep(delta.total_seconds())
