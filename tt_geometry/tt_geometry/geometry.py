from tt_date_time_tools.date_time_tools import time_to_degrees


class Arc:

    arguments = {'start_datetime', 'start_duration', 'min_datetime', 'min_duration', 'end_datetime', 'end_duration'}

    @property
    def arc_dict(self):
        return vars(self)  # or return self.__dict__


    def __init__(self, **kwargs):

        self.start_datetime = None
        self.end_datetime = None
        self.min_datetime = None

        if set(kwargs.keys()) != self.arguments:
            raise ValueError(f"Expected keys: {self.arguments}")
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.start_duration_display = True
        self.min_duration_display = True
        self.end_duration_display = True

        self.start_angle = time_to_degrees(self.start_datetime)
        self.min_angle = time_to_degrees(self.min_datetime)
        self.end_angle = time_to_degrees(self.end_datetime)

        self.total_angle = min(abs(self.end_angle - self.start_angle), 360 - abs(self.end_angle - self.start_angle))


class StartArc(Arc):

    def __init__(self, **kwargs):

        ets = kwargs['end_datetime']
        kwargs['start_datetime'] = kwargs['start_datetime'].replace(hour=0, minute=0, year=ets.year, month=ets.month, day=ets.day)
        if kwargs['min_datetime'].date() != ets.date():
            kwargs['min_datetime'] = kwargs['start_datetime']

        super().__init__(**kwargs)


class EndArc(Arc):

    def __init__(self, **kwargs):

        sts = kwargs['start_datetime']
        kwargs['end_datetime'] = kwargs['end_datetime'].replace(hour=0, minute=0, year=sts.year, month=sts.month, day=sts.day)
        if kwargs['min_datetime'].date() != sts.date():
            kwargs['min_datetime'] = kwargs['end_datetime']

        super().__init__(**kwargs)
