from bs4 import BeautifulSoup as Soup
from tt_navigation.navigation import distance, direction, heading
from os import makedirs


class Waypoint:

    current_folder = None
    velocity_folder = None

    type = {'CurrentStationWP': 'Symbol-Spot-Orange', 'SurrogateWP': 'Symbol-Pin-Orange', 'LocationWP': 'Symbol-Spot-Green', 'InterpolatedWP': 'Symbol-Spot-Blue', 'InterpolatedDataWP': 'Symbol-Spot-Black'}
    ordinal_number = 0
    index_lookup = {}

    def __init__(self, gpxtag):

        self.lat = round(float(gpxtag.attrs['lat']), 4)
        self.lon = round(float(gpxtag.attrs['lon']), 4)
        self.index = Waypoint.ordinal_number
        self.coords = tuple([self.lat, self.lon])
        self.symbol = gpxtag.sym.text
        self.name = gpxtag.find('name').text.strip('\n')
        self.unique_name = self.name.split(',')[0].split('(')[0].replace('.', '').strip().replace(" ", "_") + '_' + str(self.index)
        self.prev_edge = None
        self.next_edge = None

        Waypoint.index_lookup[Waypoint.ordinal_number] = self
        Waypoint.ordinal_number += 1


class FileWP(Waypoint):  # used in battery validation
    def __init__(self, filepath):
        with open(filepath, 'r') as f: gpxfile = f.read()
        gpxtag = Soup(gpxfile, 'xml', preserve_whitespace_tags=['name', 'type', 'sym', 'text']).find('wpt')
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.code = str(gpxtag.find('link').find('text').text).split(' ')[0]
        super().__init__(gpxtag)


class TideWP(FileWP):  # used in battery validation
    def __init__(self, *args):
        super().__init__(*args)
        self.folder = Waypoint.current_folder.joinpath(self.unique_name)
        makedirs(self.folder, exist_ok=True)
        self.downloaded_data_filepath = self.folder.joinpath(self.unique_name + '_downloaded_data')
        self.final_data_filepath = self.folder.joinpath(self.unique_name + '_final_data_file')


class LocationWP(Waypoint):  # waypoints that define a location
    def __init__(self, *args):
        super().__init__(*args)


class DataWP(Waypoint):  # waypoints that get NOAA data and store it

    def __init__(self, gpxtag):
        super().__init__(gpxtag)

        if gpxtag.link:
            self.noaa_url = gpxtag.find('link').attrs['href']
            self.code = gpxtag.find('link').find('text').text.split(' ')[0]

        self.folder = Waypoint.velocity_folder.joinpath(self.unique_name)
        makedirs(self.folder, exist_ok=True)

        self.downloaded_current_path = self.folder.joinpath(self.unique_name + '_downloaded_current_data')
        self.spline_fit_current_path = self.folder.joinpath(self.unique_name + '_spline_fit_current_data')
        self.downloaded_tide_path = self.folder.joinpath(self.unique_name + '_downloaded_tide_data')

        self.downloaded_current_data = None
        self.spline_fit_current_data = None
        self.downloaded_tide_data = None


class CurrentStationWP(DataWP):  # CurrentWP who's data is used to calculate elapsed time
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedDataWP(DataWP):  # CurrentWP that downloads data used for interpolation
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedWP(DataWP):  # CurrentCalculationWP that calculates data used to calculate elapsed time

    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class Edge:  # connection between calculation waypoints

    elapsed_time_folder = None
    edge_range = None

    def __init__(self, start_wp, end_wp):
        self.final_data_filepath = None
        self.elapsed_time_data = None
        self.length = 0

        if start_wp == end_wp: raise IndexError
        if not isinstance(start_wp, CurrentStationWP) and not isinstance(start_wp, InterpolatedWP): raise TypeError
        if not isinstance(end_wp, CurrentStationWP) and not isinstance(end_wp, InterpolatedWP): raise TypeError

        self.unique_name = '[' + str(start_wp.index) + '-' + str(end_wp.index) + ']'
        self.start = start_wp
        self.end = end_wp
        start_wp.next_edge = self
        end_wp.prev_edge = self

        if Edge.elapsed_time_folder is None: raise TypeError
        self.folder = Edge.elapsed_time_folder.joinpath(self.unique_name)
        makedirs(self.folder, exist_ok=True)

        wp1 = start_wp
        while not wp1 == end_wp:
            wp2 = Waypoint.index_lookup[wp1.index + 1]
            while isinstance(wp2, InterpolatedDataWP):
                wp2 = Waypoint.index_lookup[wp2.index + 1]
            self.length += round(distance(wp1.coords, wp2.coords), 4)
            wp1 = wp2


class Path:

    def path_integrity(self):
        for i, edge in enumerate(self.edges[:-1]):
            if not edge.end == self.edges[i+1].start:
                raise RecursionError

    def __init__(self, edges):
        self.edges = edges
        self.path_integrity()
        self.name = '{' + str(self.edges[0].start.index) + '-' + str(self.edges[-1].end.index) + '}'
        self.length = round(sum([edge.length for edge in self.edges]), 4)
        self.direction = direction(self.edges[0].start.coords, self.edges[-1].end.coords)
        self.heading = heading(self.edges[0].start.coords, self.edges[-1].end.coords)


class Route:

    def __init__(self, filepath, edge_range):
        Edge.edge_range = edge_range
        self.transit_time_lookup = {}
        self.elapsed_time_lookup = {}
        self.whole_path = self.velo_path = None
        self.interpolation_groups = None
        self.waypoints = None
        self.filepath = filepath

        with open(filepath, 'r') as f: gpxfile = f.read()
        tree = Soup(gpxfile, 'xml', preserve_whitespace_tags=['name', 'type', 'sym', 'text'])
        self.write_clean_gpx(filepath, tree)

        # build ordered list of all waypoints
        waypoints = []
        for tag in tree.find_all('rtept'):
            if tag.sym.text == Waypoint.type['CurrentStationWP']: waypoints.append(CurrentStationWP(tag))
            elif tag.sym.text == Waypoint.type['SurrogateWP']: waypoints.append(CurrentStationWP(tag))
            elif tag.sym.text == Waypoint.type['LocationWP']: waypoints.append(LocationWP(tag))
            elif tag.sym.text == Waypoint.type['InterpolatedWP']: waypoints.append(InterpolatedWP(tag))
            elif tag.sym.text == Waypoint.type['InterpolatedDataWP']: waypoints.append(InterpolatedDataWP(tag))
        self.waypoints = waypoints

        # create interpolation groups
        self.interpolation_groups = []
        interpolated_wps = [wp for wp in waypoints if isinstance(wp, InterpolatedWP)]
        for wp in interpolated_wps:
            group= [wp]
            wp = Waypoint.index_lookup[wp.index+1]
            while isinstance(wp, InterpolatedDataWP):
                group.append(wp)
                wp = Waypoint.index_lookup[wp.index+1]
            self.interpolation_groups.append(group)

        # create aggregated path from waypoints
        self.elapsed_time_wps = [wp for wp in waypoints if isinstance(wp, CurrentStationWP) or isinstance(wp, InterpolatedWP)]
        self.elapsed_time_edges = []
        for i, wp in enumerate(self.elapsed_time_wps[:-1]):
            self.elapsed_time_edges.append(Edge(wp, self.elapsed_time_wps[i+1]))

        self.elapsed_time_path = Path(self.elapsed_time_edges)

    @staticmethod
    def write_clean_gpx(filepath, tree):
        new_filepath = filepath.parent.joinpath(filepath.stem + ' new.gpx')
        tag_names = ['extensions', 'time']
        for name in tag_names:
            for tag in tree.find_all(name):
                tag.decompose()
        with open(new_filepath, "w") as file:
            file.write(tree.prettify())
