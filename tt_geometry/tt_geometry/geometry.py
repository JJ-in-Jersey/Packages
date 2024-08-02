from datetime import timedelta as td
from tt_date_time_tools.date_time_tools import time_to_degrees


class BaseArc:

    columns = None

    def info(self):
        return self.arc_dict

    def __init__(self, args):

        self.fractured = False
        self.zero_angle = False
        self.next_day_arc = False

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

        if self.arc_dict['start_date'] != self.arc_dict['end_date']:
            self.fractured = True

        angle_difference = self.arc_dict['end_angle'] - self.arc_dict['start_angle']
        if not self.fractured and (angle_difference == 360.0 or angle_difference == 0):
            self.zero_angle = True

        if self.fractured and not self.zero_angle and self.arc_dict['end_angle'] == 360.0 and not self.arc_dict['end_angle'] == 0.0:
            self.next_day_arc = True

        # end of the arc is in the next day and should be set to 00:00:00 for this day
        if self.fractured and not self.zero_angle:
            self.arc_dict['end_angle'] = 360
            self.arc_dict['end_round_angle'] = 360
            self.arc_dict['end_time'] = self.arc_dict['end_time'].replace(hour=23, minute=59)
            self.arc_dict['end_round_time'] = self.arc_dict['end_time'].replace(hour=23, minute=59)
            self.arc_dict['end_et'] = None

        #  if the minimum is in the next day, this day minimum should be zeroed out
        if (self.fractured and not self.zero_angle and
                not self.arc_dict['min_date'] == self.arc_dict['start_date']):
            self.arc_dict['min_angle'] = None
            self.arc_dict['min_time'] = None
            self.arc_dict['min_round_time'] = None
            self.arc_dict['min_round_angle'] = None
            self.arc_dict['min_et'] = None

        #  create new arc for the next day
        if self.fractured and not self.zero_angle and self.next_day_arc:
            new_args = dict(args)
            new_args['start_date'] = new_args['start_date'] + td(days=1)
            new_args['start_time'] = new_args['start_date'].replace(hour=0, minute=0)
            new_args['start_round_time'] = new_args['start_date'].replace(hour=0, minute=0)
            new_args['start_angle'] = 0
            new_args['start_round_angle'] = 0
            new_args['start_et'] = None
            self.next_day_arc = Arc(new_args)
