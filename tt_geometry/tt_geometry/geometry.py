from datetime import timedelta as td
from tt_date_time_tools.date_time_tools import time_to_degrees
from copy import deepcopy


class BaseArc:

    columns = None

    def info(self):
        return self.arc_dict

    def __init__(self, args):

        self.arc_dict = {
            'start_datetime': None, 'min_datetime': None, 'end_datetime': None,
            'start_round_datetime': None, 'min_round_datetime': None, 'end_round_datetime': None,
            'start_et': None, 'min_et': None, 'end_et': None
        }

        for key in self.arc_dict.keys():
            self.arc_dict[key] = args[key]

        self.arc_dict['start_angle'] = time_to_degrees(self.arc_dict['start_datetime'].time())
        self.arc_dict['start_round_angle'] = time_to_degrees(self.arc_dict['start_round_datetime'].time())
        if not self.arc_dict['min_datetime'] is None: self.arc_dict['min_angle'] = time_to_degrees(self.arc_dict['min_datetime'].time())
        if not self.arc_dict['min_round_datetime'] is None: self.arc_dict['min_round_angle'] = time_to_degrees(self.arc_dict['min_round_datetime'].time())
        self.arc_dict['end_angle'] = time_to_degrees(self.arc_dict['end_datetime'].time())
        self.arc_dict['end_round_angle'] = time_to_degrees(self.arc_dict['end_round_datetime'].time())
        self.arc_dict['arc_angle'] = self.arc_dict['end_angle'] - self.arc_dict['start_angle']
        self.arc_dict['arc_round_angle'] = self.arc_dict['end_round_angle'] - self.arc_dict['start_round_angle']

        BaseArc.columns = list(self.arc_dict.keys())

        self.zero_angle = False
        self.next_day_arc = False


class Arc(BaseArc):

    def __init__(self, args: dict):
        super().__init__(args)

        end_day_one = self.arc_dict['start_datetime'].date() == self.arc_dict['end_datetime'].date()
        end_equals_midnight = self.arc_dict['end_round_angle'] == 360.0 or self.arc_dict['end_round_angle'] == 0.0

        # absolutely must split into to arcs, implies creation of a next_day_arc
        # start day and end day are different and arc doesn't end just over the line on the next day
        if not end_day_one and not end_equals_midnight:

            #  copy args for next day arc
            new_args = deepcopy(args)

            #  reset current day end to midnight
            self.arc_dict['end_datetime'] = self.arc_dict['start_datetime'].replace(hour=0, minute=0)  # force end date to start date
            self.arc_dict['end_round_datetime'] = self.arc_dict['end_datetime']
            self.arc_dict['end_angle'] = time_to_degrees(self.arc_dict['end_datetime'].time())
            self.arc_dict['end_round_angle'] = time_to_degrees(self.arc_dict['end_round_datetime'].time())
            self.arc_dict['end_et'] = None

            #  set next day start point to midnight
            new_args['start_datetime'] = (new_args['start_datetime'] + td(days=1)).replace(hour=0, minute=0)
            new_args['start_round_datetime'] = new_args['start_datetime']
            new_args['start_angle'] = time_to_degrees(new_args['start_datetime'].time())
            new_args['start_round_angle'] = time_to_degrees(new_args['start_round_datetime'].time())
            new_args['start_et'] = None

            if not self.arc_dict['min_datetime'] is None:
                #  if minima is in the start day, zero out the minima for the next day
                if self.arc_dict['min_datetime'].date() == self.arc_dict['start_datetime'].date():
                    new_args['min_angle'] = None
                    new_args['min_datetime'] = None
                    new_args['min_round_datetime'] = None
                    new_args['min_round_angle'] = None
                    new_args['min_et'] = None
                elif self.arc_dict['min_datetime'].date() == self.arc_dict['end_datetime'].date():
                    #  if minima is in the next day, zero out start day minima
                    self.arc_dict['min_angle'] = None
                    self.arc_dict['min_datetime'] = None
                    self.arc_dict['min_round_datetime'] = None
                    self.arc_dict['min_round_angle'] = None
                    self.arc_dict['min_et'] = None

            self.next_day_arc = Arc(new_args)

        #  arc starts on first day and ends just over the line the next day, reset end date to first day
        if not end_day_one and end_equals_midnight:
            self.arc_dict['end_datetime'] = self.arc_dict['start_datetime'].replace(hour=0, minute=0)  # force end date to start date
            self.arc_dict['end_round_datetime'] = self.arc_dict['end_datetime']
            self.arc_dict['end_angle'] = 360
            self.arc_dict['end_round_angle'] = 360

        # zero angle arc - start and end are on the same day and the angle difference is 0 or 360
        # doesn't matter if their midnight or not
        # purge from list later
        if end_day_one:
            angle_round_difference = self.arc_dict['end_round_angle'] - self.arc_dict['start_round_angle']
            if angle_round_difference == 360.0 or angle_round_difference == 0:
                self.zero_angle = True
