from bs4 import BeautifulSoup as Soup
from tt_navigation.navigation import distance, direction, heading
from os import makedirs


class Waypoint:
    waypoints_folder = None
    color = {'TideStationWP': 'Yellow', 'CurrentStationWP': 'Orange',
             'LocationWP': 'Green', 'InterpolatedWP': 'Blue',
             'InterpolatedDataWP': 'Black'}
    ordinal_number = 0
    index_lookup = {}

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

        if gpxtag.link:
            self.noaa_url = gpxtag.find('link').attrs['href']
            self.code = gpxtag.find('link').find('text').text.split(' ')[0]


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


class InterpolatedDataWP(DownloadedDataWP):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


class InterpolatedWP(EdgeNode):  # Not really a data waypoint but stores data in the downloaded data path
    def __init__(self, gpxtag):
        super().__init__(gpxtag)


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
        self.direction = direction(self.edges[0].start.coords, self.edges[-1].end.coords)
        self.heading = heading(self.edges[0].start.coords, self.edges[-1].end.coords)


class Route:

    def __init__(self, filepath):
        self.transit_time_lookup = {}
        self.elapsed_time_lookup = {}
        self.whole_path = self.velo_path = None
        self.interpolation_groups = None
        self.waypoints = None
        self.filepath = filepath

        with open(filepath, 'r') as f:
            gpxfile = f.read()
        tree = Soup(gpxfile, 'xml', preserve_whitespace_tags=['name', 'type', 'sym', 'text'])
        self.write_clean_gpx(filepath, tree)

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

        # create interpolation groups
        self.interpolation_groups = []
        interpolated_wps = [wp for wp in waypoints if isinstance(wp, InterpolatedWP)]
        for wp in interpolated_wps:
            group = [wp]
            wp = Waypoint.index_lookup[wp.index + 1]
            while isinstance(wp, InterpolatedDataWP):
                group.append(wp)
                wp = Waypoint.index_lookup[wp.index + 1]
            self.interpolation_groups.append(group)

        # create edges
        edge_nodes = [wp for wp in waypoints if isinstance(wp, EdgeNode)]
        self.edge_nodes_edges = [Edge(wp, edge_nodes[i+1]) for i, wp in enumerate(self.edge_nodes[:-1])]

        # self.elapsed_time_path = Path(self.elapsed_time_edges)

    @staticmethod
    def write_clean_gpx(filepath, tree):
        new_filepath = filepath.parent.joinpath(filepath.stem + ' new.gpx')
        tag_names = ['extensions', 'time']
        for name in tag_names:
            for tag in tree.find_all(name):
                tag.decompose()
        with open(new_filepath, "w") as file:
            file.write(tree.prettify())
