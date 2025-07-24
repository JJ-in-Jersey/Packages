from pandas import DataFrame as PandasDataFrame, read_csv
from pathlib import Path
from io import StringIO


class DataFrame(PandasDataFrame):

    def __init__(self, data=None, *, csv_source: Path | StringIO = None, **kwargs):
        if csv_source is not None:
            data = read_csv(csv_source, usecols=kwargs.pop('columns', None))
        super().__init__(data, **kwargs)

    @property
    def _constructor(self):
        return self.__class__

    def write(self, csv_target: Path, **kwargs):
        if 'index' not in kwargs:
            kwargs['index'] = False
        self.to_csv(csv_target, **kwargs)
        return csv_target

    # def save_to_csvs(self, file_path: Union[str, Path], **kwargs):
    #     suffix = '.csv'
    #     if len(self) > self.row_limit:
    #         num_of_spreadsheets = len(self) / self.row_limit
    #         whole_spreadsheets = len(self) // self.row_limit
    #         for i in range(whole_spreadsheets):
    #             output_stem = file_path.parent.joinpath(file_path.stem + '_spreadsheet_' + str(i))
    #             temp = self.loc[i * self.row_limit: i * self.row_limit + self.row_limit - 1]
    #             temp.to_csv(output_stem.with_suffix(output_stem.suffix + suffix), index=False)
    #         if num_of_spreadsheets > whole_spreadsheets:
    #             output_stem = file_path.parent.joinpath(file_path.stem + '_spreadsheet_' + str(whole_spreadsheets))
    #             temp = self.loc[whole_spreadsheets * self.row_limit:]
    #             temp.to_csv(output_stem.with_suffix(output_stem.suffix + suffix), index=False)
    #     return file_path
