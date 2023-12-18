import dateparser as dp
from tt_date_time_tools.date_time_tools import int_timestamp as index

YEAR = None

FIRST_DAY = None
FIRST_DAY_INDEX = None
FIRST_DAY_DATE = None

LAST_DAY = None
LAST_DAY_INDEX = None
LAST_DAY_DATE = None


class Globals:

    @staticmethod
    def initialize_dates(year):

        print('initializing globals')

        global YEAR
        global FIRST_DAY, FIRST_DAY_INDEX, FIRST_DAY_DATE
        global LAST_DAY, LAST_DAY_INDEX, LAST_DAY_DATE

        YEAR = year
        FIRST_DAY = dp.parse('1/1/' + str(YEAR))
        FIRST_DAY_INDEX = index(FIRST_DAY)
        FIRST_DAY_DATE = FIRST_DAY.date()
        LAST_DAY = dp.parse('1/1/' + str(YEAR + 1))
        LAST_DAY_INDEX = index(LAST_DAY)
        LAST_DAY_DATE = LAST_DAY.date()

    def __init__(self):
        pass

