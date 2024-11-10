from bs4 import BeautifulSoup as Soup
from tt_navigation.navigation import distance, directions, Heading
from tt_file_tools.file_tools import read_df, write_df, print_file_exists
from tt_jobs.jobs import InterpolatePointJob
from tt_globals.globals import Globals
from os import makedirs
from pathlib import Path
import pandas as pd

class Waypoint:
    waypoints_folder = None
    color = {'TideStationWP': 'Yellow', 'CurrentStationWP': 'Orange',
             'LocationWP': 'Green', 'InterpolatedWP': 'Blue',
             'InterpolatedDataWP': 'Black'}
    ordinal_number = 0
    index_lookup = {}
    name_lookup = {}

    def __init__(self, gpxtag):
        self.lat = round(float(gpxtag.attrs['lat']), 4)
        self.lon = round(float(gpxtag.attrs['lon']), 4)
        self.index = self.ordinal_number
        self.coords = tuple([self.lat, self.lon])
        self.symbol = gpxtag.sym.text
        if 'Spot' in gpxtag.sym.text:
            self.type = 'Harmonic'
        elif 'Circle' in gpxtag.sym.text:
            self.type = 'Subordinate'
        self.name = gpxtag.find('name').text.strip('\n')
        self.unique_name = str(self.index) + '_' + self.name.split(',')[0].split('(')[0].replace('.', '').strip().replace(" ", "_")
        self.prev_edge = None
        self.next_edge = None

        self.folder = Waypoint.waypoints_folder.joinpath(self.unique_name)
        makedirs(self.folder, exist_ok=True)

        self.index_lookup[self.index] = self
        Waypoint.ordinal_number += 1


class LocationWP(Waypoint):
    def __init__(self, *args):
        super().__init__(*args)


class DownloadedDataWP(Waypoint):

    def __init__(self, gpxtag):
        super().__init__(gpxtag)

        self.code = None
        self.bin_no = None

        if gpxtag.link:
            self.noaa_url = gpxtag.find('link').attrs['href']
            tagname = gpxtag.find('link').find('text').text.split(' ')[0]
            tagsplit = tagname.split('_')
            self.code = tagsplit[0]
            self.bin_no = None if len(tagsplit) == 1 else tagsplit[-1]


class EdgeNode(DownloadedDataWP):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class TideStationWP(DownloadedDataWP):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class SurrogateWP(EdgeNode):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class CurrentStationWP(EdgeNode):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedDataWP(DownloadedDataWP):  # downloaded data used to interpolate a location
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedWP(EdgeNode):  # result of interpolation of other waypoint data

    def create_data_waypoint_list(self):
        index = self.index + 1
        while index <= max(Waypoint.index_lookup) and isinstance(Waypoint.index_lookup[index], InterpolatedDataWP):
            self.data_waypoints.append(Waypoint.index_lookup[index])
            index += 1

    def interpolate(self, job_manager):

        output_filepath = self.folder.joinpath('interpolated_velocity.csv')

        if not output_filepath.exists():
            velocity_data = []
            for i, wp in enumerate(self.data_waypoints):
                velocity_data.append(read_df(wp.folder.joinpath(Globals.WAYPOINT_DATAFILE_NAME)))
                velocity_data[i]['lat'] = wp.lat
                velocity_data[i]['lon'] = wp.lon
                print(i, len(velocity_data[i]), wp.name)

            keys = [job_manager.put(InterpolatePointJob(self, velocity_data, i)) for i in range(len(velocity_data[0]))]
            job_manager.wait()

            result_array = tuple([job_manager.get(key).date_velocity for key in keys])
            frame = pd.DataFrame(result_array, columns=['date_index', 'velocity'])
            frame.sort_values('date_index', inplace=True)
            frame['date_time'] = pd.to_datetime(frame['date_index'], unit='s').round('min')
            frame.reset_index(drop=True, inplace=True)
            write_df(frame, output_filepath)

        if print_file_exists(output_filepath):
            write_df(read_df(output_filepath), self.folder.joinpath(Globals.WAYPOINT_DATAFILE_NAME))

    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.data_waypoints = []


class Edge:  # connection between waypoints with current data

    edges_folder = None
    edge_range = None

    def __init__(self, start_wp, end_wp):
        self.final_data_filepath = None
        self.elapsed_time_data = None
        self.length = 0

        if start_wp == end_wp:
            raise IndexError
        if not isinstance(start_wp, CurrentStationWP) and not isinstance(start_wp, InterpolatedWP) and not isinstance(start_wp, SurrogateWP):
            raise TypeError
        if not isinstance(end_wp, CurrentStationWP) and not isinstance(end_wp, InterpolatedWP) and not isinstance(end_wp, SurrogateWP):
            raise TypeError

        self.unique_name = '[' + str(start_wp.unique_name) + '-' + str(end_wp.unique_name) + ']'
        self.start = start_wp
        self.end = end_wp
        start_wp.next_edge = self
        end_wp.prev_edge = self

        if Edge.edges_folder is None:
            raise TypeError
        self.folder = Edge.edges_folder.joinpath(self.unique_name)
        makedirs(self.folder, exist_ok=True)

        wp1 = start_wp
        while not wp1 == end_wp:
            wp2 = Waypoint.index_lookup[wp1.index + 1]
            while isinstance(wp2, InterpolatedDataWP) or isinstance(wp2, TideStationWP):
                wp2 = Waypoint.index_lookup[wp2.index + 1]
            self.length += round(distance(wp1.coords, wp2.coords), 4)
            wp1 = wp2


class GPXPath:

    def path_integrity(self):
        for i, edge in enumerate(self.edges[:-1]):
            if not edge.end == self.edges[i + 1].start:
                raise RecursionError

    def __init__(self, edges):
        self.edges = edges
        self.path_integrity()
        self.name = '{' + str(self.edges[0].start.index) + '-' + str(self.edges[-1].end.index) + '}'
        self.length = round(sum([edge.length for edge in self.edges]), 4)
        self.route_heading = Heading(self.edges[0].start.coords, self.edges[-1].end.coords).angle
        self.direction = directions(self.route_heading)[0]


class Route:

    def __init__(self, tree):
        self.location_name = None
        self.location_code = None
        self.transit_time_csv_to_speed = {}
        self.rounded_transit_time_csv_to_speed = {}
        self.elapsed_time_csv_to_speed = {}
        self.whole_path = self.velo_path = None
        self.interpolation_groups = None
        self.waypoints = None

        # build ordered list of all waypoints
        waypoints = []
        for tag in tree.find_all('rtept'):
            if Waypoint.color['TideStationWP'] in tag.sym.text:
                waypoints.append(TideStationWP(tag))
            elif Waypoint.color['CurrentStationWP'] in tag.sym.text:
                waypoints.append(CurrentStationWP(tag))
            elif Waypoint.color['LocationWP'] in tag.sym.text:
                waypoints.append(LocationWP(tag))
            elif Waypoint.color['InterpolatedWP'] in tag.sym.text:
                waypoints.append(InterpolatedWP(tag))
            elif Waypoint.color['InterpolatedDataWP'] in tag.sym.text:
                waypoints.append(InterpolatedDataWP(tag))
        self.waypoints = waypoints

        # populate interpolated waypoint data
        for iwp in filter(lambda w: isinstance(w, InterpolatedWP), waypoints):
            iwp.create_data_waypoint_list()

        # create edges
        edge_nodes = [wp for wp in waypoints if isinstance(wp, EdgeNode)]
        self.edges = [Edge(wp, edge_nodes[i+1]) for i, wp in enumerate(edge_nodes[:-1])]

        self.edge_path = GPXPath(self.edges)


class GpxFile:

    @staticmethod
    def write_clean_gpx(filepath, tree):
        new_filepath = filepath.parent.joinpath(filepath.stem + ' new.gpx')
        tag_names = ['extensions', 'time']
        for name in tag_names:
            for tag in tree.find_all(name):
                tag.decompose()
        with open(new_filepath, "w") as file:
            file.write(tree.prettify())

    def __init__(self, filepath: Path):
        self.tree = None
        self.type = None

        with open(filepath, 'r') as f:
            gpxfile = f.read()
        self.tree = Soup(gpxfile, 'xml', preserve_whitespace_tags=['name', 'type', 'sym', 'text'])

        if len(self.tree.find_all('rte')) == 1:
            self.type = Globals.TYPE['rte']
        elif len(self.tree.find_all('wpt')) == 1:
            self.type = Globals.TYPE['wpt']

        GpxFile.write_clean_gpx(filepath, self.tree)
