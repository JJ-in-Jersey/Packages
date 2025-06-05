from pandas import DataFrame as PandasDataFrame
from pathlib import Path
from io import StringIO, BytesIO
from typing import Union, TextIO, BinaryIO

class DataFrame(PandasDataFrame):

    _spreadsheet_row_limit = 950000

    @property
    def row_limit(self):
        return DataFrame._spreadsheet_row_limit

    @property
    def _constructor(self):
        return DataFrame

    def __init__(self, source: Union[str, Path, TextIO, BinaryIO, StringIO, BytesIO] = None,
                 data=None, *args, **kwargs):

        # Separate pandas DataFrame kwargs from read_csv kwargs
        df_specific_keys = {'index', 'columns', 'dtype', 'copy'}
        df_kwargs = {k: v for k, v in kwargs.items() if k in df_specific_keys}
        read_csv_kwargs = {k: v for k, v in kwargs.items() if k not in df_specific_keys}

        if source is not None:
            df_data = PandasDataFrame.read_csv(source, *args, **read_csv_kwargs)  # read_csv handles files & IO identically
            super().__init__(df_data, **df_kwargs)
        elif data is not None:
            super().__init__(data, *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def save_to_csv(self, file_path: Union[str, Path], **kwargs):
        self.to_csv(file_path, **kwargs)
        return file_path

    def save_to_csvs(self, file_path: Union[str, Path], **kwargs):
        suffix = '.csv'
        if len(self) > self.row_limit:
            num_of_spreadsheets = len(self) / self.row_limit
            whole_spreadsheets = len(self) // self.row_limit
            for i in range(whole_spreadsheets):
                output_stem = file_path.parent.joinpath(file_path.stem + '_spreadsheet_' + str(i))
                temp = self.loc[i * self.row_limit: i * self.row_limit + self.row_limit - 1]
                temp.to_csv(output_stem.with_suffix(output_stem.suffix + suffix), index=False)
            if num_of_spreadsheets > whole_spreadsheets:
                output_stem = file_path.parent.joinpath(file_path.stem + '_spreadsheet_' + str(whole_spreadsheets))
                temp = self.loc[whole_spreadsheets * self.row_limit:]
                temp.to_csv(output_stem.with_suffix(output_stem.suffix + suffix), index=False)
        return file_path