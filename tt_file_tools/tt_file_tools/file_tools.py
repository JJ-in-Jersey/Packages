from time import sleep
from glob import glob
from os.path import join, getctime
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as bs


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


def read_df(path):
    return pd.read_csv(path.with_suffix('.csv'), engine='c', header='infer')


def shrink_df(path):
    return shrink_dataframe(pd.read_csv(path.with_suffix('.csv'), engine='c', header='infer'))


def read_arr(path): return np.load(path.with_suffix('.npy'))


def write_arr(arr, path):
    np.save(path.with_suffix('.npy'), arr, allow_pickle=False)
    while not csv_npy_file_exists(path):
        sleep(0.1)


def read_arr_to_list(path): return list(read_arr(path))


def write_list_to_array(lst, path): write_arr(lst, path)


def csv_npy_file_exists(path): return True if path.with_suffix('.csv').exists() or path.with_suffix('.npy').exists() else False


class XMLFile:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.tree = bs(f, "html.parser")


def write_df(df, path):
    df.to_csv(path.with_suffix('.csv'), index=False)
    excel_size = 950000
    if len(df) > excel_size:
        num_of_spreadsheets = len(df)/excel_size
        whole_spreadsheets = len(df)//excel_size
        for i in range(whole_spreadsheets):
            temp = df.loc[i*excel_size: i*excel_size+excel_size-1]
            temp.to_csv(path.parent.joinpath(path.name+'_excel_'+str(i)).with_suffix('.csv'), index=False)
        if num_of_spreadsheets > whole_spreadsheets:
            temp = df.loc[whole_spreadsheets*excel_size:]
            temp.to_csv(path.parent.joinpath(path.name+'_excel_'+str(whole_spreadsheets)).with_suffix('.csv'), index=False)


def shrink_dataframe(dataframe: pd.DataFrame):
    for col in dataframe:
        if dataframe[col].dtype == np.int64:
            dataframe[col] = dataframe[col].astype(np.int16)
        elif dataframe[col].dtype == np.float64:
            dataframe[col] = dataframe[col].astype(np.float16)
    return dataframe
