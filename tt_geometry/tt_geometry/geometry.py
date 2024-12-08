from datetime import timedelta as td
from tt_date_time_tools.date_time_tools import time_to_degrees
from copy import deepcopy


class BaseArc:

    columns = None

    def info(self):
        return self.arc_dict

    def __init__(self, args):

        self.zero_angle = False
        self.next_day_arc = None

        self.arc_dict = {
            'start_eastern': None, 'min_eastern': None, 'end_eastern': None,
            'start_round': None, 'min_round': None, 'end_round': None,
            'start_tt': None, 'min_tt': None, 'end_tt': None,
            'start_angle':None, 'min_angle': None, 'end_angle': None,
            'start_round_angle': None, 'min_round_angle': None, 'end_round_angle': None
        }

        for key in args.keys():
            self.arc_dict[key] = args[key]

        self.arc_dict['start_angle'] = time_to_degrees(self.arc_dict['start_eastern'].time())
        self.arc_dict['start_round_angle'] = time_to_degrees(self.arc_dict['start_round'].time())
        self.arc_dict['end_angle'] = time_to_degrees(self.arc_dict['end_eastern'].time())
        self.arc_dict['end_round_angle'] = time_to_degrees(self.arc_dict['end_round'].time())

        if not self.arc_dict['min_eastern'] is None:
            self.arc_dict['min_angle'] = time_to_degrees(self.arc_dict['min_eastern'].time())
            if not self.arc_dict['min_round'] is None:
                self.arc_dict['min_round_angle'] = time_to_degrees(self.arc_dict['min_round'].time())
                # if min is at midnight, don't display it
                if  abs(self.arc_dict['min_round_angle']) == 360.0 or abs(self.arc_dict['min_round_angle']) == 0.0:
                    self.arc_dict['min_tt'] = None

        BaseArc.columns = list(self.arc_dict.keys())


class Arc(BaseArc):

    def __init__(self, args: dict):
        super().__init__(args)

        start_and_end_on_same_day = self.arc_dict['start_eastern'].date() == self.arc_dict['end_eastern'].date()
        start_and_min_on_same_day = not self.arc_dict['min_eastern'] is None and self.arc_dict['start_eastern'].date() == self.arc_dict['min_eastern'].date()

        # create a copy of the arguments before any adjustments in case we add a next day
        next_day_args = deepcopy(args)

        if start_and_end_on_same_day:
            starts_at_midnight = abs(self.arc_dict['start_round_angle']) == 360.0 or abs(self.arc_dict['start_round_angle']) == 0.0
            ends_at_midnight = abs(self.arc_dict['end_round_angle']) == 360.0 or abs(self.arc_dict['end_round_angle']) == 0.0
            # same day, but starts at midnight
            if starts_at_midnight:
                self.arc_dict['start_eastern'] = self.arc_dict['start_eastern'].replace(hour=0, minute=0)
                self.arc_dict['start_round'] = self.arc_dict['start_eastern']
                self.arc_dict['start_angle'] = 0.0
                self.arc_dict['start_round_angle'] = 0.0
                self.arc_dict['start_tt'] = None

            #  same day, but ends near midnight
            if ends_at_midnight:
                self.arc_dict['end_eastern'] = self.arc_dict['start_eastern'].replace(hour=0, minute=0)
                self.arc_dict['end_round'] = self.arc_dict['end_eastern']
                self.arc_dict['end_angle'] = 360.0
                self.arc_dict['end_round_angle'] = 360.0
                self.arc_dict['end_tt'] = None

        # start day and end day are different
        # must split into two arcs
        if not start_and_end_on_same_day:

            # create arguments for next day arc, starts at midnight
            next_day_args['start_eastern'] = (next_day_args['start_eastern'] + td(days=1)).replace(hour=0, minute=0)
            next_day_args['start_round'] = next_day_args['start_eastern']  # same as above
            next_day_args['start_angle'] = 0.0
            next_day_args['start_round_angle'] = 0.0
            next_day_args['start_tt'] = None  # because et was for start in prior day

            #  reset current day, ends at midnight
            self.arc_dict['end_eastern'] = self.arc_dict['start_eastern'].replace(hour=0, minute=0)
            self.arc_dict['end_round'] = self.arc_dict['end_eastern']  # same as above
            self.arc_dict['end_angle'] = 360.0
            self.arc_dict['end_round_angle'] = 360.0
            self.arc_dict['end_tt'] = None  # because the et was for end in the next day

            # if minima exists and is on the start day side
            if start_and_min_on_same_day:
                next_day_args['min_angle'] = None
                next_day_args['min_round_angle'] = None
                next_day_args['min_eastern'] = None
                next_day_args['min_round'] = None
                next_day_args['min_tt'] = None


            # if minima exists and is on the next day side
            if not start_and_min_on_same_day:
                self.arc_dict['min_angle'] = None
                self.arc_dict['min_round_angle'] = None
                self.arc_dict['min_eastern'] = None
                self.arc_dict['min_round'] = None
                self.arc_dict['min_tt'] = None

            self.next_day_arc = Arc(next_day_args)

        # zero angle arc - start and end are on the same day and the angle difference is 0 or 360
        # doesn't matter if their midnight or not
        # purge from list later
        angle_round_difference = self.arc_dict['end_round_angle'] - self.arc_dict['start_round_angle']
        if abs(angle_round_difference) == 360.0 or abs(angle_round_difference) == 0.0:
                self.zero_angle = True
