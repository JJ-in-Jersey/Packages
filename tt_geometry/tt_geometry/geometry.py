import pandas as pd
from datetime import datetime as dt, timedelta as td
from tt_date_time_tools import date_time_tools as dtt


def time_to_degrees(time): return time.hour * 15 + time.minute * 0.25


# def round_time_to(timestamp, mins): return dt.min + round((timestamp.to_pydatetime() - dt.min) / td(minutes=mins)) * td(minutes=mins)


class Arc:
    columns = ['date_time', 'date', 'start_angle', 'min_angle', 'end_angle', 'name', 'elapsed_time', 'start_datetime', 'min_datetime', 'end_datetime']
    name = None
    TIMESTEP = 15

    @staticmethod
    def round_time(timestamp, mins=15):
        return dt.min + round((timestamp.to_pydatetime() - dt.min) / td(minutes=mins)) * td(minutes=mins)

    def __init__(self, *args):
        self.elapsed_time = pd.to_timedelta(args[0] * Arc.TIMESTEP, unit='s').round('min')

        self.fractured = False

        self.start_datetime = dtt.datetime(args[1])
        self.start_date = self.start_datetime.date()
        self.start_time = self.start_datetime.time()
        self.start_angle = time_to_degrees(self.round_time(self.start_datetime))

        self.min_datetime = dtt.datetime(args[2])
        self.min_date = self.min_datetime.date()
        self.min_time = self.min_datetime.time()
        self.min_angle = time_to_degrees(self.round_time(self.min_datetime))

        self.end_datetime = dtt.datetime(args[3])
        self.end_date = self.end_datetime.date()
        self.end_time = self.end_datetime.time()
        self.end_angle = time_to_degrees(self.round_time(self.end_datetime))

        if self.start_date != self.end_date:
            self.fractured = True
            self.start_day_arc = FractionalArcStartDay(self)
            self.end_day_arc = FractionalArcEndDay(self)


# class RoundedArc(Arc):
#
#
#     def df_angles(self):
#         return pd.Series([self.start, self.start_date, self.start_angle, self.min_angle, self.end_angle, Arc.name, self.elapsed_time])
#
#     def fractional_arc_args(self):
#         return tuple([self.start, self.start_date, self.start_angle, self.min_angle, self.end_angle, Arc.name, self.elapsed_time])
#
#     def __init__(self, *args):
#         super().__init__(*args)
#
#         self.start_angle = time_to_degrees(round_time_to(self.start_datetime, RoundedArc.round_to))
#         self.min_angle = time_to_degrees(round_time_to(self.min_datetime, RoundedArc.round_to))
#         self.end_angle = time_to_degrees(round_time_to(self.end_datetime, RoundedArc.round_to))
#
#         if self.fractured:
#             start_day = FractionalArcStartDay(*args)
#             end_day = FractionalArcEndDay(*args)


# class FractionalArc(Arc):
#
#     def df_angles(self):
#         return pd.Series([self.start, self.start_date, self.start_angle, self.min_angle, self.end_angle, Arc.name, self.elapsed_time])
#
#     # start start_date, start_angle, min_angle, end_angle, name, elapsed_time
#     def __init__(self, *args):
#         self.start = args[0]
#         self.start_date = args[1]
#         self.start_angle = args[2]
#         self.min_angle = args[3]
#         self.end_angle = args[4]
#         self.name = args[5]
#         self.elapsed_time = args[6]


class FractionalArcStartDay:
    def __init__(self, arc: Arc):

        arc.end_angle = 360
        if 180 > arc.min_angle >= 0:
            arc.min_angle = None


class FractionalArcEndDay:
    def __init__(self, arc: Arc):

        arc.start_date = arc.start_date + td(days=1)
        arc.start_angle = 0
        if 360 > arc.min_angle > 180:
            arc.min_angle = None
