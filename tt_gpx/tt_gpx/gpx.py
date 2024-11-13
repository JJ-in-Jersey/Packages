from bs4 import BeautifulSoup as Soup
from os import makedirs
from pathlib import Path
import pandas as pd

from tt_navigation.navigation import distance, directions, Heading
from tt_file_tools.file_tools import read_df, write_df, print_file_exists, SoupFromXMLFile
from tt_jobs.jobs import InterpolatePointJob
from tt_globals.globals import PresetGlobals, Globals


class Waypoint:

    download_csv_name = 'downloaded_frame.csv'
    velocity_csv_name = 'velocity_frame.csv'
    spline_csv_name = 'cubic_spline_frame.csv'

    waypoint_template_gpx = PresetGlobals.templates_folder.joinpath('waypoint_template.gpx')

    types = {'H': 'Harmonic', 'S': 'Subordinate', 'W': 'Weak'}
    symbols = {'H': 'Symbol-Pin-Green', 'S': 'Symbol-Pin-Green', 'W': 'Symbol-Pin-Yellow'}

    ordinal_number = 0
    index_lookup = {}
    name_lookup = {}

    def write_gpx(self):
        soup = SoupFromXMLFile(self.waypoint_template_gpx).tree
        soup.find('name').string = self.name
        soup.find('wpt')['lat'] = self.lat
        soup.find('wpt')['lon'] = self.lon
        soup.find('type').string = self.type
        soup.find('sym').string = self.symbol

        id_tag = soup.new_tag('id')
        id_tag.string = self.id
        soup.find('name').insert_after(id_tag)

        folder_tag = soup.new_tag('folder')
        folder_tag.string = str(self.folder.absolute())
        soup.find('name').insert_after(folder_tag)

        desc_tag = soup.new_tag('desc')
        desc_tag.string = self.id
        soup.find('name').insert_after(desc_tag)

        filename = self.id + '.gpx'

        with open(self.folder.joinpath(filename), 'w') as a_file:
            a_file.write(str(soup))

        with open(PresetGlobals.gpx_folder.joinpath(filename), 'w') as a_file:
            a_file.write(str(soup))

    def __init__(self, station: dict):

        self.index = self.ordinal_number
        self.id = station['id']
        self.name = station['name']
        self.lat = round(float(station['lat']), 4)
        self.lon = round(float(station['lon']), 4)
        self.coords = tuple([self.lat, self.lon])
        self.type = station['type']
        self.symbol = self.symbols[station['type']]

        self.folder = PresetGlobals.waypoints_folder.joinpath(station['id'])
        self.download_csv = self.folder.joinpath(self.download_csv_name)
        self.velocity_csv = self.folder.joinpath(self.velocity_csv_name)
        self.spline_csv = self.folder.joinpath(self.spline_csv_name)
        makedirs(self.folder, exist_ok=True)

        self.prev_edge = None
        self.next_edge = None

        self.index_lookup[self.index] = self
        Waypoint.ordinal_number += 1


class LocationWP(Waypoint):
    def __init__(self, *args):
        super().__init__(*args)


class EdgeNode(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class SurrogateWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedDataWP(Waypoint):  # downloaded data used to interpolate a location
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedWP(Waypoint):  # result of interpolation of other waypoint data

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
        if not isinstance(start_wp, Waypoint) and not isinstance(start_wp, InterpolatedWP) and not isinstance(start_wp, SurrogateWP):
            raise TypeError
        if not isinstance(end_wp, Waypoint) and not isinstance(end_wp, InterpolatedWP) and not isinstance(end_wp, SurrogateWP):
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
            while isinstance(wp2, InterpolatedDataWP):
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
            code = tag.desc.text
            waypoints.append(Waypoint(code))
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
