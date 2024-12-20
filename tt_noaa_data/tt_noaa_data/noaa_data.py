from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
import pandas as pd
import time
import requests
from io import StringIO
from pathlib import Path
from os import listdir
from os.path import isfile, basename

from tt_file_tools.file_tools import SoupFromXMLResponse, print_file_exists, read_dict, write_dict, write_df
from tt_globals.globals import PresetGlobals
from tt_gpx.gpx import Waypoint


class StationDict:
    dict = {}

    @staticmethod
    def absolute_path_string(folder_name):
        return str(PresetGlobals.waypoints_folder.joinpath(folder_name).absolute())


    @staticmethod
    def add_waypoint(route_waypoint: Waypoint):
        if bool(StationDict.dict) and not route_waypoint.id in StationDict.dict:
            row = {'id': route_waypoint.id, 'name': route_waypoint.name,
                   'lat': route_waypoint.lat, 'lon': route_waypoint.lon,
                   'type': route_waypoint.type, 'folder_name': basename(route_waypoint.folder),
                   'folder': StationDict.absolute_path_string(basename(route_waypoint.folder))}
            StationDict.dict[row['id']] = row
            print_file_exists(write_dict(PresetGlobals.stations_file, StationDict.dict))


    def __init__(self):

        if print_file_exists(PresetGlobals.stations_file):
            StationDict.dict = read_dict(PresetGlobals.stations_file)
        else:
            StationDict.dict = {}
            my_request = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.xml?type=currentpredictions&units=english"
            for _ in range(5):
                try:
                    print(f'Requesting list of stations')
                    my_response = requests.get(my_request)
                    my_response.raise_for_status()
                    stations_tree = SoupFromXMLResponse(StringIO(my_response.content.decode())).tree
                    row_array = [{'id': station_tag.find_next('id').text,
                                  'name': station_tag.find_next('name').text,
                                  'lat': float(station_tag.find_next('lat').text),
                                  'lon': float(station_tag.find_next('lng').text),
                                  'type': station_tag.find_next('type').text,
                                  'folder_name': station_tag.find_next('type').text + ' ' + station_tag.find_next('id').text}
                                 for station_tag in stations_tree.find_all('Station')]
                    row_df = pd.DataFrame(row_array).drop_duplicates()
                    row_df['folder'] = row_df['folder_name'].apply(self.absolute_path_string)
                    row_dict = row_df.to_dict('records')
                    StationDict.dict = {r['id']: r for r in row_dict}

                    print(f'Requesting bins for each station')
                    for station_id in StationDict.dict.keys():
                        print(f'==>   {station_id}')
                        my_request = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/" + station_id + "/bins.xml?units=english"
                        for _ in range(3):
                            try:
                                my_response = requests.get(my_request)
                                my_response.raise_for_status()
                                bins_tree = SoupFromXMLResponse(StringIO(my_response.content.decode())).tree
                                bin_count = int(bins_tree.find("nbr_of_bins").text)
                                if bin_count and bins_tree.find('Bin').find('depth') is not None:
                                    bin_dict = {int(tag.num.text): float(tag.depth.text) for tag in bins_tree.find_all('Bin')}
                                    bin_dict = dict(sorted(bin_dict.items(), key=lambda item: item[1]))
                                    StationDict.dict[station_id]['bins'] = bin_dict
                                break
                            except requests.exceptions.RequestException:
                                time.sleep(2)
                    print_file_exists(write_dict(PresetGlobals.stations_file, StationDict.dict))
                    break
                except requests.exceptions.RequestException:
                    time.sleep(1)


class OneMonth:

    @staticmethod
    def connection_error(folder: str):
        folder_path = Path(folder)
        if bool([f for f in listdir(folder_path) if isfile(folder_path.joinpath(f)) and 'connection_error' in f]):
            return True
        return False

    @staticmethod
    def content_error(folder: str):
        folder_path = Path(folder)
        if bool([f for f in listdir(folder_path) if isfile(folder_path.joinpath(f)) and 'content_error' in f]):
            return True
        return False

    @staticmethod
    def adjust_frame(raw_frame: pd.DataFrame):
        frame = raw_frame.rename(columns={h: h.strip() for h in raw_frame.columns.tolist()})
        frame.Time = pd.to_datetime(frame.Time, utc=True)
        # frame.sort_values(by='Time', ignore_index=True, inplace=True)
        frame['duplicated'] = frame.duplicated(subset='Time')
        frame['stamp'] = frame.Time.apply(dt.timestamp).astype(int)
        frame['diff'] = frame.stamp.diff()
        frame['diff_sign'] = abs(frame['diff']) / frame['diff']
        frame['timestep_match'] = frame['diff'] == frame['diff'].iloc[1]
        return frame

    def __init__(self, month: int, year: int, waypoint: Waypoint, interval_time: int = 1):

        self.raw_frame = None
        self.adj_frame = None
        self.error = False
        error_type = None
        error_types = {'content': 'content_error', 'connection': 'connection_error'}

        if month < 1 or month > 12:
            self.error = ValueError
            raise self.error

        start = dt(year, month, 1)
        end = start + relativedelta(months=1) - relativedelta(days=1)

        header = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
        begin_date_field = "&begin_date=" + start.strftime("%Y%m%d")  # yyyymmdd
        end_date_field = "&end_date=" + end.strftime("%Y%m%d")  # yyyymmdd
        station_field = "&station=" + waypoint.id  # station id string
        interval_field = "&interval=" + str(interval_time)
        time_zone_field = '&time_zone=gmt'
        footer_wo_bin = "&product=currents_predictions" + interval_field + "&units=english&format=csv"
        # footer_w_bin = footer_wo_bin + "&bin=" + str(waypoint.bin)
        # footer = footer_wo_bin if waypoint.bin is None else footer_w_bin
        footer = footer_wo_bin  # requests wo bin seem to return shallowest predictions
        my_request = header + begin_date_field + end_date_field + station_field + time_zone_field + footer

        try:
            for _ in range(5):
                try:
                    my_response = requests.get(my_request)
                    my_response.raise_for_status()

                    # trap for download/communication errors - connection errors
                    if 'predictions are not available' in my_response.content.decode():
                        raise DataNotAvailable(f'<!> {waypoint.id} Predictions not available')
                    self.raw_frame = pd.read_csv(StringIO(my_response.content.decode()))
                    if self.raw_frame.empty or self.raw_frame.isna().all().all():
                        raise EmptyDataframe(f'<!> {waypoint.id} Dataframe empty or NaN')
                    break
                except Exception as err:
                    self.error = err
                    error_type = error_types['connection']
                    time.sleep(2)

            if self.error:
                raise self.error

            # trap for file/data integrity errors - content errors
            self.adj_frame = OneMonth.adjust_frame(self.raw_frame)

            if not self.adj_frame.Time.is_unique:
                error_type = error_types['content']
                raise DuplicateTimestamps(f'<!> {waypoint.id} Duplicate timestamps')
            if not self.adj_frame.stamp.is_monotonic_increasing:
                error_type = error_types['content']
                raise NonMonotonic(f'<!> {waypoint.id} Data not monotonic')
            if waypoint.type == 'H' and not self.adj_frame['timestep_match'][1:].all():
                error_type = error_types['content']
                raise DataMissing(f'<!> {waypoint.id} Data missing')

        except Exception as err:
            self.error = err
            error_text = type(err).__name__
            waypoint.folder.joinpath(f'{waypoint.id} {error_text}.{error_type}').touch()
            if self.raw_frame is not None:
                write_df(self.raw_frame, waypoint.folder.joinpath(f'month {month} raw frame.csv'))
            if self.adj_frame is not None:
                write_df(self.adj_frame, waypoint.folder.joinpath(f'month {month} adj frame.csv'))


class SixteenMonths:

    def __init__(self, year: int, waypoint: Waypoint):
        self.error = False

        months = []
        try:
            for m in range(11, 13):
                month = OneMonth(m, year - 1, waypoint)
                if month.error:
                    raise month.error
                months.append(month)

            for m in range(1, 13):
                month = OneMonth(m, year, waypoint)
                if month.error:
                    raise month.error
                months.append(month)

            for m in range(1, 3):
                month = OneMonth(m, year + 1, waypoint)
                if month.error:
                    self.error = month.error
                    raise month.error
                months.append(month)

        except Exception as err:
            self.error = err

        else:
            self.adj_frame = OneMonth.adjust_frame(pd.concat([m.raw_frame for m in months], axis=0, ignore_index=True))
            del months


class NonMonotonic(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DataNotAvailable(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DataMissing(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DuplicateTimestamps(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EmptyDataframe(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
