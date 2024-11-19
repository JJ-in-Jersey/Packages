from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import pandas as pd
import requests
from io import StringIO

from tt_file_tools.file_tools import SoupFromXMLResponse, print_file_exists, read_dict, write_dict, write_df
from tt_globals.globals import PresetGlobals
from tt_gpx.gpx import Waypoint


class StationDict:
    dict = {}

    @staticmethod
    def make_absolute_path_string(folder_name):
        return str(PresetGlobals.waypoints_folder.joinpath(folder_name).absolute())

    # @staticmethod
    # def integrity_check(start: datetime, end: datetime, time_series: pd.Series, type: str):
    #     minutes = {'H': pd.Timedelta(minutes=1), 'S': pd.Timedelta(minutes=6)}
    #     print(type)
    #     frame = pd.DataFrame(time_series)
    #     frame['datetime'] = pd.to_datetime(frame['Time'])
    #     frame['timestamp'] = frame['datetime'].apply(datetime.timestamp).astype('int')
    #     frame['time_diff'] = frame['timestamp'].diff()
    #     frame['correct_diff'] = frame['time_diff'] == minutes[type]
    #     if type == 'H':
    #         print(frame['correct_diff'].all())
    #         print(frame)
    #     return True

    def __init__(self):

        if print_file_exists(PresetGlobals.stations_file):
            StationDict.dict = read_dict(PresetGlobals.stations_file)
        else:
            StationDict.dict = {}
            my_request = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.xml?type=currentpredictions&units=english"
            for _ in range(3):
                try:
                    print(f'Requesting list of stations')
                    my_response = requests.get(my_request)
                    my_response.raise_for_status()
                    stations_tree = SoupFromXMLResponse(StringIO(my_response.content.decode())).tree
                    row_array = [{'id': station_tag.find_next('id').text,
                                  'name': station_tag.find_next('name').text,
                                  'lat': float(station_tag.find_next('lat').text),
                                  'lon': float(station_tag.find_next('lng').text),
                                  'type': station_tag.find_next('type').text}
                                 for station_tag in stations_tree.find_all('Station')]
                    row_df = pd.DataFrame(row_array).drop_duplicates()
                    row_df['folder'] = row_df['id'].apply(StationDict.make_absolute_path_string)
                    row_dict = row_df.to_dict('records')
                    print_file_exists(write_df(row_df, PresetGlobals.stations_folder.joinpath('stations.csv')))
                    StationDict.dict = {r['id']: r for r in row_dict}

                    print(f'Requesting bins for each station')
                    for station_id in self.dict.keys():
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
                                time.sleep(1)
                    print_file_exists(write_dict(PresetGlobals.stations_file, self.dict))
                    break
                except requests.exceptions.RequestException:
                    time.sleep(1)


class OneMonth:

    def __init__(self, month: int, year: int, waypoint: Waypoint, interval_time: int = 1):

        self.raw_frame = None
        self.error = False

        if month < 1 or month > 12:
            self.error = ValueError
            raise self.error

        start = datetime(year, month, 1)
        end = start + relativedelta(months=1) - relativedelta(days=1)

        header = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
        begin_date_field = "&begin_date=" + start.strftime("%Y%m%d")  # yyyymmdd
        end_date_field = "&end_date=" + end.strftime("%Y%m%d")  # yyyymmdd
        station_field = "&station=" + waypoint.id  # station id string
        interval_field = "&interval=" + str(interval_time)
        footer_wo_bin = "&product=currents_predictions&time_zone=lst_ldt" + interval_field + "&units=english&format=csv"
        # footer_w_bin = footer_wo_bin + "&bin=" + str(waypoint.bin)
        # footer = footer_wo_bin if waypoint.bin is None else footer_w_bin
        footer = footer_wo_bin  # requests wo bin seem to return shallowest predictions
        my_request = header + begin_date_field + end_date_field + station_field + footer

        try:
            for _ in range(5):
                try:
                    self.error = False
                    my_response = requests.get(my_request)
                    my_response.raise_for_status()

                    if 'predictions are not available' in my_response.content.decode():
                        self.error = DataNotAvailable(f'<!> {waypoint.id} Predictions are not available')
                        raise self.error
                    self.raw_frame = pd.read_csv(StringIO(my_response.content.decode()))

                    if self.raw_frame.empty or self.raw_frame.isna().all().all():
                        self.error =  EmptyDataframe(f'<!> {waypoint.id} Dataframe is empty or all NaN')
                        raise self.error

                    break
                except requests.exceptions.RequestException:
                    time.sleep(1)
                except DataNotAvailable:
                    time.sleep(1)
                except EmptyDataframe:
                    time.sleep(1)

            frame = self.raw_frame.rename(columns={h: h.strip() for h in self.raw_frame.columns.tolist()})
            frame['datetime'] = pd.to_datetime(frame['Time'])
            frame['timestamp'] = frame['datetime'].apply(pd.Timestamp)
            frame['timestamp'] = frame['timestamp'].apply(lambda x: x.value / 1000000000)
            frame['timestamp_diff'] = frame['timestamp'].diff()
            frame['datetime_diff'] = frame['datetime'].diff()

            if not frame['timestamp'].is_monotonic_increasing:
                write_df(self.raw_frame, waypoint.folder.joinpath(f'month {month} raw frame.csv'))
                write_df(frame, waypoint.folder.joinpath(f'month {month} not monotonic.csv'))
                self.error = NonMonotonic(f'<!> {waypoint.id} Timestamp is not monotonically increasing')
                raise self.error

            if waypoint.type == 'H':

                if not (frame.iloc[1]['timestamp_diff'] == frame['timestamp_diff'][1:]).all():
                    write_df(self.raw_frame, waypoint.folder.joinpath(f'month {month} raw frame.csv'))
                    write_df(frame, waypoint.folder.joinpath(f'month {month} missing data.csv'))
                    self.error = DataMissing(f'<!> {waypoint.id} Data is missing')
                    raise self.error

                if not frame['timestamp'].is_unique:
                    write_df(frame, waypoint.folder.joinpath(f'month {month} duplicate timestamps.csv'))
                    self.error = DuplicateTimestamps(f'<!> {waypoint.id} Duplicate timestamps')
                    raise self.error

        except DataMissing:
            pass
        except NonMonotonic:
            pass
        except DuplicateTimestamps:
            pass

class SixteenMonths:

    def __init__(self, year: int, waypoint: Waypoint):
        self.error = False

        months = []
        for m in range(11, 13):
            try:
                month = OneMonth(m, year - 1, waypoint)
                if month.error:
                    self.error = month.error
                    raise month.error
                months.append(month)
            except requests.exceptions.RequestException:
                pass
            except DataNotAvailable:
                pass
            except EmptyDataframe:
                pass
            except DataMissing:
                pass
            except NonMonotonic:
                pass
            except DuplicateTimestamps:
                pass

        for m in range(1, 13):
            try:
                month = OneMonth(m, year, waypoint)
                if month.error:
                    self.error = month.error
                    raise month.error
                months.append(month)
            except requests.exceptions.RequestException:
                pass
            except DataNotAvailable:
                pass
            except EmptyDataframe:
                pass
            except DataMissing:
                pass
            except NonMonotonic:
                pass
            except DuplicateTimestamps:
                pass

        for m in range(1, 3):
            try:
                month = OneMonth(m, year + 1, waypoint)
                if month.error:
                    self.error = month.error
                    raise month.error
                months.append(month)
            except requests.exceptions.RequestException:
                pass
            except DataNotAvailable:
                pass
            except EmptyDataframe:
                pass
            except DataMissing:
                pass
            except NonMonotonic:
                pass
            except DuplicateTimestamps:
                pass

        if not self.error:
            self.raw_frame = pd.concat([m.raw_frame for m in months], axis=0, ignore_index=True)
            self.frame = self.raw_frame.rename(columns={heading: heading.strip() for heading in self.raw_frame.columns.tolist()})
            self.frame.rename(columns={'Velocity_Major': 'velocity'}, inplace=True)
            self.frame['datetime'] = pd.to_datetime(self.frame['Time'])
            self.frame['timestamp'] = self.frame['datetime'].apply(pd.Timestamp)
            self.frame['timestamp'] = self.frame['timestamp'].apply(lambda x: x.value / 1000000000)
            self.frame['timestamp_diff'] = self.frame['timestamp'].diff()
            self.frame['datetime_diff'] = self.frame['datetime'].diff()

        for m in months:
            del m


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


# class CSVRequestFailed(Exception):
#     def __init__(self, message: str):
#         self.message = message
#         super().__init__(message)
