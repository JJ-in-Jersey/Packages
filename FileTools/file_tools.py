from glob import glob
from os.path import join, getctime
import numpy as np
import pandas as pd
from MemoryHelper import MemoryHelper as mh

def newest_file(folder):
    types = ['*.txt', '*.csv']
    files = []
    for t in types: files.extend(glob(join(folder, t)))
    return max(files, key=getctime) if len(files) else None

def read_df(path):
    df = pd.read_csv(path.with_suffix('.csv'), header='infer')
    return mh.shrink_dataframe(df)

def write_df(df, path, include_index=False):
    df.to_csv(path.with_suffix('.csv'), index=False)
    excel_size = 1000000
    if len(df) > excel_size:
        num_of_spreadsheets = len(df)/excel_size
        whole_spreadsheets = len(df)//excel_size
        for i in range(whole_spreadsheets):
            temp = df.loc[i*excel_size: i*excel_size+excel_size-1]
            temp.to_csv(path.parent.joinpath(path.name+'_excel_'+str(i)).with_suffix('.csv'), index=include_index)
        if num_of_spreadsheets > whole_spreadsheets:
            temp = df.loc[whole_spreadsheets*excel_size:]
            temp.to_csv(path.parent.joinpath(path.name+'_excel_'+str(whole_spreadsheets)).with_suffix('.csv'), index=include_index)

def read_arr(path): return np.load(path.with_suffix('.npy'))

def write_arr(arr, path): np.save(path.with_suffix('.npy'), arr, allow_pickle=False)

def read_list(path): return list(read_arr(path))

def write_list(lst, path): write_arr(lst, path)

def csv_npy_file_exists(path): return True if path.with_suffix('.csv').exists() or path.with_suffix('.npy').exists() else False
