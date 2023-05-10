from bs4 import BeautifulSoup as Soup
from Navigation import Navigation as NV
from pathlib import Path
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
        self.short_name = self.name.split(',')[0].split('(')[0].replace('.', '').strip()
        self.prev_edge = None
        self.next_edge = None

        if Waypoint.velocity_folder is None: raise TypeError
        self.folder = Waypoint.velocity_folder.joinpath(self.short_name)
        self.file = self.folder.joinpath(self.short_name + '_array')
        self.data = None
        makedirs(self.folder, exist_ok=True)

        Waypoint.index_lookup[Waypoint.ordinal_number] = self
        Waypoint.ordinal_number += 1

class PseudoWP(Waypoint):
    def __init__(self, *args):
        super().__init__(*args)

class ArtificialWP(PseudoWP):
    def __init__(self, *args):
        super().__init__(*args)

class LocationWP(PseudoWP):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)

class InterpolationWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.code = 'IP_' + str(self.index)

class CurrentStationWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.code = gpxtag.find('link').find('text').text

class DataWP(ArtificialWP):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.code = gpxtag.find('link').find('text').text

class Edge:

    elapsed_time_folder = None

    def __init__(self, start, end):
        if start == end: raise IndexError
        self.name = '[' + str(start.index) + '-' + str(end.index) + ']'
        self.start = start
        self.end = end
        start.next_edge = self
        end.prev_edge = self

        if Edge.elapsed_time_folder is None: raise TypeError
        self.folder = Edge.elapsed_time_folder.joinpath(self.name)
        self.file = self.folder.joinpath(self.name + '_array')
        self.data = None
        makedirs(self.folder, exist_ok=True)

class SimpleEdge(Edge):
    def __init__(self, start, end):
        super().__init__(start, end)
        self.length = round(NV.distance(self.start.coords, self.end.coords), 4)

class CompositeEdge(Edge):
    def __init__(self, start, end):
        super().__init__(start, end)
        self.length = 0
        wp_range = range(start.index, end.index+1)
        waypoints = [Waypoint.index_lookup[i] for i in wp_range if not isinstance(Waypoint.index_lookup[i], ArtificialWP)]
        for i, wp in enumerate(waypoints[:-1]):
            self.length += round(NV.distance(wp.coords, waypoints[i+1].coords), 4)

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
        self.direction = NV.direction(self.edges[0].start.coords, self.edges[-1].end.coords)

    def print_path(self):
        print(f'{self.name} "{self.direction}" {self.length}')
        for edge in self.edges:
            print(f'{edge.length} {edge.name} [{edge.start.name} ({type(edge.start).__name__})]-----[{edge.end.name} ({type(edge.end).__name__})] {type(edge)}')

class Route:

    def transit_time_lookup(self, key, array=None):
        if key not in self.__transit_time_dict and array is not None:
            self.__transit_time_dict[key] = array
        else:
            return self.__transit_time_dict[key]

    def elapsed_time_lookup(self, key, array=None):
        if key not in self.__elapsed_time_dict and array is not None:
            self.__elapsed_time_dict[key] = array
        else:
            return self.__elapsed_time_dict[key]

    def __init__(self, filepath):
        self.name = filepath.stem
        self.__transit_time_dict = {}
        self.__elapsed_time_dict = {}
        self.whole_path = self.velo_path = None
        self.interpolation_groups = None
        self.waypoints = None

        with open(filepath, 'r') as f: gpxfile = f.read()
        tree = Soup(gpxfile, 'xml')

        # build ordered list of all waypoints
        waypoints = []
        for waypoint in tree.find_all('rtept'):
            if waypoint.sym.text == Waypoint.type['CurrentStationWP']: waypoints.append(CurrentStationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['LocationWP']: waypoints.append(LocationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['InterpolationWP']: waypoints.append(InterpolationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['DataWP']: waypoints.append(DataWP(waypoint))

        self.waypoints = waypoints

        # create all the edges and the whole path
        edges = [SimpleEdge(wp, Waypoint.index_lookup[wp.index+1]) for wp in waypoints[:-1]]
        self.whole_path = GPXPath(edges)

        # create interpolation groups
        self.interpolation_groups = []
        wp_len = len(waypoints)
        for i in range(0, wp_len):
            if isinstance(waypoints[i], InterpolationWP):
                group = [waypoints[i]] + [waypoints[j] for j in range(i+1, wp_len) if isinstance(waypoints[j], DataWP)]
                self.interpolation_groups.append(group)

        # create velocity path
        velo_wps = [wp for wp in waypoints if not isinstance(wp, PseudoWP)]
        velo_edges = []
        for i, wp in enumerate(velo_wps[:-1]):
            if wp.index+1 == velo_wps[i+1]:
                velo_edges.append(SimpleEdge(wp, velo_wps[i+1]))
            else:
                velo_edges.append(CompositeEdge(wp, velo_wps[i + 1]))
        self.velo_path = GPXPath(velo_edges)

    def print_route(self):
        print(f'\n{self.name}')
        print(f'\nwhole path')
        self.whole_path.print_path()
        print(f'\nvelocity path')
        self.velo_path.print_path()
