import pandas as pd
import numpy as np


def shrink_dataframe(dataframe: pd.DataFrame):
    for col in dataframe:
        if dataframe[col].dtype == np.int64:
            dataframe[col] = dataframe[col].astype(np.int32)
        elif dataframe[col].dtype == np.float64:
            dataframe[col] = dataframe[col].astype(np.float32)
    return dataframe
