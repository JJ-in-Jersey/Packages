from datetime import datetime
from tt_file_tools.file_tools import SoupFromXMLResponse
from dateparser import parse

import pandas as pd
import requests
from io import StringIO


class TideXMLDataframe:

    def __init__(self, response):
        tree = SoupFromXMLResponse(response).tree

        self.frame = pd.DataFrame(columns=['date_time', 'date', 'time', 'HL'])
        for pr in tree.find_all('pr'):
            date_time = parse(pr.get('t'))
            date = date_time.date()
            time = date_time.time()
            hl = pr.get('type')
            self.frame.loc[len(self.frame)] = [date_time, date, time, hl]


def noaa_current_fetch(start, end, station: str):
    # request call returns CSV

    if end.year != start.year:
        raise ValueError

    station_split = station.split('_')
    station = station_split[0]
    bin_num = station_split[1] if len(station_split) > 1 else None

    interval = 60

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=" + start.strftime("%Y%m%d")
    u2 = "&end_date=" + end.strftime("%Y%m%d")
    u3 = "&station=" + station
    u4 = "&product=currents_predictions&time_zone=lst_ldt&interval=" + str(interval) + "&units=english&format=csv"
    u5 = "&bin=" + str(bin_num)
    url_base = u1 + u2 + u3 + u4
    url = url_base if not bin_num else url_base + u5

    # returns CSV
    response = requests.get(url)
    if response.status_code != 200:
        raise SystemExit(f'{station} request failed')
    else:
        frame = pd.read_csv(StringIO(response.content.decode()))
        return frame


def noaa_current_dataframe(start, end, station: str):
    # return speed of flowing water

    current_frame = pd.DataFrame()

    # start year
    frame = noaa_current_fetch(start, datetime(start.year, 12, 31), station)
    current_frame = pd.concat([current_frame, frame])

    # middle_year(s)
    if start.year + 1 == end.year - 1:
        frame = noaa_current_fetch(datetime(start.year + 1, 1, 1), datetime(start.year + 1, 12, 31), station)
        current_frame = pd.concat([current_frame, frame])
    else:
        for year in range(start.year + 1, end.year):
            frame = noaa_current_fetch(datetime(year, 1, 1), datetime(year, 12, 31), station)
            current_frame = pd.concat([current_frame, frame])

    # end year
    frame = noaa_current_fetch(datetime(end.year, 1, 1), end, station)
    current_frame = pd.concat([current_frame, frame])

    return current_frame


def noaa_tide_dataframe(start, end, station: str):
    # return height of flowing water

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=" + start.strftime("%Y%m%d")
    u2 = "&end_date=" + end.strftime("%Y%m%d")
    u3 = "&station=" + station
    u4 = "&product=predictions&datum=STND&time_zone=lst_ldt&interval=hilo&units=english&format=xml"
    url = u1 + u2 + u3 + u4

    response = requests.get(url)
    if response.status_code != 200:
        raise SystemExit(f'{station} request failed')
    else:
        frame = TideXMLDataframe(response.content).frame
        return frame


def noaa_slack_fetch(start, end, station: str):
    # request call returns CSV

    station_split = station.split('_')
    station = station_split[0]
    # bin_num = station_split[1] if len(station_split) > 1 else None

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=" + start.strftime("%Y%m%d")
    u2 = "&end_date=" + end.strftime("%Y%m%d")
    u3 = "&station=" + station
    u4 = "&product=currents_predictions&time_zone=lst_ldt&interval=MAX_SLACK&units=english&format=csv"
    url = u1 + u2 + u3 + u4

    response = requests.get(url)
    if response.status_code != 200:
        raise SystemExit(f'{station} request failed')
    else:
        frame = pd.read_csv(StringIO(response.content.decode()))
        return frame


def noaa_slack_dataframe(start, end, station: str):
    # return times of change in current, between high and low tide and close to zero

    slack_frame = pd.DataFrame()

    # start year
    frame = noaa_slack_fetch(start, datetime(start.year, 12, 31), station)
    slack_frame = pd.concat([slack_frame, frame])

    if start.year + 1 == end.year - 1:
        frame = noaa_slack_fetch(datetime(start.year + 1, 1, 1), datetime(start.year + 1, 12, 31), station)
        slack_frame = pd.concat([slack_frame, frame])
    else:
        for year in range(start.year + 1, end.year):
            frame = noaa_slack_fetch(datetime(year, 1, 1), datetime(year, 12, 31), station)
            slack_frame = pd.concat([slack_frame, frame])

    # end year
    frame = noaa_slack_fetch(datetime(end.year, 1, 1), end, station)
    slack_frame = pd.concat([slack_frame, frame])
    return slack_frame
