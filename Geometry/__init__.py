import pandas as pd
from datetime import datetime as dt, timedelta as td

def time_to_degrees(time):
    return time.hour * 15 + time.minute * 0.25

def round_time_to(timestamp, mins):
    return dt.min + round((timestamp.to_pydatetime() - dt.min) / td(minutes=mins)) * td(minutes=mins)

class Arc:

    def angle_list(self):
        return [self.start_angle, self.min_angle, self.end_angle]

    def time_list(self):
        return [self.start_time, self.min_time, self.end_time]

    def __init__(self, *args):
        self.fractured = False
        self.tts = args[0]
        self.start_index = args[1]
        self.min_index = args[2]
        self.end_index = args[3]

        self.start_time = pd.to_datetime(self.start_index, unit='s').round('min')
        self.end_time = pd.to_datetime(self.end_index, unit='s').round('min')

        if self.start_time.date() != self.end_time.date(): self.fractured = True

        self.start_angle = time_to_degrees(self.start_time)
        self.end_angle = time_to_degrees(self.end_time)

        if self.min_index is not None:
            self.min_time = pd.to_datetime(self.min_index, unit='s').round('min')
            self.min_angle = time_to_degrees(self.min_time)

class RoundedArc:

    def __init__(self, arc: Arc, minutes):
        self.arc = arc
        self.min_time = None
        self.min_angle = None

        self.start_time = round_time_to(self.arc.start_time, minutes)
        self.end_time = round_time_to(self.arc.end_time, minutes)

        self.start_angle = time_to_degrees(self.start_time)
        self.end_angle = time_to_degrees(self.end_time)

        if m_index is not None:
            self.min_time = round_time_to(self.arc.min_time, minutes)
            self.min_angle = time_to_degrees(self.min_time)
