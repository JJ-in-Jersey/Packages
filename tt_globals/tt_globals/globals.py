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

    def __init__(self):
        pass

