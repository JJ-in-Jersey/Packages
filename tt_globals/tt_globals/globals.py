from dateparser import parse
from datetime import timedelta
from tt_date_time_tools.date_time_tools import int_timestamp as date_time_index


class Globals:

    YEAR = None

    FIRST_DOWNLOAD_DAY = None
    FIRST_DAY = None
    FIRST_DAY_INDEX = None
    FIRST_DAY_DATE = None

    LAST_DOWNLOAD_DAY = None
    LAST_DAY = None
    LAST_DAY_INDEX = None
    LAST_DAY_DATE = None

    DOWNLOAD_INDEX_RANGE = None
    ELAPSED_TIME_INDEX_RANGE =  None

    CHECKMARK = u'\N{check mark}'
    TIMESTEP = 15  # seconds
    WINDOW_MARGIN = 20  # time on either side of best, minutes
    TIMESTEP_MARGIN = int(WINDOW_MARGIN * 60 / TIMESTEP)  # number of timesteps to add to minimum to find edges of time windows
    FIVE_HOURS_OF_TIMESTEPS = int(5 * 3600 / TIMESTEP)  # transit time windows < midline at least 5 hours long (6 hour tide change)
    BOAT_SPEEDS = [v for v in range(-7, -2, 2)] + [v for v in range(3, 8, 2)]  # knots

    @staticmethod
    def initialize_dates(year):

        print('initializing globals')

        Globals.YEAR = year

        Globals.FIRST_DOWNLOAD_DAY = parse('12/1/' + str(Globals.YEAR - 1))
        Globals.FIRST_DAY = parse('1/1/' + str(Globals.YEAR))
        Globals.FIRST_DAY_INDEX = date_time_index(Globals.FIRST_DAY)
        Globals.FIRST_DAY_DATE = Globals.FIRST_DAY.date()

        Globals.LAST_DOWNLOAD_DAY = parse('2/1/' + str(Globals.YEAR + 1))
        Globals.LAST_DAY = parse('1/1/' + str(Globals.YEAR + 1))
        Globals.LAST_DAY_INDEX = date_time_index(Globals.LAST_DAY)
        Globals.LAST_DAY_DATE = Globals.LAST_DAY.date()

        Globals.DOWNLOAD_INDEX_RANGE = range(date_time_index(Globals.FIRST_DOWNLOAD_DAY), date_time_index(Globals.LAST_DOWNLOAD_DAY), Globals.TIMESTEP)
        Globals.ELAPSED_TIME_INDEX_RANGE =  range(date_time_index(Globals.FIRST_DOWNLOAD_DAY), date_time_index(Globals.LAST_DOWNLOAD_DAY - timedelta(weeks=1)), Globals.TIMESTEP)
        Globals.TRANSIT_TIME_INDEX_RANGE = range(date_time_index(Globals.FIRST_DOWNLOAD_DAY)), date_time_index(Globals.LAST_DOWNLOAD_DAY- timedelta(weeks=2), Globals.TIMESTEP)

    def __init__(self):
        pass
