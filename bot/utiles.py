from datetime import datetime
from dateutil.parser import parse as dt_parse
from multipledispatch import dispatch
from time import sleep

# convert from time to microseconds from epoch
@dispatch(str)
def time_to_int(time: str) -> int:
    dt = dt_parse(time)
    return time_to_int(dt)

@dispatch(datetime)
def time_to_int(time: datetime) -> int:
    epoch = datetime.utcfromtimestamp(0)
    return int((time - epoch).total_seconds() * 1000)

def tf_to_minutes(tf: str) -> int:
    coef_mapping = {
        "m": 1,
        "h": 60,
        "d": 60 * 24,
        "w": 60 * 24 * 7,
        "M": 60 * 24 * 30,
    }
    return int(tf[:-1]) * coef_mapping[tf[-1]]

def wait_till(end_time: datetime):
    """
    :param end_time: wait till time
    """
    while datetime.now() < end_time:
        sleep(0.1)