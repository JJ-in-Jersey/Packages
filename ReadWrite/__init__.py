import pandas as pd
import numpy as np
from pickle import HIGHEST_PROTOCOL

class ReadWrite:

    @staticmethod
    def read_df_csv(path): return pd.read_csv(path.with_suffix('.csv'), header='infer')

    @staticmethod
    def write_df_csv(df, path, include_index=False):
        df.to_csv(path.with_suffix('.csv'), index=include_index)
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

    @staticmethod
    def read_df_pkl(path): return pd.read_pickle(path.with_suffix('.pkl'))

    @staticmethod
    def write_df_pkl(df, path): df.to_pickle(path.with_suffix('.pkl'), protocol=HIGHEST_PROTOCOL)

    @staticmethod
    def read_df_hdf(path): return pd.read_hdf(path.with_suffix('.hdf'))

    @staticmethod
    def write_df_hdf(df, path): df.to_hdf(path.with_suffix('.hdf'), key='gonzo', mode='w', index=False)

    @classmethod
    def read_df(cls, path):
        if path.with_suffix('.csv').exists(): return cls.read_df_csv(path)
        elif path.with_suffix('.pkl').exists(): return cls.read_df_pkl(path)
        elif path.with_suffix('.hdf').exists(): return cls.read_df_hdf(path)
        else: print('Unrecognizable extension')

    @classmethod
    def write_df(cls, df, path, extension):
        if extension == 'csv': cls.write_df_csv(df, path)
        elif extension == 'pkl': cls.write_df_pkl(df, path)
        elif extension == 'hdf': cls.write_df_hdf(df, path)
        else: print('Unrecognizable extension')

    @staticmethod
    def read_arr(path): return np.load(path.with_suffix('.npy'))

    @staticmethod
    def write_arr(arr, path): np.save(path.with_suffix('.npy'), arr, allow_pickle=False)

    @classmethod
    def read_list(cls, path): return list(cls.read_arr(path))

    @classmethod
    def write_list(cls, lst, path): cls.write_arr(lst, path)

    def __init__(self):
        pass
