import pandas as pd
from datetime import datetime as dt, timedelta as td

def time_to_degrees(time):
    return time.hour * 15 + time.minute * 0.25

def round_time_to(timestamp, mins):
    return dt.min + round((timestamp.to_pydatetime() - dt.min) / td(minutes=mins)) * td(minutes=mins)

class Arc:

    columns = ['date', 'start', 'min', 'end', 'name']
    round_to = 15
    name = None

    def angles(self): return pd.Series([self.date(), self.start_angle, self.min_angle, self.end_angle, Arc.name])
    def times(self): return pd.Series([self.date(), self.start_time, self.min_time, self.end_time, Arc.name])

    def arc_name(self, name):
        self.name = name

    def __init__(self, *args):
        self.tts = args[0]
        self.start_index = args[1]
        self.min_index = args[2]
        self.end_index = args[3]
        self.name = None
        self.min_time = None
        self.min_angle = None
        self.date = None

        self.base_start_time = pd.to_datetime(self.start_index, unit='s').round('min')
        self.base_end_time = pd.to_datetime(self.end_index, unit='s').round('min')
        self.base_date = self.base_start_time.date

        if self.min_index is not None:
            self.base_min_time = pd.to_datetime(self.min_index, unit='s').round('min')

class RoundedArc(Arc):

    def __init__(self, *args):
        super().__init__(*args)
        self.fractured = False
        self.has_minimum = False

        self.start_time = round_time_to(self.base_start_time, Arc.round_to)
        self.end_time = round_time_to(self.base_end_time, Arc.round_to)

        if self.start_time.date() != self.end_time.date(): self.fractured = True
        self.date = self.start_time.date

        self.start_angle = time_to_degrees(self.start_time)
        self.end_angle = time_to_degrees(self.end_time)

        if self.base_min_time is not None:
            self.min_time = round_time_to(self.base_min_time, Arc.round_to)
            self.min_angle = time_to_degrees(self.min_time)

def fractured_arc_clone(arc: Arc):
    if not arc.fractured: raise TypeError
    if arc.min_angle == 0:
        print('min is zero')
    elif 360 > arc.min_angle > 180:
        print('min on left')
    else:
        print('min on right')
