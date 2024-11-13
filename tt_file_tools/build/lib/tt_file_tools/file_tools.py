from time import sleep
from glob import glob
from os.path import join, getctime
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as Soup
from pathlib import Path
import json


def newest_file(folder):
    types = ['*.txt', '*.csv', '*.xml']
    files = []
    for t in types:
        files.extend(glob(join(folder, t)))
    return max(files, key=getctime) if len(files) else None


def wait_for_new_file(folder, event_function):
    newest_before = newest_after = newest_file(folder)
    event_function()
    while newest_before == newest_after:
        sleep(0.1)
        newest_after = newest_file(folder)
    return newest_after


def read_df(filepath: Path):
    if not filepath.exists():
        raise FileExistsError(filepath)
    return pd.read_csv(filepath, header='infer')


class SoupFromXMLFile:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.tree = Soup(f, "xml")


class SoupFromXMLResponse:
    def __init__(self, response):
        self.tree = Soup(response, 'xml')


def write_df(df: pd.DataFrame, path: Path, debug: bool = False):
    suffix = '.csv'
    df.to_csv(path, index=False)
    if debug:
        spreadsheet_limit = 950000
        if len(df) > spreadsheet_limit:
            num_of_spreadsheets = len(df)/spreadsheet_limit
            whole_spreadsheets = len(df)//spreadsheet_limit
            for i in range(whole_spreadsheets):
                output_stem = path.parent.joinpath(path.stem+'_spreadsheet_'+str(i))
                temp = df.loc[i*spreadsheet_limit: i*spreadsheet_limit+spreadsheet_limit-1]
                temp.to_csv(output_stem.with_suffix(output_stem.suffix + suffix), index=False)
            if num_of_spreadsheets > whole_spreadsheets:
                output_stem = path.parent.joinpath(path.stem+'_spreadsheet_'+str(whole_spreadsheets))
                temp = df.loc[whole_spreadsheets*spreadsheet_limit:]
                temp.to_csv(output_stem.with_suffix(output_stem.suffix + suffix), index=False)
    return path

def shrink_dataframe(dataframe: pd.DataFrame):
    for col in dataframe:
        if dataframe[col].dtype == np.int64:
            dataframe[col] = dataframe[col].astype(np.int16)
        elif dataframe[col].dtype == np.float64:
            dataframe[col] = dataframe[col].astype(np.float16)
    return dataframe


def print_file_exists(filepath: Path):
    checkmark = u'\N{check mark}'
    if filepath.exists():
        print(f'   {checkmark}   {str(filepath)}')
        return True
    else:
        print(f'   x   {str(filepath)}')
        return False


def read_text_arr(filepath: Path):
    with open(filepath) as text_file:
        lines = [line.splitlines()[0].split(",") for line in text_file]
    return lines


def write_dict(file: Path, dictionary: dict):
    with open(file, 'w') as a_file:
        json.dump(dictionary, a_file)
    return file


def read_dict(file: Path):
    if not file.exists():
        raise FileExistsError(file)
    with open(file, 'r') as a_file:
        return json.load(a_file)