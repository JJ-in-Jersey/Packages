from glob import glob
from os.path import join, getctime
import numpy as np
import pandas as pd
from MemoryHelper import MemoryHelper as mh

class DateTimeTools:

    @staticmethod
    def hours_mins(secs): return "%d:%02d" % (secs // 3600, secs % 3600 // 60)

    @staticmethod
    def mins_secs(secs): return "%d:%02d" % (secs // 60, secs % 60)

    @staticmethod
    def int_timestamp(date): return int(pd.Timestamp(date).timestamp())

    @staticmethod
    def round_dt_quarter_hour(timestamp): return dt.min + round(
        (timestamp.to_pydatetime() - dt.min) / td(minutes=15)) * td(minutes=15)

    @staticmethod
    def time_to_degrees(time): return int(time.hour * 15 + time.minute * 3.5)

    def __init__(self):
        pass
