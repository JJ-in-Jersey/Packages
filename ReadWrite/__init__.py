# import pandas as pd
# import numpy as np
# from MemoryHelper import MemoryHelper as mh
# class ReadWrite:
#
#     @staticmethod
#     def read_df(path):
#         df = pd.read_csv(path.with_suffix('.csv'), header='infer')
#         return mh.shrink_dataframe(df)
#
#     @staticmethod
#     def write_df(df, path, include_index=False):
#         # df.to_csv(path.with_suffix('.csv'), index=include_index)
#         df.to_csv(path.with_suffix('.csv'), index=False)
#         excel_size = 1000000
#         if len(df) > excel_size:
#             num_of_spreadsheets = len(df)/excel_size
#             whole_spreadsheets = len(df)//excel_size
#             for i in range(whole_spreadsheets):
#                 temp = df.loc[i*excel_size: i*excel_size+excel_size-1]
#                 temp.to_csv(path.parent.joinpath(path.name+'_excel_'+str(i)).with_suffix('.csv'), index=include_index)
#             if num_of_spreadsheets > whole_spreadsheets:
#                 temp = df.loc[whole_spreadsheets*excel_size:]
#                 temp.to_csv(path.parent.joinpath(path.name+'_excel_'+str(whole_spreadsheets)).with_suffix('.csv'), index=include_index)
#
#     @staticmethod
#     def read_arr(path): return np.load(path.with_suffix('.npy'))
#
#     @staticmethod
#     def write_arr(arr, path): np.save(path.with_suffix('.npy'), arr, allow_pickle=False)
#
#     @classmethod
#     def read_list(cls, path): return list(cls.read_arr(path))
#
#     @classmethod
#     def write_list(cls, lst, path): cls.write_arr(lst, path)
#
#     def __init__(self):
#         pass
