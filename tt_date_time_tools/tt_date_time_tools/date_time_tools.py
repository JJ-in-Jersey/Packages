import dateparser
from pandas import Timestamp


def hours_mins(secs): return "%d:%02d" % (secs // 3600, secs % 3600 // 60)


def mins_secs(secs): return "%d:%02d" % (secs // 60, secs % 60)


def time_to_degrees(time: str | Timestamp | None):
    if isinstance(time, str):
        time = dateparser.parse(time)
        return (time.hour * 15 + time.minute * 0.25) % 360
    elif isinstance(time, Timestamp):
        return (time.hour * 15 + time.minute * 0.25) % 360
    else:
        raise TypeError
