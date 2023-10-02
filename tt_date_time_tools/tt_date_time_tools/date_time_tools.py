import pandas as pd
from datetime import datetime as dt, timedelta as td


def hours_mins(secs): return "%d:%02d" % (secs // 3600, secs % 3600 // 60)


def mins_secs(secs): return "%d:%02d" % (secs // 60, secs % 60)


def int_timestamp(date): return int(pd.Timestamp(date).timestamp())


def round_dt_quarter_hour(timestamp): return dt.min + round((timestamp.to_pydatetime() - dt.min) / td(minutes=15)) * td(minutes=15)


def time_to_degrees(time): return time.hour * 15 + time.minute * 0.25
