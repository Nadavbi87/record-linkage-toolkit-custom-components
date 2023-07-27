from recordlinkage.algorithms.string import jaro_similarity, jarowinkler_similarity, levenshtein_similarity, \
    damerau_levenshtein_similarity, qgram_similarity, cosine_similarity, smith_waterman_similarity, \
    longest_common_substring_similarity
from recordlinkage.base import BaseCompareFeature
import pandas
from recordlinkage.utils import fillna as _fillna


class String(BaseCompareFeature):
    """Compute the (partial) similarity between strings values.

    This class is used to compare string values. The implemented algorithms
    are: 'jaro','jarowinkler', 'levenshtein', 'damerau_levenshtein', 'qgram'
    or 'cosine'. In case of agreement, the similarity is 1 and in case of
    complete disagreement it is 0. The Python Record Linkage Toolkit uses the
    `jellyfish` package for the Jaro, Jaro-Winkler, Levenshtein and Damerau-
    Levenshtein algorithms.

    Parameters
    ----------
    left_on : str or int
        The name or position of the column in the left DataFrame.
    right_on : str or int
        The name or position of the column in the right DataFrame.
    method : str, default 'levenshtein'
        An approximate string comparison method. Options are ['jaro',
        'jarowinkler', 'levenshtein', 'damerau_levenshtein', 'qgram',
        'cosine', 'smith_waterman', 'lcs']. Default: 'levenshtein'
    threshold : float, tuple of floats
        A threshold value. All approximate string comparisons higher or
        equal than this threshold are 1. Otherwise 0.
    missing_value : numpy.dtype
        The value for a comparison with a missing value. Default 0.
    """

    name = "string"
    description = "Compare string attributes of record pairs."

    def __init__(self,
                 left_on,
                 right_on,
                 method='levenshtein',
                 threshold=None,
                 below_threshold_normalize=True,
                 above_threshold_normalize=False,
                 missing_value=0.0,
                 label=None):
        super(String, self).__init__(left_on, right_on, label=label)

        self.method = method
        self.threshold = threshold
        self.missing_value = missing_value
        self.below_threshold_normalize = below_threshold_normalize
        self.above_threshold_normalize = above_threshold_normalize

    def _compute_vectorized(self, s_left, s_right):

        if self.method == 'jaro':
            str_sim_alg = jaro_similarity
        elif self.method in ['jarowinkler', 'jaro_winkler', 'jw']:
            str_sim_alg = jarowinkler_similarity
        elif self.method == 'levenshtein':
            str_sim_alg = levenshtein_similarity
        elif self.method in [
                'dameraulevenshtein', 'damerau_levenshtein', 'dl'
        ]:
            str_sim_alg = damerau_levenshtein_similarity
        elif self.method in ['q_gram', 'qgram']:
            str_sim_alg = qgram_similarity
        elif self.method == 'cosine':
            str_sim_alg = cosine_similarity
        elif self.method in ['smith_waterman', 'smithwaterman', 'sw']:
            str_sim_alg = smith_waterman_similarity
        elif self.method in ['longest_common_substring', 'lcs']:
            str_sim_alg = longest_common_substring_similarity
        else:
            raise ValueError("The algorithm '{}' is not known.".format(
                self.method))

        c = str_sim_alg(s_left, s_right)

        if self.threshold is not None:
            if self.below_threshold_normalize:
                c = c.where((c >= self.threshold) | (pandas.isnull(c)), other=0.0)
            if self.above_threshold_normalize:
                c = c.where((c < self.threshold) | (pandas.isnull(c)), other=1.0)

        c = _fillna(c, self.missing_value)

        return c