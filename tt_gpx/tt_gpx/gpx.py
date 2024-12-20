from os import makedirs, listdir
from os.path import isfile, isdir, islink
from os import unlink as delete_file
from shutil import rmtree as delete_folder
from pathlib import Path
from bs4 import BeautifulSoup as Soup
from num2words import num2words
from string import Template

from tt_navigation.navigation import distance, directions, Heading
from tt_file_tools.file_tools import SoupFromXMLFile
# from tt_jobs.jobs import InterpolatePointJob
from tt_globals.globals import PresetGlobals


class BaseWaypoint:

    raw_csv_name = 'raw_frame.csv'
    adjusted_csv_name = 'adjusted_frame.csv'
    velocity_csv_name = 'velocity_frame.csv'
    spline_csv_name = 'cubic_spline_frame.csv'

    code_types = {'H': 'Harmonic', 'S': 'Subordinate', 'W': 'Weak', 'L': 'Location', 'E': 'Empty', 'P': 'Pseudo'}
    code_symbols = {'H': 'Symbol-Pin-Green', 'S': 'Symbol-Pin-Green', 'W': 'Symbol-Pin-Yellow',
                    'L': 'Symbol-Pin-White', 'E': 'Symbol-Pin-Orange', 'P': 'Symbol-Pin-Blue'}
    symbol_codes = {'Symbol-Pin-Yellow': 'W', 'Symbol-Pin-White': 'L', 'Symbol-Pin-Orange': 'E', 'Symbol-Pin-Blue': 'P' }
    ordinal_number = 0

    def write_gpx(self):
        soup = SoupFromXMLFile(PresetGlobals.templates_folder.joinpath('waypoint_template.gpx')).tree
        soup.find('name').string = self.name
        soup.find('wpt')['lat'] = self.lat
        soup.find('wpt')['lon'] = self.lon
        soup.find('type').string = self.type
        soup.find('sym').string = self.symbol

        id_tag = soup.new_tag('id')
        id_tag.string = self.id
        soup.find('name').insert_after(id_tag)

        if self.folder is not None:
            self.folder = Path(self.folder)
            folder_tag = soup.new_tag('folder')
            folder_tag.string = str(self.folder.absolute())
            soup.find('name').insert_after(folder_tag)

        desc_tag = soup.new_tag('desc')
        desc_tag.string = self.id
        soup.find('name').insert_after(desc_tag)

        with open(PresetGlobals.gpx_folder.joinpath(self.id + '.gpx'), 'w') as a_file:
            a_file.write(str(soup))


    def empty_folder(self):
        folder = self.folder
        for path in [folder.joinpath(f) for f in listdir(folder)]:
            try:
                if path.exists():
                    if isfile(path) or islink(path):
                        delete_file(path)
                    elif isdir(path):
                        delete_folder(path)
            except OSError(f'Cannot remove {path}') as err:
                print(err)


    def __init__(self, station: dict):

        self.index = BaseWaypoint.ordinal_number
        self.id = 'Location ' + str(self.index) if station['type'] == 'L' else station['id']
        self.name = 'Location ' + str(self.index) if station['type'] == 'L' else station['name']
        self.lat = round(float(station['lat']), 4)
        self.lon = round(float(station['lon']), 4)
        self.coords = tuple([self.lat, self.lon])
        self.type = station['type']
        self.symbol = self.code_symbols[station['type']]
        self.folder = station['folder']
        if self.folder is not None:
            self.folder = Path(self.folder)
            self.raw_csv_path = self.folder.joinpath(self.raw_csv_name)
            self.adjusted_csv_path = self.folder.joinpath(self.adjusted_csv_name)
            self.spline_csv_path = self.folder.joinpath(self.spline_csv_name)
            self.velocity_csv_path = self.folder.joinpath(self.velocity_csv_name)
            makedirs(self.folder, exist_ok=True)

        self.prev_edge = None
        self.next_edge = None

        BaseWaypoint.ordinal_number += 1


class EdgeNode(BaseWaypoint):
    def __init__(self, *args):
        super().__init__(*args)


class Waypoint(EdgeNode):
    def __init__(self, *args):
        super().__init__(*args)


class Location(EdgeNode):
    def __init__(self, tag):
        super_dict = {'id': None, 'name': None, 'lat': tag.attrs['lat'], 'lon': tag.attrs['lon'], 'type': 'L', 'folder': None}
        super().__init__(super_dict)


class Empty(BaseWaypoint):
    def __init__(self, tag):
        super_dict = {'id': tag.find('name').text, 'name': tag.find('name').text, 'lat': tag.attrs['lat'],
                    'lon': tag.attrs['lon'], 'type': BaseWaypoint.symbol_codes[tag.find('sym').text], 'folder': None}
        super().__init__(super_dict)


class Data(BaseWaypoint):
    def __init__(self, station: dict):
        station['type'] = 'D'
        super().__init__(station)


# class InterpolatedWP(Waypoint):  # result of interpolation of other waypoint data
#
#     def create_data_waypoint_list(self):
#         index = self.index + 1
#         while index <= max(Waypoint.index_lookup) and isinstance(Waypoint.index_lookup[index], InterpolatedDataWP):
#             self.data_waypoints.append(Waypoint.index_lookup[index])
#             index += 1
#
#     def interpolate(self, job_manager):
#
#         output_filepath = self.folder.joinpath('interpolated_velocity.csv')
#
#         if not output_filepath.exists():
#             velocity_data = []
#             for i, wp in enumerate(self.data_waypoints):
#                 velocity_data.append(read_df(wp.velocity_csv))
#                 velocity_data[i]['lat'] = wp.lat
#                 velocity_data[i]['lon'] = wp.lon
#                 print(i, len(velocity_data[i]), wp.name)
#
#             keys = [job_manager.put(InterpolatePointJob(self, velocity_data, i)) for i in range(len(velocity_data[0]))]
#             job_manager.wait()
#
#             result_array = tuple([job_manager.get(key).date_velocity for key in keys])
#             frame = pd.DataFrame(result_array, columns=['date_index', 'velocity'])
#             frame.sort_values('date_index', inplace=True)
#             frame['date_time'] = pd.to_datetime(frame['date_index'], unit='s').round('min')
#             frame.reset_index(drop=True, inplace=True)
#             write_df(frame, output_filepath)
#
#         if print_file_exists(output_filepath):
#             write_df(read_df(output_filepath), self.folder.joinpath(wp.velocity_frame))
#
#     def __init__(self, gpxtag):
#         super().__init__(gpxtag)
#         self.data_waypoints = []


class Edge:  # connection between waypoints with current data

    def __init__(self, start: EdgeNode, end: EdgeNode):

        if start.id == end.id:
            raise IndexError
        if not isinstance(start, EdgeNode) or not isinstance(end, EdgeNode):
            raise TypeError

        start.next_edge = self
        end.prev_edge = self

        self.start = start
        self.end = end
        self.name = 'Edge ' + str(start.index) + ' ' + str(end.index)
        self.length = round(distance(start.coords, end.coords), 4)


class Segment:

    prefix = 'Segment'

    def __init__(self, node: EdgeNode):

        self.length = 0
        self.start = node

        while node.next_edge is not None:
            self.length += node.next_edge.length
            self.end = node.next_edge.end
            node = self.end
            if not isinstance(self.end, Location):
                break

        self.name = Segment.prefix + ' ' + str(self.start.index) + '-' + str(self.end.index)


class Route:

    template_dict = {'elapsed timesteps': Template('elapsed_timesteps $speed.csv'),
                      'transit timesteps': Template('transit_timesteps $speed.csv'),
                      'savgol': Template('savgol $speed.csv'),
                      'minima': Template('minima $speed.csv'),
                      'arcs': Template('arcs $speed.csv'),
                      'transit times': Template('transit times $loc.csv'),
                      'first_day': Template('$year/12/1'),
                      'last_day': Template('$year/1/31')}


    def make_folder(self):
        makedirs(self.folder, exist_ok=True)


    def touch_heading(self):
        if self.folder.exists():
            self.folder.joinpath(str(self.heading) + '.heading').touch()
        else:
            raise FileExistsError(self.folder)

    def times_folder(self, speed: int):
        folder_path = self.folder.joinpath(num2words(speed))
        makedirs(folder_path, exist_ok=True)
        return folder_path

    def filepath(self, name: str, field):
        return self.times_folder(field).joinpath(Route.template_dict[name].substitute({'speed': field}))

    def __init__(self, stations_dict: dict, tree: Soup):

        self.name = tree.find('name').string
        self.code = ''.join(word[0] for word in self.name.upper().split())
        self.folder = PresetGlobals.project_base_folder.joinpath(self.name)

        self.waypoints = []
        for tag in tree.find_all('rtept'):
            if tag.sym.text == Waypoint.code_symbols['H'] or tag.sym == Waypoint.code_symbols['S']:
                self.waypoints.append(Waypoint(stations_dict[tag.desc.text]))
            elif tag.sym.text == Waypoint.code_symbols['L']:
                self.waypoints.append(Location(tag))
            elif tag.sym.text == Waypoint.code_symbols['E']:
                self.waypoints.append(Empty(tag))
            elif tag.sym.text == Waypoint.code_symbols['D']:
                self.waypoints.append(Data(stations_dict[tag.desc.text]))

        self.heading = Heading(self.waypoints[0].coords, self.waypoints[-1].coords).angle
        self.direction = directions(self.heading)[0]

        edge_nodes = [wp for wp in self.waypoints if isinstance(wp, EdgeNode)]
        self.edges = [Edge(wp, edge_nodes[i+1]) for i, wp in enumerate(edge_nodes[:-1])]
        self.segments = []
        node = edge_nodes[0]
        while node.next_edge is not None:
            seg = Segment(node)
            self.segments.append(seg)
            node = seg.end

        if round(sum([e.length for e in self.edges]), 4) != round(sum([e.length for e in self.segments]), 4):
            raise ValueError
        self.length = round(sum([e.length for e in self.segments]), 4)


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

        GpxFile.write_clean_gpx(filepath, self.tree)
