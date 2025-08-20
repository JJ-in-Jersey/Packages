from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from pandas import concat, to_datetime
from numpy import sign
from time import sleep
import requests
from io import StringIO

from os.path import basename

from tt_dataframe.dataframe import DataFrame
from tt_dictionary.dictionary import Dictionary
from tt_file_tools.file_tools import SoupFromXMLResponse, print_file_exists
from tt_globals.globals import PresetGlobals
from tt_gpx.gpx import Waypoint
from tt_exceptions.exceptions import DataNotAvailable, EmptyResponse, DuplicateValues, NonMonotonic, DataMissing


class StationDict(Dictionary):

    def __init__(self):

        if PresetGlobals.stations_file.exists():
            super().__init__(json_source=PresetGlobals.stations_file)
        else:
            my_request = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.xml?type=currentpredictions&units=english"
            for _ in range(5):
                try:
                    print(f'Requesting list of stations')
                    my_response = requests.get(my_request)
                    my_response.raise_for_status()
                    stations_tree = SoupFromXMLResponse(StringIO(my_response.content.decode())).soup
                    row_array = [{'id': station_tag.find_next('id').text,
                                  'name': station_tag.find_next('name').text,
                                  'lat': float(station_tag.find_next('lat').text),
                                  'lon': float(station_tag.find_next('lng').text),
                                  'type': station_tag.find_next('type').text,
                                  'folder_name': station_tag.find_next('type').text + ' ' + station_tag.find_next('id').text}
                                 for station_tag in stations_tree.find_all('Station')]
                    row_df = DataFrame(row_array).drop_duplicates()
                    row_df['folder'] = row_df['folder_name'].apply(self.absolute_path_string)
                    row_dict = row_df.to_dict('records')
                    self.update({r['id']: r for r in row_dict})

                    print(f'Requesting bins for each station')
                    for station_id in self.keys():
                        print(f'==>   {station_id}')
                        my_request = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/" + station_id + "/bins.xml?units=english"
                        for _ in range(3):
                            try:
                                my_response = requests.get(my_request)
                                my_response.raise_for_status()
                                bins_tree = SoupFromXMLResponse(StringIO(my_response.content.decode())).soup
                                bin_count = int(bins_tree.find("nbr_of_bins").text)
                                if bin_count and bins_tree.find('Bin').find('depth') is not None:
                                    bin_dict = {int(tag.num.text): float(tag.depth.text) for tag in bins_tree.find_all('Bin')}
                                    bin_dict = dict(sorted(bin_dict.items(), key=lambda item: item[1]))
                                    self[station_id]['bins'] = bin_dict
                                break
                            except requests.exceptions.RequestException:
                                sleep(2)
                    print_file_exists(self.write(PresetGlobals.stations_file))
                    super().__init__(json_source=PresetGlobals.stations_file)
                    break
                except requests.exceptions.RequestException:
                    sleep(1)


    @staticmethod
    def absolute_path_string(folder_name):
        return str(PresetGlobals.waypoints_folder.joinpath(folder_name).absolute())


    def add_waypoint(self, route_waypoint: Waypoint):
        row = {'id': route_waypoint.id, 'name': route_waypoint.name,
               'lat': route_waypoint.lat, 'lon': route_waypoint.lon,
               'type': route_waypoint.type, 'folder_name': basename(route_waypoint.folder),
               'folder': StationDict.absolute_path_string(basename(route_waypoint.folder))}
        self[row['id']] = row
        print_file_exists(self.write(PresetGlobals.stations_file))


    def comment_waypoint(self, waypoint_id: str):
        if waypoint_id in self:
            print(f'Excluding {waypoint_id} from station dictionary')
            self['#' + waypoint_id] = self.pop(waypoint_id)
            self.write(PresetGlobals.stations_file)


class OneMonth(DataFrame):

    def __init__(self, month: int, year: int, waypoint: Waypoint):

        my_response = None

        if month < 1 or month > 12:
            raise ValueError

        try:
            attempts = 5
            for attempt in range(attempts):
                try:
                    my_response = requests.get(self.url(month, year, waypoint))
                    my_response.raise_for_status()
                    if not (my_response.content and my_response.text.strip() and bool(len(my_response.content))):
                        raise EmptyResponse
                    if 'predictions are not available' in my_response.content.decode():
                        raise DataNotAvailable
                    break  # break try-5 loop because the request was successful
                except Exception as e:
                    if attempt == attempts - 1:
                        raise e
                    sleep(2)
        except Exception as e:
            raise e

        try:
            frame = DataFrame(csv_source=StringIO(my_response.content.decode()))
            frame.columns = frame.columns.str.strip()

            if frame.empty or frame.isna().all().all():
                raise EmptyResponse(f'<!> {waypoint.id} Dataframe empty or NaN')
            frame.Time = to_datetime(frame.Time, utc=True)
            frame['duplicated'] = frame.duplicated(subset='Time')
            frame['stamp'] = frame.Time.apply(dt.timestamp).astype(int)
            frame['diff'] = frame.stamp.diff()
            frame['diff_sign'] = sign(frame['diff'])
            frame['timestep_match'] = frame['diff'] == frame['diff'].iloc[1]

            if not frame.Time.is_unique:
                raise DuplicateValues
            if not frame.stamp.is_monotonic_increasing:
                raise NonMonotonic
            if waypoint.type == 'H' and not frame['timestep_match'][1:].all():
                raise DataMissing
        except Exception as e:
            raise e
        else:
            super().__init__(data=frame)

    @staticmethod
    def url(month: int, year: int, waypoint: Waypoint, interval_time: int = 1):

        if month < 1 or month > 12:
            raise ValueError

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

        return header + begin_date_field + end_date_field + station_field + time_zone_field + footer


class SixteenMonths(DataFrame):

    def __init__(self, year: int, waypoint: Waypoint):

        frame = DataFrame()
        try:
            frame = concat([frame] + [OneMonth(m, year - 1, waypoint) for m in range(11, 13)], axis=0, ignore_index=True)
            frame = concat([frame] + [OneMonth(m, year, waypoint) for m in range(1, 13)], axis=0, ignore_index=True)
            frame = concat([frame] + [OneMonth(m, year + 1, waypoint) for m in range(1, 3)], axis=0, ignore_index=True)
            # for m in range(11,13):
            #     month = OneMonth(m, year -1, waypoint)
            #     frame = concat([frame, month], axis=0, ignore_index=True)
            # for m in range(1,13):
            #     month = OneMonth(m, year, waypoint)
            #     frame = concat([frame, month], axis=0, ignore_index=True)
            # for m in range(1,3):
            #     month = OneMonth(m, year + 1, waypoint)
            #     frame = concat([frame, month], axis=0, ignore_index=True)
        except Exception as e:
            raise e
        else:
            super().__init__(data=frame)
