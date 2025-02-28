import dateparser
import pandas as pd
from sympy.combinatorics.group_numbers import is_nilpotent_number


def hours_mins(secs): return "%d:%02d" % (secs // 3600, secs % 3600 // 60)


def mins_secs(secs): return "%d:%02d" % (secs // 60, secs % 60)


def time_to_degrees(time):
    if isinstance(time, str):
        time = dateparser.parse(time)
        return time.hour * 15 + time.minute * 0.25
    elif isinstance(time, pd.Timestamp):
        return time.hour * 15 + time.minute * 0.25
    elif time is None:
        return None
