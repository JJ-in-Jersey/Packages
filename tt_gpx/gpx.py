from bs4 import BeautifulSoup as Soup
from tt_navigation import distance, direction, heading
from os import makedirs

class Waypoint:

    velocity_folder = None

    type = {'CurrentStationWP': 'Symbol-Spot-Orange', 'LocationWP': 'Symbol-Spot-Green', 'InterpolationWP': 'Symbol-Spot-Blue', 'DataWP': 'Symbol-Spot-Black'}
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

        self.folder = Waypoint.velocity_folder.joinpath(self.unique_name)
        self.interpolation_data_file = self.folder.joinpath(self.unique_name + '_interpolation')
        self.interpolation_data = None
        self.output_data_file = self.folder.joinpath(self.unique_name + '_output')
        self.output_data = None

        Waypoint.index_lookup[Waypoint.ordinal_number] = self
        Waypoint.ordinal_number += 1

class DistanceWP(Waypoint):  # required for distance calculations
    def __init__(self, *args):
        super().__init__(*args)

class ElapsedTimeWP(DistanceWP):  # required for elapsed time calculations
    def __init__(self, *args):
        super().__init__(*args)

class LocationWP(DistanceWP):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)

class InterpolationWP(ElapsedTimeWP):
    def __init__(self, gpxtag, start_index, end_index):
        super().__init__(gpxtag)
        makedirs(self.folder, exist_ok=True)
        self.start_index = start_index
        self.end_index = end_index

class CurrentStationWP(ElapsedTimeWP):
    def __init__(self, gpxtag, start_index, end_index):
        super().__init__(gpxtag)
        makedirs(self.folder, exist_ok=True)
        self.start_index = start_index
        self.end_index = end_index
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.code = gpxtag.find('link').find('text').text

class DataWP(Waypoint):
    def __init__(self, gpxtag, start_index, end_index):
        super().__init__(gpxtag)
        makedirs(self.folder, exist_ok=True)
        self.start_index = start_index
        self.end_index = end_index
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.code = gpxtag.find('link').find('text').text

class Edge:

    elapsed_time_folder = None

    def __init__(self, start, end, edge_range):
        if start == end: raise IndexError
        self.unique_name = '[' + str(start.index) + '-' + str(end.index) + ']'
        self.start = start
        self.end = end
        start.next_edge = self
        end.prev_edge = self

        if Edge.elapsed_time_folder is None: raise TypeError
        self.folder = Edge.elapsed_time_folder.joinpath(self.unique_name)
        makedirs(self.folder, exist_ok=True)
        self.output_data_file = self.folder.joinpath(self.unique_name + '_output')
        self.output_data = None
        self.edge_range = edge_range


class SimpleEdge(Edge):
    def __init__(self, start, end, edge_range):
        super().__init__(start, end, edge_range)
        self.length = round(distance(self.start.coords, self.end.coords), 4)

class CompositeEdge(Edge):
    def __init__(self, start, end, edge_range):
        super().__init__(start, end, edge_range)
        self.length = 0
        wp_range = range(start.index, end.index+1)
        waypoints = [Waypoint.index_lookup[i] for i in wp_range if isinstance(Waypoint.index_lookup[i], DistanceWP)]
        for i, wp in enumerate(waypoints[:-1]):
            self.length += round(distance(wp.coords, waypoints[i+1].coords), 4)

class GPXPath:

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

    def print_path(self):
        print(f'{self.name} "{self.direction}" {self.length}')
        for edge in self.edges:
            print(f'{edge.length} {edge.name} [{edge.start.name} ({type(edge.start).__name__})]-----[{edge.end.name} ({type(edge.end).__name__})] {type(edge)}')

class Route:

    def __init__(self, filepath, wp_si, wp_ei, e_r):
        self.name = filepath.stem
        self.transit_time_lookup = {}
        self.elapsed_time_lookup = {}
        self.whole_path = self.velo_path = None
        self.interpolation_groups = None
        self.waypoints = None

        with open(filepath, 'r') as f: gpxfile = f.read()
        tree = Soup(gpxfile, 'xml')

        # build ordered list of all waypoints
        waypoints = []
        for tag in tree.find_all('rtept'):
            if tag.sym.text == Waypoint.type['CurrentStationWP']: waypoints.append(CurrentStationWP(tag, wp_si, wp_ei))
            elif tag.sym.text == Waypoint.type['LocationWP']: waypoints.append(LocationWP(tag))
            elif tag.sym.text == Waypoint.type['InterpolationWP']: waypoints.append(InterpolationWP(tag, wp_si, wp_ei))
            elif tag.sym.text == Waypoint.type['DataWP']: waypoints.append(DataWP(tag, wp_si, wp_ei))

        self.waypoints = waypoints

        # create all the edges and the whole path
        edges = [SimpleEdge(wp, Waypoint.index_lookup[wp.index+1], e_r) for wp in waypoints[:-1]]
        self.whole_path = GPXPath(edges)

        # create interpolation groups
        self.interpolation_groups = []
        for i, wp in enumerate(waypoints):
            if isinstance(wp, InterpolationWP):
                group = [wp]
                count = i+1
                while count < len(waypoints) and isinstance(waypoints[count], DataWP):
                    group.append(waypoints[count])
                    count += 1
                self.interpolation_groups.append(group)

        # create elapsed time path - exclude waypoints not required for elapsed time calculations
        elapsed_time_wps = [wp for wp in waypoints if isinstance(wp, ElapsedTimeWP)]
        elapsed_time_edges = []
        for i, wp in enumerate(elapsed_time_wps[:-1]):
            if wp.index+1 == elapsed_time_wps[i+1]:
                elapsed_time_edges.append(SimpleEdge(wp, elapsed_time_wps[i+1], e_r))
            else:
                elapsed_time_edges.append(CompositeEdge(wp, elapsed_time_wps[i + 1], e_r))
        self.elapsed_time_path = GPXPath(elapsed_time_edges)

    def print_route(self):
        print(f'\n{self.name}')
        print(f'\nwhole path')
        self.whole_path.print_path()
        print(f'\nvelocity path')
        self.elapsed_time_path.print_path()
