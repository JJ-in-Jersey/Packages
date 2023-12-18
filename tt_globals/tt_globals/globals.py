import dateparser as dp
from tt_date_time_tools.date_time_tools import int_timestamp as index


class Globals:

    YEAR = None

    FIRST_DAY = None
    FIRST_DAY_INDEX = None
    FIRST_DAY_DATE = None

    LAST_DAY = None
    LAST_DAY_INDEX = None
    LAST_DAY_DATE = None

    DOWNLOAD_INDEX_RANGE = None

    CHECKMARK = u'\N{check mark}'
    TIMESTEP = 15  # seconds
    TIME_RESOLUTION = 5  # time shown on chart, rounded to minutes
    WINDOW_MARGIN = 20  # time on either side of best, minutes
    TIMESTEP_MARGIN = int(WINDOW_MARGIN * 60 / TIMESTEP)  # number of timesteps to add to minimum to find edges of time windows
    FIVE_HOURS_OF_TIMESTEPS = int(5 * 3600 / TIMESTEP)  # transit time windows < midline at least 5 hours long (6 hour tide change)
    BOAT_SPEEDS = [v for v in range(-7, -2, 2)] + [v for v in range(3, 8, 2)]  # knots

    @staticmethod
    def initialize_dates(year):

        print('initializing globals')

        Globals.YEAR = year
        Globals.FIRST_DAY = dp.parse('1/1/' + str(Globals.YEAR))
        Globals.FIRST_DAY_INDEX = index(Globals.FIRST_DAY)
        Globals.FIRST_DAY_DATE = Globals.FIRST_DAY.date()
        Globals.LAST_DAY = dp.parse('1/1/' + str(Globals.YEAR + 1))
        Globals.LAST_DAY_INDEX = index(Globals.LAST_DAY)
        Globals.LAST_DAY_DATE = Globals.LAST_DAY.date()
        Globals.DOWNLOAD_INDEX_RANGE = range(index(dp.parse('12/1/' + str(year - 1) + ' 00:00:00')), index(dp.parse('2/1/' + str(year + 1) + ' 00:00:00')), Globals.TIMESTEP)

    def __init__(self):
        pass
