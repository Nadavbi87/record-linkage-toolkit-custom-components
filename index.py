from recordlinkage.base import BaseIndexAlgorithm
from recordlinkage.utils import listify, construct_multiindex
import pandas as pd
import numpy


def _extract_first_n_letters_series(series, num_of_letters=1):
    if pd.api.types.is_string_dtype(series):
        series = series.str[:num_of_letters]
    return series


class PrefixMatch(BaseIndexAlgorithm):
    def __init__(self, left_on=None, right_on=None, prefix_length=1, drop_na=True, **kwargs):
        super(PrefixMatch, self).__init__(**kwargs)
        # variables to block on
        self.left_on = left_on
        self.right_on = right_on
        self.prefix_length = prefix_length
        self.drop_na = drop_na

    def __repr__(self):

        class_name = self.__class__.__name__
        left_on, right_on = self._get_left_and_right_on()

        return "<{} left_on={!r}, right_on={!r}>".format(
            class_name, left_on, right_on)

    def _get_left_and_right_on(self):

        if self.right_on is None:
            return self.left_on, self.left_on
        else:
            return self.left_on, self.right_on

    def _prepare_dataset(self, df, on_list, new_index_col, blocking_keys):
        # 1. make a dataframe
        # 2. rename columns
        # 3. add index col
        # 4. drop na (last step to preserve index)
        data = pd.DataFrame(df[on_list], copy=False)
        data.columns = blocking_keys
        data[new_index_col] = numpy.arange(len(df))
        if self.drop_na:
            data.dropna(axis=0, how='any', subset=blocking_keys, inplace=True)
        return data.apply(lambda series: _extract_first_n_letters_series(series, self.prefix_length))

    def _link_index(self, df_a, df_b):

        left_on, right_on = self._get_left_and_right_on()
        left_on = listify(left_on)
        right_on = listify(right_on)

        blocking_keys = ["blocking_key_%d" % i for i, v in enumerate(left_on)]

        data_left = self._prepare_dataset(df_a, left_on, 'index_x', blocking_keys)
        data_right = self._prepare_dataset(df_b, right_on, 'index_y', blocking_keys)

        # merge dataframes
        dfs = []
        for column in blocking_keys:
            dfs.append(data_left.merge(data_right, how='inner', on=column))

        # concatenate merge results
        pairs_df = pd.concat(dfs)

        result = construct_multiindex(
            levels=[df_a.index.values, df_b.index.values],
            codes=[pairs_df['index_x'].values, pairs_df['index_y'].values],
            verify_integrity=False)

        # remove duplicate matching - (x,y), (y,x)
        result = result[~result.duplicated(keep='first')]

        return result
