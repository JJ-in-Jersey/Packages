from tt_os_abstraction.os_abstraction import env
from os import makedirs
from string import Template

PROJECT_BASE_FOLDER = env('user_profile').joinpath('Fair Currents')
STATIONS_FOLDER = PROJECT_BASE_FOLDER.joinpath('stations')
STATIONS_FILE = STATIONS_FOLDER.joinpath('stations.json')
ROUTES_FOLDER = PROJECT_BASE_FOLDER.joinpath('routes')
WAYPOINTS_FOLDER = STATIONS_FOLDER.joinpath('waypoints')
GPX_FOLDER = STATIONS_FOLDER.joinpath('gpx')
SOURCE_BASE_FOLDER = env('user_profile').joinpath('PycharmProjects').joinpath('Fair-Currents')
TEMPLATES_FOLDER = SOURCE_BASE_FOLDER.joinpath('templates')

CHECKMARK = u'\N{check mark}'

TIMESTEP = 60  # 60 seconds, one minute
SPEEDS = [-10 + v for v in range(0, 8)] + [3 + v for v in range(0, 8)]

TEMPLATES= {
    'ElapsedTimeFrame': Template('elapsed_timesteps $speed.csv'),
    'TimeStepsFrame': Template('transit_timesteps $speed.csv'),
    'SavGolFrame': Template('savitsky_golay $speed.csv'),
    'FairCurrentFrame': Template('fair_current $speed.csv'),
    'SavGolMinimaFrame': Template('savitsky_golay_minima $speed.csv'),
    'FairCurrentMinimaFrame': Template('fair_current_minima $speed.csv'),
    'ArcsFrame': Template('arcs $speed.csv'),
    'transit_times': Template('transit_times $speed.csv'),
    'first_day': Template('$year/12/1'),
    'last_day': Template('$year/1/31')
}

def make_project_folders():
    makedirs(PROJECT_BASE_FOLDER, exist_ok=True)
    makedirs(STATIONS_FOLDER, exist_ok=True)
    makedirs(ROUTES_FOLDER.routes_folder, exist_ok=True)
    makedirs(WAYPOINTS_FOLDER.waypoints_folder, exist_ok=True)
    makedirs(GPX_FOLDER.gpx_folder, exist_ok=True)
