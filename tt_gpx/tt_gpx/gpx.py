from os import makedirs, listdir
from os.path import isfile, isdir, islink
from os import unlink as delete_file
from shutil import rmtree as delete_folder
from pathlib import Path
from bs4 import BeautifulSoup as Soup
from num2words import num2words
from typing import Union, Type, Any

from tt_navigation.navigation import distance, directions, Heading, dir_abbrevs
from tt_file_tools.file_tools import SoupFromXMLFile
import tt_globals.globals as fc_globals

class BaseWaypoint:

    raw_csv_name = 'raw_frame.csv'
    velocity_csv_name = 'velocity_frame.csv'
    spline_csv_name = 'cubic_spline_frame.csv'

    code_types = {'H': 'Harmonic', 'S': 'Subordinate', 'W': 'Weak', 'L': 'Location', 'E': 'Empty', 'P': 'Pseudo'}
    code_symbols = {'H': 'Symbol-Pin-Green', 'S': 'Symbol-Pin-Green', 'W': 'Symbol-Pin-Yellow',
                    'L': 'Symbol-Pin-White', 'E': 'Symbol-Pin-Orange', 'P': 'Symbol-Pin-Blue'}
    symbol_codes = {'Symbol-Pin-Yellow': 'W', 'Symbol-Pin-White': 'L', 'Symbol-Pin-Orange': 'E', 'Symbol-Pin-Blue': 'P'}
    ordinal_number = 0

    def write_gpx(self):
        soup = SoupFromXMLFile(fc_globals.TEMPLATES_FOLDER.joinpath('waypoint_template.gpx')).soup
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

        with open(fc_globals.GPX_FOLDER.joinpath(self.id + '.gpx'), 'w') as a_file:
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
        if bool(station['folder']):
            self.folder = Path(station['folder'])
        else:
            self.folder = fc_globals.WAYPOINTS_FOLDER.joinpath(self.name)
            
        self.raw_csv_path = self.folder.joinpath(self.raw_csv_name)
        self.spline_csv_path = self.folder.joinpath(self.spline_csv_name)
        self.velocity_csv_path = self.folder.joinpath(self.velocity_csv_name)
        makedirs(self.folder, exist_ok=True)

        self.folder.joinpath(self.type + ' ' +self.name.replace(',','').replace('"','') + '.info').touch()

        self.prev_edge = None
        self.next_edge = None

        BaseWaypoint.ordinal_number += 1


#  edges are edges in the route, segments are used for distance and elapsed time
class EdgeNode(BaseWaypoint):
    def __init__(self, *args):
        super().__init__(*args)


class Waypoint(EdgeNode):
    def __init__(self, *args):
        super().__init__(*args)


class Location(EdgeNode):
    def __init__(self, tag):
        super_dict = {'id': None, 'name': tag.find('name').text, 'lat': tag.attrs['lat'], 'lon': tag.attrs['lon'], 'type': 'L', 'folder': None}
        super().__init__(super_dict)


class Empty(BaseWaypoint):
    def __init__(self, tag):
        super_dict = {'id': tag.find('name').text, 'name': tag.find('name').text, 'lat': tag.attrs['lat'],
                      'lon': tag.attrs['lon'], 'type': BaseWaypoint.symbol_codes[tag.find('sym').text], 'folder': None}
        super().__init__(super_dict)


class Pseudo(Empty):
    def __init__(self, *args):
        super().__init__(*args)


class Edge:  # connection between waypoints with current data

    def __init__(self, start: EdgeNode, end: EdgeNode):

        if start.id == end.id:
            raise IndexError
        # if not isinstance(start, EdgeNode) or not isinstance(end, EdgeNode):
        #     raise TypeError

        start.next_edge = self
        end.prev_edge = self

        self.start = start
        self.end = end
        self.name = 'Edge ' + str(start.index) + ' ' + str(end.index)
        self.length = round(distance(start.coords, end.coords), 4)


# segments are used for distance and elapsed time, edges are edges in the route
class Segment:

    prefix = 'Segment'

    def __init__(self, node: EdgeNode):

        self.length = 0
        self.start = node
        self.node_list = [node]

        while node.next_edge is not None:
            self.node_list.extend([node.next_edge.end])
            self.length += node.next_edge.length
            self.end = node.next_edge.end
            node = self.end
            if not isinstance(self.end, Location):
                break

        self.length = round(self.length, 4)
        self.name = Segment.prefix + ' ' + str(self.start.index) + '-' + str(self.end.index)


class Route:

    name = code = folder = waypoints = heading = direction = dir_abbrevs = edges = segments = length = None

    @classmethod
    def filepath(cls, name: Union[str, Type[Any]], speed: int):
        new_folder_path = Route.folder.joinpath(num2words(speed))
        makedirs(new_folder_path, exist_ok=True)
        if isinstance(name, str):
            return new_folder_path.joinpath(fc_globals.TEMPLATES[name].substitute({'speed': speed}))
        elif isinstance(name, type):
            return new_folder_path.joinpath(fc_globals.TEMPLATES[name.__name__].substitute({'speed': speed}))
        else:
            raise TypeError('argument must be str or type')

    def __init__(self, stations_dict: dict, tree: Soup):

        Route.name = tree.find('name').string
        Route.code = ''.join(word[0] for word in self.name.upper().split())
        Route.folder = fc_globals.PROJECT_BASE_FOLDER.joinpath(self.code)

        Route.waypoints = []
        for tag in tree.find_all('rtept'):
            if tag.sym.text == Waypoint.code_symbols['H'] or tag.sym == Waypoint.code_symbols['S']:
                Route.waypoints.append(Waypoint(stations_dict[str(tag.desc.text).replace('\n', '').strip()]))
            elif tag.sym.text == Waypoint.code_symbols['L']:
                Route.waypoints.append(Location(tag))
            elif tag.sym.text == Waypoint.code_symbols['E']:
                Route.waypoints.append(Empty(tag))
            elif tag.sym.text == Waypoint.code_symbols['P']:
                Route.waypoints.append(Pseudo(tag))
            else:
                raise TypeError('Unknown waypoint type')

        Route.heading = Heading(Route.waypoints[0].coords, Route.waypoints[-1].coords).angle
        Route.directions = directions(Route.heading)
        Route.dir_abbrevs = dir_abbrevs(Route.heading)

        edge_nodes = [wp for wp in Route.waypoints if isinstance(wp, EdgeNode)]
        Route.edges = [Edge(wp, edge_nodes[i+1]) for i, wp in enumerate(edge_nodes[:-1])]
        Route.segments = []
        node = edge_nodes[0]
        while node.next_edge is not None:
            seg = Segment(node)
            Route.segments.append(seg)
            node = seg.end

        if round(sum([e.length for e in Route.edges]), 4) != round(sum([e.length for e in Route.segments]), 4):
            raise ValueError
        Route.length = round(sum([e.length for e in Route.segments]), 4)


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
        self.tree = Soup(gpxfile, preserve_whitespace_tags=['name', 'type', 'sym', 'text'], features='xml')

        # GpxFile.write_clean_gpx(filepath, self.tree)
