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

    def __init__(self, *args):
        self.tts = args[0]
        self.start_index = args[1]
        self.min_index = args[2]
        self.end_index = args[3]
        self.min_time = None
        self.min_angle = None
        self.fractured = False

        self.base_start = pd.to_datetime(self.start_index, unit='s').round('min')
        self.base_min = pd.to_datetime(self.min_index, unit='s').round('min')
        self.base_end = pd.to_datetime(self.end_index, unit='s').round('min')

class RoundedArc(Arc):

    def df_angles(self): return pd.Series([self.start_date, self.start_angle, self.min_angle, self.end_angle, Arc.name])
    def fractional_arc_args(self): return tuple([self.start_date, self.start_angle, self.min_angle, self.end_angle, Arc.name])
    def print_times(self): print(f's: {self.start_time} m: {self.min_time} e: {self.end_time}')
    def print_angles(self): print(f's: {self.start_angle} m: {self.min_angle} e: {self.end_angle}')

    def __init__(self, *args):
        super().__init__(*args)

        self.start = round_time_to(self.base_start, Arc.round_to)
        self.min = round_time_to(self.base_min, Arc.round_to)
        self.end = round_time_to(self.base_end, Arc.round_to)

        self.start_date = self.start.date()
        self.start_time = self.start.time()
        self.end_date = self.end.date()
        self.end_time = self.end.time()
        self.min_date = self.min.date()
        self.min_time = self.min.time()

        self.start_angle = time_to_degrees(self.start)
        self.end_angle = time_to_degrees(self.end)
        self.min_angle = time_to_degrees(self.min)

        if self.start_date != self.end_date and self.end_angle != 0:
            self.fractured = True
        else:
            self.end_angle = 360
            if self.min_angle == 0: self.min_angle = 360

class FractionalArc:

    def df_angles(self): return pd.Series([self.start_date, self.start_angle, self.min_angle, self.end_angle, Arc.name])

    # start_date, start_angle, min_angle, end_angle, name
    def __init__(self, *args):
        self.start_date = args[0]
        self.start_angle = args[1]
        self.min_angle = args[2]
        self.end_angle = args[3]
        self.name = args[4]

class FractionalArcStartDay(FractionalArc):
    def __init__(self, *args):
        super().__init__(*args)

        self.end_angle = 360
        if 180 > self.min_angle >= 0: self.min_angle = None

class FractionalArcEndDay(FractionalArc):
    def __init__(self, *args):
        super().__init__(*args)

        self.start_angle = 0
        if 360 > self.min_angle > 180: self.min_angle = None
