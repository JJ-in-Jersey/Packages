from datetime import datetime as dt

import pandas as pd
from datetime import timedelta
from tt_date_time_tools.date_time_tools import date_to_index
from tt_file_tools.file_tools import read_df, write_df, print_file_exists
from tt_os_abstraction.os_abstraction import env
from os import makedirs
from num2words import num2words

class PresetGlobals:

    project_base_folder = env('user_profile').joinpath('Fair Currents')
    stations_folder = project_base_folder.joinpath('stations')
    stations_file = stations_folder.joinpath('stations.json')
    routes_folder = project_base_folder.joinpath('routes')
    waypoints_folder = stations_folder.joinpath('waypoints')
    gpx_folder = stations_folder.joinpath('gpx')

    source_base_folder = env('user_profile').joinpath('PycharmProjects').joinpath('Fair-Currents')
    templates_folder = source_base_folder.joinpath('templates')

    checkmark = u'\N{check mark}'

    timestep = 60  # one minute
    speeds = [-9.0 + v for v in range(0, 7)] + [3.0 + v for v in range(0, 7)]
    time_window_scale = 1.5

    @staticmethod
    def make_folders():
        makedirs(PresetGlobals.project_base_folder, exist_ok=True)
        makedirs(PresetGlobals.stations_folder, exist_ok=True)
        makedirs(PresetGlobals.routes_folder, exist_ok=True)
        makedirs(PresetGlobals.waypoints_folder, exist_ok=True)
        makedirs(PresetGlobals.gpx_folder, exist_ok=True)

    def __init__(self):
        pass


class Globals:

    edges_folder = None
    transit_times_folder = None

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



    def initialize_dates(self, args):
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
    def create_location_folders(project_name:str, year:int):
        print('\nInitializing location folders')

        project =  Globals.project_base_folder.joinpath(project_name + '_' + str(year))
        Globals.edges_folder = None if project_name is None else project.joinpath('edges')
        Globals.transit_times_folder = None if project_name is None else project.joinpath('transit times')

        makedirs(Globals.edges_folder, exist_ok=True)
        makedirs(Globals.transit_times_folder, exist_ok=True)

        for s in Globals.speeds:
            makedirs(Globals.transit_times_folder.joinpath(num2words(s)), exist_ok=True)

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
