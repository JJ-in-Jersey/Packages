from datetime import datetime, timedelta
import requests
from pathlib import Path


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
