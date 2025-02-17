from datetime import datetime as dt

import pandas as pd
from datetime import timedelta
from tt_date_time_tools.date_time_tools import date_to_index
from tt_file_tools.file_tools import read_df, write_df, print_file_exists
from tt_os_abstraction.os_abstraction import env
import shutil
from os import makedirs
from num2words import num2words


class Globals:

    TYPE = {'rte': 'route', 'wpt': 'point'}

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
    TEMPLATE_ELAPSED_TIME_DATAFRAME = None
    TRANSIT_TIME_INDEX_RANGE = None
    TEMPLATE_TRANSIT_TIME_DATAFRAME = None

    PROJECT_FOLDER = None
    WAYPOINTS_FOLDER = None
    EDGES_FOLDER = None
    TRANSIT_TIMES_FOLDER = None

    NORMALIZED_DOWNLOAD_DATES = None
    NORMALIZED_DOWNLOAD_INDICES = None

    CHECKMARK = u'\N{check mark}'
    TIMESTEP = 15  # seconds
    BOAT_SPEEDS = [-9.0 + v for v in range(0, 7)] + [3.0 + v for v in range(0, 7)]  # knots
    TIME_WINDOW_SCALE_FACTOR = 1.5

    WAYPOINT_DATAFILE_NAME = 'normalized_velocity.csv'
    EDGE_DATAFILE_NAME = 'normalized_velocity_spline_fit.csv'

    @staticmethod
    def initialize_dates(args):
        print('\nInitializing globals dates')

        Globals.YEAR = args['year']

        Globals.FIRST_DOWNLOAD_DAY = dt(Globals.YEAR - 1, 11, 1)
        Globals.FIRST_DAY = dt(Globals.YEAR - 1, 12, 1)

        Globals.FIRST_DAY_INDEX = date_to_index(Globals.FIRST_DAY)
        Globals.FIRST_DAY_DATE = Globals.FIRST_DAY.date()

        Globals.LAST_DOWNLOAD_DAY = dt(Globals.YEAR + 1, 3, 1)
        Globals.LAST_DAY = dt(Globals.YEAR + 1, 1, 31)
        
        Globals.LAST_DAY_INDEX = date_to_index(Globals.LAST_DAY)
        Globals.LAST_DAY_DATE = Globals.LAST_DAY.date()

        Globals.DOWNLOAD_INDEX_RANGE = range(date_to_index(Globals.FIRST_DOWNLOAD_DAY), date_to_index(Globals.LAST_DOWNLOAD_DAY + timedelta(days=1)), Globals.TIMESTEP)
        Globals.ELAPSED_TIME_INDEX_RANGE = range(date_to_index(Globals.FIRST_DOWNLOAD_DAY), date_to_index(Globals.LAST_DOWNLOAD_DAY - timedelta(days=6)), Globals.TIMESTEP)
        Globals.TRANSIT_TIME_INDEX_RANGE = range(date_to_index(Globals.FIRST_DOWNLOAD_DAY), date_to_index(Globals.LAST_DOWNLOAD_DAY - timedelta(days=13)), Globals.TIMESTEP)

        Globals.NORMALIZED_DOWNLOAD_DATES = [Globals.FIRST_DOWNLOAD_DAY + timedelta(hours=index) for index in range(0, ((Globals.LAST_DOWNLOAD_DAY - Globals.FIRST_DOWNLOAD_DAY).days + 1)*24)]
        Globals.NORMALIZED_DOWNLOAD_INDICES = [date_to_index(Globals.FIRST_DOWNLOAD_DAY + timedelta(hours=index)) for index in range(0, ((Globals.LAST_DOWNLOAD_DAY - Globals.FIRST_DOWNLOAD_DAY).days + 1)*24)]

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

    @staticmethod
    def initialize_structures():
        print('\nInitializing globals structures')

        et_path = Globals.PROJECT_FOLDER.joinpath('template_elapsed_time_dataframe.csv')
        if et_path.exists():
            Globals.TEMPLATE_ELAPSED_TIME_DATAFRAME = read_df(et_path)
        else:
            Globals.TEMPLATE_ELAPSED_TIME_DATAFRAME = pd.DataFrame(data={'departure_index': Globals.ELAPSED_TIME_INDEX_RANGE})
            Globals.TEMPLATE_ELAPSED_TIME_DATAFRAME['date_time'] = pd.to_datetime(Globals.TEMPLATE_ELAPSED_TIME_DATAFRAME['departure_index'], unit='s').round('min')
            write_df(Globals.TEMPLATE_ELAPSED_TIME_DATAFRAME, et_path)
        print_file_exists(et_path)

        tt_path = Globals.PROJECT_FOLDER.joinpath('template_transit_time_dataframe.csv')
        if tt_path.exists():
            Globals.TEMPLATE_TRANSIT_TIME_DATAFRAME = read_df(tt_path)
        else:
            Globals.TEMPLATE_TRANSIT_TIME_DATAFRAME = pd.DataFrame(data={'departure_index': Globals.TRANSIT_TIME_INDEX_RANGE})
            Globals.TEMPLATE_TRANSIT_TIME_DATAFRAME['date_time'] = pd.to_datetime(Globals.TEMPLATE_TRANSIT_TIME_DATAFRAME['departure_index'], unit='s').round('min')
            write_df(Globals.TEMPLATE_TRANSIT_TIME_DATAFRAME, tt_path)
        print_file_exists(tt_path)

    def __init__(self):
        pass
