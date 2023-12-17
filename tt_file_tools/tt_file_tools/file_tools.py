from time import sleep
from glob import glob
from os.path import join, getctime
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as Soup
from pathlib import Path


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


def read_df(filepath):
    return pd.read_csv(filepath, header='infer')


def read_arr(path): return np.load(path.with_suffix('.npy'))


def write_arr(arr, path):
    np.save(path.with_suffix('.npy'), arr, allow_pickle=False)
    while not path.exists():
        sleep(0.1)


def read_arr_to_list(path): return list(read_arr(path))


def write_list_to_array(lst, path): write_arr(lst, path)


class XMLFile:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.tree = Soup(f, "html.parser")


def write_df(df, path):
    df.to_csv(path, index=False)
    spreadsheet_limit = 950000
    if len(df) > spreadsheet_limit:
        num_of_spreadsheets = len(df)/spreadsheet_limit
        whole_spreadsheets = len(df)//spreadsheet_limit
        for i in range(whole_spreadsheets):
            temp = df.loc[i*spreadsheet_limit: i*spreadsheet_limit+spreadsheet_limit-1]
            temp.to_csv(path.parent.joinpath(path.stem+'_spreadsheet_'+str(i)).with_suffix('.csv'), index=False)
        if num_of_spreadsheets > whole_spreadsheets:
            temp = df.loc[whole_spreadsheets*spreadsheet_limit:]
            temp.to_csv(path.parent.joinpath(path.stem+'_spreadsheet_'+str(whole_spreadsheets)).with_suffix('.csv'), index=False)


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
    else:
        print(f'   x {str(filepath)}')