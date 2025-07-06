from tt_os_abstraction.os_abstraction import env
from os import makedirs


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

    timestep = 60  # 60 seconds, one minute
    speeds = [-10 + v for v in range(0, 8)] + [3 + v for v in range(0, 8)]
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
