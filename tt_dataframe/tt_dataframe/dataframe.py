from pandas import DataFrame as PandasDataFrame, read_csv
from pathlib import Path
from io import StringIO


class DataFrame(PandasDataFrame):


    @property
    def _constructor(self):
        return self.__class__

    def write(self, csv_target: Path, **kwargs):
        if 'index' not in kwargs:
            kwargs['index'] = False
        self.to_csv(csv_target, **kwargs)
        return csv_target

    def __init__(self, data=None, *, csv_source: Path | StringIO = None, **kwargs):
        if csv_source is not None:
            data = read_csv(csv_source, usecols=kwargs.pop('columns', None))
        super().__init__(data, **kwargs)

