from datetime import datetime, timedelta
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


def noaa_current_datafile(folder: Path, year: int, month: int, interval, station, bin_num=None):

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date="
    u2 = "&end_date="
    u3 = "&station="
    u4 = "&product=currents_predictions&time_zone=lst_ldt&interval="
    u5 = "&units=english&format=csv&bin="

    if not bin_num:
        u5 = "&units=english&format=csv"

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year+1, 1, 1) - timedelta(days=1)

    url = u1 + start_date.strftime("%Y%m%d") + u2 + end_date.strftime("%Y%m%d") + u3 + station + u4 + str(interval) + str(bin_num) + u5
    response = requests.get(url)
    filepath = folder.joinpath(station + '_' + str(year) + '_' + str(month) + '.csv')
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    return filepath


def noaa_current_14_months(folder, year, interval, station, bin_num=None):

    frame = pd.DataFrame()

    file = noaa_current_datafile(folder, year - 1, 12, interval, station, bin_num)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    for m in range(1, 13):
        file = noaa_current_datafile(folder, year, m, interval, station, bin_num)
        frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    file = noaa_current_datafile(folder, year + 1, 1, interval, station, bin_num)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    return frame


def noaa_tide_datafile(folder: Path, year: int, month: int, station):

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date="
    u2 = "&end_date="
    u3 = "&station="
    u4 = "&product=predictions&datum=STND&time_zone=lst_ldt&interval=hilo&units=english&format=xml"

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year+1, 1, 1) - timedelta(days=1)

    url = u1 + start_date.strftime("%Y%m%d") + u2 + end_date.strftime("%Y%m%d") + u3 + station + u4
    response = requests.get(url)
    filepath = folder.joinpath(station + '_' + str(year) + '_' + str(month) + '.xml')
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    return filepath


def noaa_tide_14_months(folder, year, code):

    frame = pd.DataFrame()

    file = noaa_tide_datafile(folder, year - 1, 12, code)
    frame = pd.concat([frame, TideXMLDataframe(file).frame])

    for m in range(1, 13):
        file = noaa_tide_datafile(folder, year, m, code)
        frame = pd.concat([frame, TideXMLDataframe(file).frame])

    file = noaa_tide_datafile(folder, year + 1, 1, code)
    frame = pd.concat([frame, TideXMLDataframe(file).frame])

    return frame
