from bs4 import BeautifulSoup as Soup
from Navigation import Navigation as NV

class Waypoint:

    type = {'CurrentStationWP': 'Symbol-Spot-Orange', 'PlaceHolderWP': 'Symbol-Spot-Green', 'InterpolationWP': 'Symbol-Spot-Blue', 'InterpolationDataWP': 'Symbol-Spot-Black'}
    ordinal_number = 0
    number_lookup = {}

    def prev_edge(self, path, edge=None):
        if edge is not None: self.__prev_edges[path] = edge  # set edge value
        else: return self.__prev_edges[path]  # return edge value

    def next_edge(self, path, edge=None):
        if edge is not None: self.__next_edges[path] = edge  # set edge value
        else: return self.__next_edges[path]  # return edge value
    def has_velocity(self): return False

    def __init__(self, gpxtag):
        lat = round(float(gpxtag.attrs['lat']), 4)
        lon = round(float(gpxtag.attrs['lon']), 4)
        self.number = Waypoint.ordinal_number
        self.coords = tuple([lat, lon])
        self.symbol = gpxtag.sym.text
        self.name = gpxtag.find('name').text.strip('\n')
        self.short_name = self.name.split(',')[0].split('(')[0].replace('.', '').strip()
        self.__prev_edges = {}
        self.__next_edges = {}
        self.velo_array = None

        Waypoint.number_lookup[Waypoint.ordinal_number] = self
        Waypoint.ordinal_number += 1

class PlaceHolderWP(Waypoint):

    def __init__(self, gpxtag):
        super().__init__(gpxtag)

class InterpolationWP(Waypoint):

    def has_velocity(self): return True

    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.velo_arr = None

class CurrentStationWP(Waypoint):

    def has_velocity(self): return True

    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.noaa_code = gpxtag.find('link').find('text').text
        self.velo_arr = None

class InterpolationDataWP(Waypoint):

    def has_velocity(self): return True

    def __init__(self, gpxtag):
        super().__init__(gpxtag)
        self.noaa_url = gpxtag.find('link').attrs['href'] if gpxtag.link else None
        self.noaa_code = gpxtag.find('link').find('text').text
        self.velo_arr = None

class Edge:

    def __init__(self, path, start, end):
        self.path = path
        self.start = start
        self.end = end
        self.name = '[' + str(self.start.number) + '-' + str(self.end.number) + ']'
        self.length = round(NV.distance(self.start.coords, self.end.coords), 4)
        start.next_edge(path, self)
        end.prev_edge(path, self)

class ElapsedTimeSegment:

    def update(self):
        self.start_velo = self.start.velo_array()
        self.end_velo = self.end.velo_array()

    def __init__(self, path, start, end):
        self.start = start
        self.end = end
        self.path = path
        self.name = 'segment ' + str(start.number) + '-' + str(end.number)
        self.start_velo = None
        self.end_velo = None
        self.length = path.length(start, end)
        self.elapsed_times_df = None

class Path:

    def total_length(self): return round(sum([edge.length for edge in self.edges]), 4)
    def direction(self): return NV.direction(self.waypoints[0].coords, self.waypoints[-1].coords)

    def __init__(self, waypoints):
        self.waypoints = [wp for wp in waypoints if not isinstance(wp, InterpolationDataWP)]  # filter out data waypoints
        self.edges = [Edge(self, waypoint, self.waypoints[i+1]) for i, waypoint in enumerate(self.waypoints[:-1])]
        self.name = '{' + str(self.waypoints[0].number) + '-' + str(self.waypoints[-1].number) + '}'

    def print_path(self):

        print(f'{self.name} #wps:{len(self.waypoints)} #edges:{len(self.edges)} total length:{self.total_length()}')
        for edge in self.edges:
            print(f'{edge.name}  {edge.start.name} - type:{type(edge.start).__name__} - {edge.end.name} - type:{type(edge.end).__name__} - {edge.length}')

    def length(self, start_wp, end_wp):
        length = 0
        if start_wp == end_wp: return length
        wp_range = range(start_wp.number, end_wp.number) if start_wp.number < end_wp.number else range(end_wp.number, start_wp.number)
        for i in wp_range:
            length += Waypoint.number_lookup[i].next_edge(self).length
        return length

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
        self.waypoints = []
        self.path_waypoints = []
        self.elapsed_time_waypoints = []
        self.path = None
        self.elapsed_time_segments = []

        with open(filepath, 'r') as f: gpxfile = f.read()
        tree = Soup(gpxfile, 'xml')

        # build ordered list of all waypoints
        for waypoint in tree.find_all('rtept'):
            if waypoint.sym.text == Waypoint.type['CurrentStationWP']: self.waypoints.append(CurrentStationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['PlaceHolderWP']: self.waypoints.append(PlaceHolderWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['InterpolationWP']: self.waypoints.append(InterpolationWP(waypoint))
            elif waypoint.sym.text == Waypoint.type['InterpolationDataWP']: self.waypoints.append(InterpolationDataWP(waypoint))

        self.path = Path(self.waypoints)

        self.elapsed_time_waypoints = [wp for wp in self.waypoints if not isinstance(wp, PlaceHolderWP) and not isinstance(wp, InterpolationDataWP)]  # filter out placeholder waypoints and data waypoints
        self.elapsed_time_waypoints = [wp for wp in self.elapsed_time_waypoints if not isinstance(wp, InterpolationWP)]  # temporarily remove InterpolationWP
        self.elapsed_time_segments = [ElapsedTimeSegment(self.path, wp, self.elapsed_time_waypoints[i+1]) for i, wp in enumerate(self.elapsed_time_waypoints[:-1])]

    def print_route(self):
        print(f'{self.name}\n')
        print(f'All waypoints:')
        for wp in self.waypoints:
            print(f'    {wp.number} {wp.name}')
        print('\nElapsed time waypoints:')
        for wp in self.elapsed_time_waypoints:
            print(f'    {wp.number} {wp.name}')
