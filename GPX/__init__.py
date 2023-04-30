from bs4 import BeautifulSoup as Soup
from Navigation import Navigation as NV

class Waypoint:

    type = {'CurrentStationWP': 'Symbol-Spot-Orange', 'PlaceHolderWP': 'Symbol-Spot-Green', 'InterpolationWP': 'Symbol-Spot-Blue', 'InterpolationDataWP': 'Symbol-Spot-Black'}
    ordinal_number = 0
    index_lookup = {}

    def __init__(self, gpxtag):
        lat = round(float(gpxtag.attrs['lat']), 4)
        lon = round(float(gpxtag.attrs['lon']), 4)
        self.index = Waypoint.ordinal_number
        self.coords = tuple([lat, lon])
        self.symbol = gpxtag.sym.text
        self.name = gpxtag.find('name').text.strip('\n')
        self.short_name = self.name.split(',')[0].split('(')[0].replace('.', '').strip()
        self.prev_edge = None
        self.next_edge = None

        Waypoint.index_lookup[Waypoint.ordinal_number] = self
        Waypoint.ordinal_number += 1

class PlaceHolderWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)

class InterpolationWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.velo_arr = None

class CurrentStationWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.noaa_code = gpxtag.find('link').find('text').text
        self.velo_arr = None

class InterpolationDataWP(Waypoint):
    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.noaa_code = gpxtag.find('link').find('text').text
        self.velo_arr = None

class Edge:
    def __init__(self, start, end):
        if start == end: raise IndexError
        self.start = start
        self.end = end
        self.name = '[' + str(self.start.index) + '-' + str(self.end.index) + ']'
        start.next_edge = self
        end.prev_edge = self

class HaversineEdge(Edge):
    def __init__(self, start, end):
        super().__init__(start, end)
        self.length = round(NV.distance(self.start.coords, self.end.coords), 4)

class LengthSumEdge(Edge):
    def __init__(self, start, end):
        super().__init__(start, end)
        self.length = 0
        wp_range = range(start.index, end.index) if start.index < end.index else range(end.index, start.index)
        for i in wp_range:
            start_coords = Waypoint.index_lookup[i].coords
            end_coords = Waypoint.index_lookup[i+1].coords
            self.length += round(NV.distance(start_coords, end_coords), 4)

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
        self.direction = NV.direction(self.edges[0].start.coords, self.edges[-1].end.coords)

    def print_path(self):
        print(f'{self.name} "{self.direction}" {self.length}')
        for edge in self.edges:
            print(f'{edge.name} [{edge.start.name} ({type(edge.start).__name__})]--{edge.length}--[{edge.end.name} ({type(edge.end).__name__})] {type(edge)}')

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
        self.whole_path = None
        self.velo_path = None
        self.interpolation_groups = []

        with open(filepath, 'r') as f: gpxfile = f.read()
        tree = Soup(gpxfile, 'xml')

        # build ordered list of all waypoints
        waypoints = []
        for waypoint in tree.find_all('rtept'):
            if waypoint.sym.text == Waypoint.type['CurrentStationWP']: waypoints.append(CurrentStationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['PlaceHolderWP']: waypoints.append(PlaceHolderWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['InterpolationWP']: waypoints.append(InterpolationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['InterpolationDataWP']: waypoints.append(InterpolationDataWP(waypoint))

        edges = [HaversineEdge(waypoint, waypoints[i+1]) for i, waypoint in enumerate(waypoints[:-1])]
        self.whole_path = Path(edges)

        #  calculate interpolation groups
        wp_len = len(waypoints)
        for i in range(0, wp_len):
            if isinstance(waypoints[i], InterpolationWP):
                group = [waypoints[i]] + [waypoints[j] for j in range(i+1, wp_len) if isinstance(waypoints[j], InterpolationDataWP)]
                self.interpolation_groups.append(group)

        velo_wps = [wp for wp in waypoints if type(wp) == CurrentStationWP or type(wp) == InterpolationWP]
        velo_edges = []
        for i, wp in enumerate(velo_wps[:-1]):
            print(wp.name, type(wp), velo_wps[i+1].name, type(velo_wps[i+1]))
            if wp.index+1 == velo_wps[i+1].index:  # adjacent points
                velo_edges.append(HaversineEdge(wp, velo_wps[i+1]))
            elif type(wp) == InterpolationWP or type(velo_wps[i+1]) == InterpolationWP:  # skip data points
                velo_edges.append(HaversineEdge(wp, velo_wps[i + 1]))
            else:  # add placeholder points
                velo_edges.append(LengthSumEdge(wp, velo_wps[i + 1]))
        self.velo_path = Path(velo_edges)

    def print_route(self):
        print(f'\n{self.name}')
        print(f'\nwhole path')
        self.whole_path.print_path()
        print(f'\nvelocity path')
        self.velo_path.print_path()
