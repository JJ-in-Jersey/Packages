from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from pandas import concat, to_datetime
from time import sleep
import requests
from io import StringIO
from os.path import basename

from tt_dataframe.dataframe import DataFrame
from tt_dictionary.dictionary import Dictionary
from tt_file_tools.file_tools import SoupFromXMLResponse, print_file_exists
import tt_globals.globals as fc_globals
from tt_gpx.gpx import Waypoint
from tt_exceptions.exceptions import EmptyResponse, DuplicateValues, NonMonotonic, PredictionsNotAvailable

from tt_job_manager.job_manager import JobManager

class StationDict(Dictionary):

    @classmethod
    def _convert_to_this(cls, json_dict: dict):
        return dict(json_dict)

    def __init__(self, job_manager: JobManager = None):
        if fc_globals.STATIONS_FILE.exists():
            super().__init__(json_source=fc_globals.STATIONS_FILE)
            return

        super().__init__()
        if not self and job_manager is not None:

            self.get_request()

            from tt_jobs.jobs import RequestBinJob
            keys = [job_manager.submit_job(RequestBinJob(station_id)) for station_id in self.keys()]
            # for station_id in self.keys():
            #     job = RequestBinJob(station_id)
            #     result = job.execute()
            job_manager.wait()

            for station_id in keys:
                self[station_id]['bins'] = job_manager.get_result(station_id)

            self.write(fc_globals.STATIONS_FILE)
        else:
            raise SyntaxError("StationDict requires existing STATIONS_FILE or JobManager")

    @staticmethod
    def absolute_path_string(folder_name):
        return str(fc_globals.WAYPOINTS_FOLDER.joinpath(folder_name).absolute())

    def add_waypoint(self, route_waypoint: Waypoint):
        row = {'id': route_waypoint.id, 'name': route_waypoint.name,
               'lat': route_waypoint.lat, 'lon': route_waypoint.lon,
               'type': route_waypoint.type, 'folder_name': basename(route_waypoint.folder),
               'folder': StationDict.absolute_path_string(basename(route_waypoint.folder))}
        self[row['id']] = row
        print_file_exists(self.write(fc_globals.STATIONS_FILE))

    def comment_waypoint(self, waypoint_id: str):
        if waypoint_id in self:
            print(f'Excluding {waypoint_id} from station dictionary')
            self['#' + waypoint_id] = self.pop(waypoint_id)
            self.write(fc_globals.STATIONS_FILE)

    def get_request(self):
        my_request = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.xml?type=currentpredictions&units=english"
        for _ in range(3):
            try:
                print(f'Requesting list of stations')
                my_response = requests.get(my_request)
                my_response.raise_for_status()
                stations_tree = SoupFromXMLResponse(StringIO(my_response.content.decode())).soup
                row_array = [{'id': station_tag.find_next('id').text,
                    'name': station_tag.find_next('name').text, 'lat': float(station_tag.find_next('lat').text),
                    'lon': float(station_tag.find_next('lng').text), 'type': station_tag.find_next('type').text,
                    'folder_name': station_tag.find_next('type').text + ' ' + station_tag.find_next('id').text}
                    for station_tag in stations_tree.find_all('Station')]
                row_df = DataFrame(row_array).drop_duplicates()
                row_df['folder'] = row_df['folder_name'].apply(self.absolute_path_string)
                row_dict = row_df.to_dict('records')
                self.update({r['id']: r for r in row_dict})
                break
            except requests.exceptions.RequestException:
                sleep(1)

class OneMonth(DataFrame):

    def __init__(self, month: int, year: int, waypoint: Waypoint):

        frame = None
        exception_message = f'{self.__class__.__name__} {waypoint.id} month: {month} year: {year}'

        if month < 1 or month > 12:
            raise ValueError

        attempts = 20
        for attempt in range(attempts):
            try:
                my_response = requests.get(self.url(month, year, waypoint))
                # check response
                my_response.raise_for_status()
                if 'predictions are not available' in my_response.content.decode():
                    raise PredictionsNotAvailable(f'{exception_message} attempt: {attempt + 1}')

                # create frame
                frame = DataFrame(csv_source=StringIO(my_response.content.decode()))
                frame.columns = frame.columns.str.strip()

                # check frame
                if frame.empty or frame.isna().all().all():
                    raise EmptyResponse(f'{exception_message} attempt: {attempt + 1}')
                if frame['Time'].duplicated().any():
                    raise DuplicateValues(f'{exception_message} attempt: {attempt + 1}')
                if not frame['Time'].is_monotonic_increasing:
                    raise NonMonotonic(f'{exception_message} attempt: {attempt + 1}')

                frame['Time'] = to_datetime(frame.Time, utc=True)
                frame.drop(columns=['Depth', 'Bin'], inplace=True)
                frame['stamp'] = frame.Time.apply(dt.timestamp).astype(int)

                break  # break for success
            except Exception as e:
                if isinstance(e, (PredictionsNotAvailable, DuplicateValues, NonMonotonic)):
                    raise
                if attempt < attempts - 1:
                    sleep(min(2 ** attempt, 8))
                else:
                    raise

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
        try:
            months = []
            months.extend([OneMonth(m, year - 1, waypoint) for m in range(11, 13)])
            months.extend([OneMonth(m, year, waypoint) for m in range(1, 13)])
            months.extend([OneMonth(m, year + 1, waypoint) for m in range(1, 3)])

            # print(f"Number of months: {len(months)}")
            # for i, m in enumerate(months):
            #     print(f"{waypoint.id}  Month {i}: shape={m.shape}, empty={m.empty}, all_na={m.isna().all().all()}")

            frame = concat(months, axis=0, ignore_index=True)
        except Exception as e:
            raise e
        else:
            super().__init__(data=frame)
