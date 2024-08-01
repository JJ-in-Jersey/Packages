import pandas as pd
from datetime import datetime as dt, timedelta as td
from tt_date_time_tools.date_time_tools import time_to_degrees


class BaseArc:

    columns = None
    types = {}

    def info(self):
        return self.arc_dict

    def __init__(self, args):
        self.arc_dict = {
            'start_date': None, 'min_date': None, 'end_date': None,
            'start_time': None, 'start_round_time': None, 'start_et': None,
            'min_time': None, 'min_round_time': None, 'min_et': None,
            'end_time': None, 'end_round_time': None, 'end_et': None
        }

        for key in self.arc_dict.keys():
            self.arc_dict[key] = args[key]

        self.arc_dict['start_angle'] = time_to_degrees(self.arc_dict['start_time'])
        self.arc_dict['start_round_angle'] = time_to_degrees(self.arc_dict['start_round_time'])
        self.arc_dict['min_angle'] = time_to_degrees(self.arc_dict['min_time'])
        self.arc_dict['min_round_angle'] = time_to_degrees(self.arc_dict['min_round_time'])
        self.arc_dict['end_angle'] = time_to_degrees(self.arc_dict['end_time'])
        self.arc_dict['end_round_angle'] = time_to_degrees(self.arc_dict['end_round_time'])
        self.arc_dict['arc_angle'] = self.arc_dict['end_angle'] - self.arc_dict['start_angle']
        self.arc_dict['arc_round_angle'] = self.arc_dict['end_round_angle'] - self.arc_dict['start_round_angle']

        BaseArc.columns = list(self.arc_dict.keys())


class Arc(BaseArc):

    def __init__(self, args: dict):
        super().__init__(args)

        self.fractured = False
        self.start_day_arc = False
        self.end_day_arc = False

        if self.arc_dict['start_date'] != self.arc_dict['end_date']:
            self.fractured = True

            if not self.arc_dict['min_date'] == self.arc_dict['start_date']:
                self.arc_dict['min_angle'] = None
                self.arc_dict['min_time'] = None
                self.arc_dict['min_round_time'] = None
                self.arc_dict['min_round_angle'] = None
                self.arc_dict['min_et'] = None

            if not self.arc_dict['start_angle'] == 0.0 and not self.arc_dict['start_angle'] == 360.0:
                self.start_day_arc = True
                self.arc_dict['end_angle'] = 360
                self.arc_dict['end_round_angle'] = self.arc_dict['end_angle']
                self.arc_dict['end_time'] = pd.to_datetime(str(dt.today().date())).time()  # set to 00:00:00
                self.arc_dict['end_round_time'] = self.arc_dict['end_time']
                self.arc_dict['end_et'] = None

                if self.arc_dict['min_angle'] == 0:
                    self.arc_dict['min_angle'] = 360
                    self.arc_dict['min_round_angle'] = self.arc_dict['min_angle']

                # self.start_day_arc = FractionalArcStartDay(self)
            if not self.arc_dict['end_angle'] == 360.0 and not self.arc_dict['end_angle'] == 0.0:
                self.end_day_arc = True
                self.arc_dict['start_date'] = self.arc_dict['start_date'] + td(days=1)
                self.arc_dict['start_time'] = pd.to_datetime(str(dt.today().date())).time()  # set to 00:00:00
                self.arc_dict['start_angle'] = 0
                self.arc_dict['start_round_time'] = self.arc_dict['start_time']
                self.arc_dict['start_round_angle'] = self.arc_dict['start_angle']
                self.arc_dict['start_et'] = None
