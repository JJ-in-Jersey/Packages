from datetime import timedelta as td
from tt_date_time_tools.date_time_tools import time_to_degrees
from copy import deepcopy

from tt_exceptions.exceptions import DateMismatch


class Arc:

    arguments = {'start_time', 'start_duration', 'min_time', 'min_duration', 'end_time', 'end_duration'}
    midnight_tolerance = 1.25  # in degrees, = 5 minutes

    @property
    def arc_dict(self):
        return vars(self)  # or return self.__dict__


    def __init__(self, **kwargs):

        if set(kwargs.keys()) != self.arguments:
            raise ValueError(f"Expected keys: {self.arguments}")
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.start_duration_display = True
        self.min_duration_display = True
        self.end_duration_display = True

        self.start_angle = time_to_degrees(self.start_time)
        if abs(self.start_angle) % 360 <= self.midnight_tolerance:
            self.start_duration_display = False

        self.min_angle = time_to_degrees(self.min_time)
        if abs(self.min_angle) % 360 <= self.midnight_tolerance:
            self.min_duration_display = False

        self.end_angle = time_to_degrees(self.end_time)
        if abs(self.end_angle) % 360 <= self.midnight_tolerance:
            self.end_duration_display = False

        self.total_angle = abs(self.end_angle - self.start_angle) % 360

        if self.start_time.date() != self.end_time.date():
            raise DateMismatch(f'     {self.__class__} start and end days are different')

        # if self.total_angle % 360 <= 0:
        #     raise LengthMismatch(f'     {self.__class__} Ignoring arc length pf {self.total_angle} degrees, {self.total_angle/0.25} minutes')


class StartArc(Arc):

    def __init__(self, **kwargs):

        ets = kwargs['end_time']
        kwargs['start_time'] = kwargs['start_time'].replace(hour = 0, minute=0, year=ets.year, month=ets.month, day=ets.day)
        if kwargs['min_time'].date() != ets.date():
            kwargs['min_time'] = kwargs['start_time']

        super().__init__(**kwargs)


class EndArc(Arc):

    def __init__(self, **kwargs):

        sts = kwargs['start_time']
        kwargs['end_time'] = kwargs['end_time'].replace(hour = 0, minute=0, year=sts.year, month=sts.month, day=sts.day)
        if kwargs['min_time'].date() != sts.date():
            kwargs['min_time'] = kwargs['end_time']

        super().__init__(**kwargs)
