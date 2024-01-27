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


def noaa_current_fetch(start, end, folder: Path, station, bin_num=None):

    if end.year != start.year:
        raise ValueError

    interval = 60

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date="
    u2 = "&end_date="
    u3 = "&station=" + station + "&product=currents_predictions&time_zone=lst_ldt&interval=" + str(interval) + "&units=english&format=csv"
    u4 = "&bin=" + str(bin_num)

    url_base = u1 + start.strftime("%Y%m%d") + u2 + end.strftime("%Y%m%d") + u3
    url = url_base if not bin_num else url_base + u4

    response = requests.get(url)
    filepath = folder.joinpath(station + '_' + str(start.year) + '.csv')
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    return filepath


def noaa_current_dataframe(start, end, folder, station, bin_num=None):

    frame = pd.DataFrame()

    # start year
    file = noaa_current_fetch(start, datetime(start.year, 12, 31), folder, station, bin_num)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    if start.year + 1 == end.year - 1:
        file = noaa_current_fetch(datetime(start.year + 1, 1,1), datetime(start.year + 1, 12,31), folder, station, bin_num)
        frame = pd.concat([frame, pd.read_csv(file, header='infer')])
    else:
        for year in range(start.year + 1, end.year):
            file = noaa_current_fetch(datetime(year, 1, 1), datetime(year, 12, 31), folder, station, bin_num)
            frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    # end year
    file = noaa_current_fetch(datetime(end.year, 1, 1), end, folder, station, bin_num)
    frame = pd.concat([frame, pd.read_csv(file, header='infer')])

    return frame


def noaa_tide_dataframe(start, end, folder, station):

    filepath = folder.joinpath(station + '.xml')

    u1 = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date="
    u2 = "&end_date="
    u3 = "&station=" + station + "&product=predictions&datum=STND&time_zone=lst_ldt&interval=hilo&units=english&format=xml"

    url = u1 + start.strftime("%Y%m%d") + u2 + end.strftime("%Y%m%d") + u3
    response = requests.get(url)
    with open(filepath, mode="wb") as file:
        file.write(response.content)

    frame = TideXMLDataframe(filepath).frame

    return frame
