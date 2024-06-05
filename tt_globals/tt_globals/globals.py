from dateparser import parse
from datetime import timedelta
from tt_date_time_tools.date_time_tools import int_timestamp as date_time_index
from tt_os_abstraction.os_abstraction import env
import shutil
from os import makedirs
from num2words import num2words


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
    ELAPSED_TIME_INDEX_RANGE = None
    TRANSIT_TIME_INDEX_RANGE = None

    PROJECT_FOLDER = None
    WAYPOINTS_FOLDER = None
    EDGES_FOLDER = None
    TRANSIT_TIMES_FOLDER = None

    EXPECTED_HARMONIC_DATETIMES = None

    CHECKMARK = u'\N{check mark}'
    TIMESTEP = 15  # seconds
    WINDOW_MARGIN = 15  # minutes on either side of best time
    TIMESTEP_MARGIN = int(WINDOW_MARGIN * 60 / TIMESTEP)  # number of timesteps to add to minimum to find edges of time windows
    BOAT_SPEEDS = [v for v in range(-7, -2, 2)] + [v for v in range(3, 8, 2)]  # knots

    @staticmethod
    def initialize_dates(args):
        print('\nInitializing globals dates')

        Globals.YEAR = args['year']

        Globals.FIRST_DOWNLOAD_DAY = parse('11/1/' + str(Globals.YEAR - 1))
        Globals.FIRST_DAY = parse('12/1/' + str(Globals.YEAR - 1))
        Globals.FIRST_DAY_INDEX = date_time_index(Globals.FIRST_DAY)
        Globals.FIRST_DAY_DATE = Globals.FIRST_DAY.date()

        Globals.LAST_DOWNLOAD_DAY = parse('3/1/' + str(Globals.YEAR + 1)) - timedelta(hours=1)
        Globals.LAST_DAY = parse('1/31/' + str(Globals.YEAR + 1))
        Globals.LAST_DAY_INDEX = date_time_index(Globals.LAST_DAY)
        Globals.LAST_DAY_DATE = Globals.LAST_DAY.date()

        Globals.DOWNLOAD_INDEX_RANGE = range(date_time_index(Globals.FIRST_DOWNLOAD_DAY), date_time_index(Globals.LAST_DOWNLOAD_DAY), Globals.TIMESTEP)
        Globals.ELAPSED_TIME_INDEX_RANGE = range(date_time_index(Globals.FIRST_DOWNLOAD_DAY), date_time_index(Globals.LAST_DOWNLOAD_DAY - timedelta(weeks=1)), Globals.TIMESTEP)
        Globals.TRANSIT_TIME_INDEX_RANGE = range(date_time_index(Globals.FIRST_DOWNLOAD_DAY), date_time_index(Globals.LAST_DOWNLOAD_DAY - timedelta(weeks=2)), Globals.TIMESTEP)

        Globals.EXPECTED_HARMONIC_DATETIMES = [Globals.FIRST_DOWNLOAD_DAY + timedelta(hours=index) for index in range(0, (Globals.LAST_DOWNLOAD_DAY - Globals.FIRST_DOWNLOAD_DAY).days*24)]

    @staticmethod
    def initialize_folders(args):
        print('\nInitializing globals folders')

        Globals.PROJECT_FOLDER = env('user_profile').joinpath('Developer Workspace/' + args['project_name'] + '_' + str(Globals.YEAR) + '/')

        if args['delete_data']:
            shutil.rmtree(Globals.PROJECT_FOLDER, ignore_errors=True)

        Globals.WAYPOINTS_FOLDER = Globals.PROJECT_FOLDER.joinpath('Waypoints')
        Globals.EDGES_FOLDER = Globals.PROJECT_FOLDER.joinpath('Edges')
        Globals.TRANSIT_TIMES_FOLDER = Globals.PROJECT_FOLDER.joinpath('Transit Times')

        makedirs(Globals.PROJECT_FOLDER, exist_ok=True)
        makedirs(Globals.WAYPOINTS_FOLDER, exist_ok=True)
        makedirs(Globals.EDGES_FOLDER, exist_ok=True)
        makedirs(Globals.TRANSIT_TIMES_FOLDER, exist_ok=True)

        for s in Globals.BOAT_SPEEDS:
            makedirs(Globals.TRANSIT_TIMES_FOLDER.joinpath(num2words(s)), exist_ok=True)

    def __init__(self):
        pass
