import pandas as pd
from datetime import datetime as dt, timedelta as td
from tt_date_time_tools import date_time_tools as dtt


def time_to_degrees(time): return time.hour * 15 + time.minute * 0.25


class Arc:

    columns = ['name', 'start_date', 'start_time', 'start_angle', 'min_time', 'min_angle', 'end_time', 'end_angle', 'elapsed_time']
    name = None

    def info(self):
        return pd.Series([self.name, self.start_date, self.start_time, self.start_angle, self.min_time, self.min_angle, self.end_time, self.end_angle, self.elapsed_time])

    @staticmethod
    def round_time(timestamp, mins=15):
        return dt.min + round((timestamp.to_pydatetime() - dt.min) / td(minutes=mins)) * td(minutes=mins)

    @staticmethod
    def time_to_degrees(time):
        return time.hour * 15 + time.minute * 0.25

    def __init__(self, *args):
        # from arc_frame: start_index, start_datetime, min_index, min_datetime, end_index, end_datetime, transit_time
        # from arc_frame:     args[0],        args[1],   args[2],      args[3],   args[4],      args[5],      args[6]

        self.fractured = False
        self.start_day_arc = None
        self.end_day_arc = None
        self.name = Arc.name
        self.elapsed_time = str(args[6]).split(' ')[2][:-3]

        self.start_datetime = dtt.datetime(args[0])
        self.start_date = self.start_datetime.date()
        self.start_time = self.start_datetime.time()
        self.start_angle = time_to_degrees(self.round_time(self.start_datetime))

        self.min_datetime = dtt.datetime(args[2])
        self.min_date = self.min_datetime.date()
        self.min_time = self.min_datetime.time()
        self.min_angle = time_to_degrees(self.round_time(self.min_datetime))

        self.end_datetime = dtt.datetime(args[4])
        self.end_date = self.end_datetime.date()
        self.end_time = self.end_datetime.time()
        self.end_angle = time_to_degrees(self.round_time(self.end_datetime))

        if self.start_date != self.end_date:
            self.fractured = True
            if not self.start_angle == 0.0:
                self.start_day_arc = FractionalArcStartDay(self)
            if not self.end_angle == 360.0:
                self.end_day_arc = FractionalArcEndDay(self)


class FractionalArcStartDay:

    def info(self):
        return pd.Series([self.name, self.start_date, self.start_time, self.start_angle, self.min_time, self.min_angle, self.end_time, self.end_angle, self.elapsed_time])

    def __init__(self, arc: Arc):

        self.name = arc.name
        self.elapsed_time = arc.elapsed_time

        self.start_date = arc.start_date
        self.start_angle = arc.start_angle
        self.start_time = arc.start_time

        self.min_angle = arc.min_angle
        self.min_time = arc.min_time

        self.end_angle = arc.end_angle
        self.end_time = arc.end_time

        self.end_angle = 360
        self.end_time = pd.to_datetime(str(dt.today().date())).time()

        if 180 > arc.min_angle >= 0:
            self.min_angle = None
            self.min_time = None


class FractionalArcEndDay:

    def info(self):
        return pd.Series([self.name, self.start_date, self.start_time, self.start_angle, self.min_time, self.min_angle, self.end_time, self.end_angle, self.elapsed_time])

    def __init__(self, arc: Arc):

        self.name = arc.name
        self.elapsed_time = arc.elapsed_time

        self.start_date = arc.start_date
        self.start_angle = arc.start_angle
        self.start_time = arc.start_time

        self.min_angle = arc.min_angle
        self.min_time = arc.min_time

        self.end_angle = arc.end_angle
        self.end_time = arc.end_time

        self.start_date = arc.start_date + td(days=1)
        self.start_angle = 0
        self.start_time = pd.to_datetime(str(dt.today().date())).time()

        if 360 > arc.min_angle > 180:
            self.min_angle = None
            self.min_time = None
