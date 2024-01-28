from datetime import datetime
from tt_file_tools.file_tools import XMLFile
from dateparser import parse

import pandas as pd
import requests
from pathlib import Path


class TideXMLDataframe:

    def __init__(self, filepath):
        tree = XMLFile(filepath).tree

        self.frame = pd.DataFrame(columns=['date_time', 'date', 'time', 'HL'])
        for pr in tree.find_all('pr'):
            date_time = parse(pr.get('t'))
            date = date_time.date()
            time = date_time.time()
            hl = pr.get('type')
            self.frame.loc[len(self.frame)] = [date_time, date, time, hl]


def noaa_current_fetch(start, end, folder: Path, station: str):

    if end.year != start.year:
        raise ValueError

    station_split = station.split('_')
    station = station_split[0]
    bin_num = station_split[1] if len(station_split) > 1 else None
    # print(station, bin_num)

    filepath = folder.joinpath(station + '_' + str(start.year) + '_current.csv')
    interval = 60

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=" + start.strftime("%Y%m%d")
    u2 = "&end_date=" + end.strftime("%Y%m%d")
    u3 = "&station=" + station
    u4 = "&product=currents_predictions&time_zone=lst_ldt&interval=" + str(interval) + "&units=english&format=csv"
    u5 = "&bin=" + str(bin_num)
    url_base = u1 + u2 + u3 + u4
    url = url_base if not bin_num else url_base + u5

    response = requests.get(url)
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    return filepath


def noaa_current_dataframe(start, end, folder: Path, station: str):
    # return speed of flowing water

    frame = pd.DataFrame()

    # start year
    file = noaa_current_fetch(start, datetime(start.year, 12, 31), folder, station)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    if start.year + 1 == end.year - 1:
        file = noaa_current_fetch(datetime(start.year + 1, 1,1), datetime(start.year + 1, 12,31), folder, station)
        frame = pd.concat([frame, pd.read_csv(file, header='infer')])
    else:
        for year in range(start.year + 1, end.year):
            file = noaa_current_fetch(datetime(year, 1, 1), datetime(year, 12, 31), folder, station)
            frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    # end year
    file = noaa_current_fetch(datetime(end.year, 1, 1), end, folder, station)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    return frame


def noaa_tide_dataframe(start, end, folder: Path, station: str):
    # return height of flowing water

    filepath = folder.joinpath(station + '_tide.xml')

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=" + start.strftime("%Y%m%d")
    u2 = "&end_date=" + end.strftime("%Y%m%d")
    u3 = "&station=" + station
    u4 = "&product=predictions&datum=STND&time_zone=lst_ldt&interval=hilo&units=english&format=xml"
    url = u1 + u2 + u3 + u4

    response = requests.get(url)
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    frame = TideXMLDataframe(filepath).frame

    return frame

def noaa_slack_fetch(start, end, folder: Path, station: str):

    station_split = station.split('_')
    station = station_split[0]
    bin_num = station_split[1] if len(station_split) > 1 else None
    # print(station, bin_num)

    filepath = folder.joinpath(station + '_slack.csv')

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=" + start.strftime("%Y%m%d")
    u2 = "&end_date=" + end.strftime("%Y%m%d")
    u3 = "&station=" + station
    u4 = "&product=currents_predictions&time_zone=lst_ldt&interval=MAX_SLACK&units=english&format=csv"
    url = u1 + u2 + u3 + u4

    response = requests.get(url)
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    return filepath

def noaa_slack_dataframe(start, end, folder: Path, station: str):
    # return times of change in current, between high and low tide and close to zero

    frame = pd.DataFrame()

    # start year
    file = noaa_slack_fetch(start, datetime(start.year, 12, 31), folder, station)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    if start.year + 1 == end.year - 1:
        file = noaa_slack_fetch(datetime(start.year + 1, 1,1), datetime(start.year + 1, 12,31), folder, station)
        frame = pd.concat([frame, pd.read_csv(file, header='infer')])
    else:
        for year in range(start.year + 1, end.year):
            file = noaa_slack_fetch(datetime(year, 1, 1), datetime(year, 12, 31), folder, station)
            frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    # end year
    file = noaa_current_fetch(datetime(end.year, 1, 1), end, folder, station)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    return frame