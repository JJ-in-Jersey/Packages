from pandas import DataFrame as PandasDataFrame, read_csv
import polars as pl
from pathlib import Path
from io import StringIO

POLARS_DTYPE_MAP = {
    int: pl.Int64,
    bool: pl.Boolean,
    float: pl.Float64,
    str: pl.Utf8,
    # Add other types as needed
}

class DataFrame(PandasDataFrame):


    @property
    def _constructor(self):
        return DataFrame


    def reconstruct_tuple_column(self, column_name, *col_types):
        """
        Args:
            column_name (str): column to be reconstructed/replaced.
            *col_types: type objects (e.g., int, bool, float) for the elements in the tuple.
        """

        bool_indices = [i for i, t in enumerate(col_types) if t is bool]
        index_name = self.index.name or 'index'
        pl_series = pl.Series(self[column_name].name, self[column_name])
        pl_df = pl.DataFrame({index_name: self.index.to_list(), column_name: pl_series})

        split_expr = pl_df[column_name].str.strip_chars('()').str.split(by=', ')

        elements = []
        for i, ct in enumerate(col_types):
            element_expr = split_expr.list.get(i)
            if i in bool_indices:
                expr = (pl.when(element_expr.str.to_uppercase() == "TRUE").then(pl.lit(True)).otherwise(pl.lit(False)))
            else:
                expr = element_expr.cast(POLARS_DTYPE_MAP.get(ct))
            elements.append(expr.alias(f"col_{i}"))

        pl_df = pl_df.with_columns(pl.struct(elements).alias(f"{column_name}_STRUCT"))

        result_df = pl_df.select([index_name, f"{column_name}_STRUCT"]).to_pandas()
        result_df = result_df.set_index(index_name)
        struct_list = result_df[f"{column_name}_STRUCT"].to_list()
        reconstructed_tuples = [tuple(d.values()) for d in struct_list]
        self[column_name] = reconstructed_tuples


    def write(self, csv_target: Path, **kwargs):
        if 'index' not in kwargs:
            kwargs['index'] = False
        self.to_csv(csv_target, **kwargs)
        return csv_target


    def __init__(self, data=None, *, csv_source: Path | StringIO = None, **kwargs):
        if csv_source is not None:
            data = read_csv(csv_source, usecols=kwargs.pop('columns', None))
        super().__init__(data, **kwargs)

