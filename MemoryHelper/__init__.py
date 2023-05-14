from bs4 import BeautifulSoup as Soup
from Navigation import Navigation as NV
from pathlib import Path
from os import makedirs

class MemoryHelper:

    @staticmethod
    def shrink_dataframe(dataframe):
        for col in dataframe:
            if dataframe[col].dtype == np.int64:
                dataframe[col] = dataframe[col].astype(np.int32)
            elif dataframe[col].dtype == np.float64:
                dataframe[col] = dataframe[col].astype(np.half)
        return dataframe

    def __init__(self):
        pass
