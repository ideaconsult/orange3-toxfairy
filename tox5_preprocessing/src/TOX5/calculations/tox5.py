import pandas as pd
from rpy2 import robjects
from rpy2.robjects.packages import importr, data
from rpy2.robjects import pandas2ri
import rpy2.robjects as ro
from rpy2.robjects.vectors import ListVector

from itertools import product
import re

# import warnings
# warnings.filterwarnings('ignore')
# utils.install_packages('toxpiR')

base = importr("base")
utils = importr("utils")
utils.chooseCRANmirror(ind=1)
toxpiR = importr("toxpiR")


class TOX5:
    def __init__(self, data, cell, manual_names=None, manual_slices=None):
        self.data = data
        self.cell = cell
        self.manual_names = manual_names
        self.manual_slices = manual_slices

        self.__transformed_data = []
        self.__tox5_scores = pd.DataFrame()
        self.__all_slice_names = list((self.data.loc[:, self.data.columns.str.startswith(tuple(self.cell))]).keys())

    @property
    def all_slice_names(self):
        return self.__all_slice_names

    @property
    def transformed_data(self):
        return self.__transformed_data

    @transformed_data.setter
    def transformed_data(self, value):
        self.__transformed_data = value

    @property
    def tox5_scores(self):
        return self.__tox5_scores

    @tox5_scores.setter
    def tox5_scores(self, value):
        self.__tox5_scores = value

    def transform_data(self):
        with ro.default_converter + pandas2ri.converter:
            r_from_pd_df = ro.conversion.get_conversion().py2rpy(self.data)

        slice_names_ = robjects.StrVector(self.all_slice_names)

        transforming_data = robjects.r('''
            transforming_data <- function(slice_names_, df){
                    trans_func <- TxpTransFuncList(tf1 = function(x) sqrt(x), tf2 = function(x) -log10(x)+6)

                    test_slice <- list()
                    slice_names <- c()

                    for (x in slice_names_){
                        slice_names <- c(slice_names, x)

                        if (grepl("1st",x,ignore.case=TRUE)){
                            test_slice <- append(test_slice, x = TxpSlice(x, trans_func[rep("tf2", 1)]))
                        }else if (grepl("auc",x,ignore.case=TRUE)){
                            test_slice <- append(test_slice, x = TxpSlice(x, trans_func[rep("tf1", 1)]))
                        } else if (grepl("max",x,ignore.case=TRUE)){
                            test_slice <- append(test_slice, x = TxpSlice(x, trans_func[rep("tf2", 1)]))
                        }
                    }

                    names(test_slice) <- rev(slice_names)
                    model <- TxpModel(txpSlices = test_slice)
                    results <- txpCalculateScores(model = model, input = df, id.var = 'material')

                    return (as.data.frame((sort(results)), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
            }
        ''')
        self.transformed_data = transforming_data(slice_names_, r_from_pd_df)

    def generate_auto_slices(self, slicing_pattern='by_time_endpoint'):
        cell = set([item.split('_')[0] for item in self.all_slice_names])
        time = set([item.split('_')[1] for item in self.all_slice_names])
        endpoint = set([item.split('_')[-1] for item in self.all_slice_names])

        slices_names = []
        slices = []

        if slicing_pattern == 'by_time_endpoint':
            slices_names = [f"{cell_str}_{time_str}_{endpoint_str}" for cell_str, time_str, endpoint_str in
                            product(cell, time, endpoint)]
            for cell_val, time_val, endpoint_val in product(cell, time, endpoint):
                tmp = []
                for string in self.all_slice_names:
                    pattern = fr'^(?=.*{cell_val})(?=.*{time_val})(?=.*{endpoint_val}).*'
                    if re.match(pattern, string):
                        tmp.append(string)
                if tmp:
                    slices.append(tmp)
        elif slicing_pattern == 'by_endpoint':
            slices_names = [f"{cell_str}_{endpoint_str}" for cell_str, endpoint_str in
                            product(cell, endpoint)]
            for cell_val, endpoint_val in product(cell, endpoint):
                tmp = []
                for string in self.all_slice_names:
                    pattern = fr'^(?=.*{cell_val})(?=.*{endpoint_val}).*'
                    if re.match(pattern, string):
                        tmp.append(string)
                if tmp:
                    slices.append(tmp)

        return slices_names, slices

    def calculate_tox5_scores(self, slices_pattern='by_time_endpoint', manual_slicing=False):
        if manual_slicing:
            slices_names = self.manual_names
            slices = self.manual_slices
        else:
            slices_names, slices = self.generate_auto_slices(slices_pattern)

        slices_names_r = robjects.StrVector(slices_names)
        slices_r = ListVector([(str(i), x) for i, x in enumerate(slices)])
        calculate_scores = robjects.r('''
                    calculate_scores <- function(df, slices_names_r, slices_r){
                        toxpi_slices <- list()
                        slice_names <- c()
                        i<-1
                        for (n in slices_names_r){
                            tmp <- unlist(slices_r[i])
                            i<-i+1
                            toxpi_slices <- append(toxpi_slices, TxpSlice(tmp))
                        }

                        names(toxpi_slices) <- slices_names_r
                        model <- TxpModel(txpSlices = as.TxpSliceList(toxpi_slices))
                        results <- txpCalculateScores(model = model, input = df, id.var = 'Material')
                        return (as.data.frame((sort(results)), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
                    }
                ''')

        result = calculate_scores(self.transformed_data, slices_names_r, slices_r)

        with ro.default_converter + pandas2ri.converter:
            self.tox5_scores = ro.conversion.get_conversion().rpy2py(result)
