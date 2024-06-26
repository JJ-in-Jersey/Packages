import pandas as pd
from datetime import datetime as dt, timedelta as td
from dateutil import parser
from tt_date_time_tools.date_time_tools import time_to_degrees


class Arc:

    columns = ['name', 'start_date', 'start_time', 'start_round_time',
               'start_angle', 'start_round_angle', 'min_time', 'min_round_time',
               'min_angle', 'min_round_angle', 'end_time', 'end_round_time',
               'end_angle', 'end_round_angle', 'elapsed_time']
    name = None

    def info(self):
        return pd.Series([self.name, self.start_date, self.start_time, self.start_round_time,
                          self.start_angle, self.start_round_angle, self.min_time, self.min_round_time,
                          self.min_angle, self.min_round_angle, self.end_time, self.end_round_time,
                          self.end_angle, self.end_round_angle, self.elapsed_time])

    def __init__(self, arg_dict: dict):
        # from arc_frame: start_index, start_datetime, min_index, min_datetime, end_index, end_datetime, transit_time, round_start, round_min, round_end
        # from arc_frame:     args[0],        args[1],   args[2],      args[3],   args[4],      args[5],      args[6]       arg[7]     arg[8]     arg[9]

        self.fractured = False
        self.start_day_arc = None
        self.end_day_arc = None
        self.name = Arc.name
        self.elapsed_time = str(arg_dict['transit_time']).split(' ')[2][:-3]

        self.start_datetime = parser.parse(str(arg_dict['start_datetime']))
        self.start_date = self.start_datetime.date()

        self.start_time = self.start_datetime.time()
        self.start_angle = time_to_degrees(self.start_time)
        self.start_round_time = parser.parse(str(arg_dict['start_round_time'])).time()
        self.start_round_angle = time_to_degrees(self.start_round_time)

        self.min_datetime = parser.parse(str(arg_dict['min_datetime']))
        self.min_date = self.min_datetime.date()
        self.min_time = self.min_datetime.time()
        self.min_angle = time_to_degrees(self.min_time)
        self.min_round_time = parser.parse(str(arg_dict['min_round_time'])).time()
        self.min_round_angle = time_to_degrees(self.min_round_time)

        self.end_datetime = parser.parse(str(arg_dict['end_datetime']))
        self.end_date = self.end_datetime.date()
        self.end_time = self.end_datetime.time()
        self.end_angle = time_to_degrees(self.end_time)
        self.end_round_time = parser.parse(str(arg_dict['end_round_time'])).time()
        self.end_round_angle = time_to_degrees(self.end_round_time)

        if self.start_date != self.end_date:
            self.fractured = True
            if not self.start_angle == 0.0 and not self.start_angle == 360.0:
                self.start_day_arc = FractionalArcStartDay(self)
            if not self.end_angle == 360.0 and not self.end_angle == 0.0:
                self.end_day_arc = FractionalArcEndDay(self)


class FractionalArcStartDay:
    #  arc with legitimate start date, end of a day

    def info(self):
        return pd.Series([self.name, self.start_date, self.start_time, self.start_round_time,
                          self.start_angle, self.start_round_angle, self.min_time, self.min_round_time,
                          self.min_angle, self.min_round_angle, self.end_time, self.end_round_time,
                          self.end_angle, self.end_round_angle, self.elapsed_time])

    def __init__(self, arc: Arc):

        self.name = arc.name
        self.elapsed_time = arc.elapsed_time

        self.start_date = arc.start_date
        self.start_time = arc.start_time
        self.start_angle = arc.start_angle
        self.start_round_time = arc.start_round_time
        self.start_round_angle = arc.start_round_angle

        self.min_date = arc.min_date
        self.min_time = arc.min_time
        self.min_angle = arc.min_angle
        self.min_round_time = arc.min_round_time
        self.min_round_angle = arc.min_round_angle

        self.end_angle = 360
        self.end_round_angle = 360
        self.end_time = pd.to_datetime(str(dt.today().date())).time()  # set to 00:00:00
        self.end_round_time = self.end_time
        self.end_round_angle = self.end_angle

        if not self.min_date == self.start_date:
            self.min_angle = None
            self.min_time = None
            self.min_round_time = None
            self.min_round_angle = None

        if self.min_angle == 0:
            self.min_angle = 360
            self.min_round_angle = self.min_angle


class FractionalArcEndDay:
    #  arc with a legitimate end date, start of a day

    def info(self):
        return pd.Series([self.name, self.start_date, self.start_time, self.start_round_time,
                          self.start_angle, self.start_round_angle, self.min_time, self.min_round_time,
                          self.min_angle, self.min_round_angle, self.end_time, self.end_round_time,
                          self.end_angle, self.end_round_angle, self.elapsed_time])

    def __init__(self, arc: Arc):

        self.name = arc.name
        self.elapsed_time = arc.elapsed_time

        self.start_date = arc.start_date + td(days=1)
        self.start_time = pd.to_datetime(str(dt.today().date())).time()
        self.start_angle = 0
        self.start_round_time = self.start_time
        self.start_round_angle = self.start_angle

        self.min_date = arc.min_date
        self.min_time = arc.min_time
        self.min_angle = arc.min_angle
        self.min_round_time = arc.min_round_time
        self.min_round_angle = arc.min_round_angle

        self.end_time = arc.end_time
        self.end_angle = arc.end_angle
        self.end_round_time = arc.end_round_time
        self.end_round_angle = arc.end_round_angle

        # self.start_angle = 0
        if not self.min_date == self.start_date:
            self.min_angle = None
            self.min_time = None
            self.min_round_time = None
            self.min_round_angle = None
