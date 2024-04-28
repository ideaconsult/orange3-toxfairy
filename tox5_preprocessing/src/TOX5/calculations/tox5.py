import pandas as pd
import numpy as np
from rpy2 import robjects
from rpy2.robjects import pandas2ri
import rpy2.robjects as ro
from rpy2.robjects.vectors import ListVector
from itertools import product
from sklearn.utils import resample
import re
import warnings

warnings.filterwarnings('ignore')


class TOX5:
    def __init__(self, data, cell, manual_names=None, manual_slices=None):
        self.data = data
        self.cell = cell
        self.manual_names = manual_names
        self.manual_slices = manual_slices

        self.__transformed_data_r = []
        self.__transformed_data = []
        self.__tox5_scores = pd.DataFrame()
        self.__all_slice_names = []

        self.slice_names = []
        self.slices = []

    @property
    def all_slice_names(self):
        self.__all_slice_names = list((self.data.loc[:, self.data.columns.str.startswith(tuple(self.cell))]).keys())
        return self.__all_slice_names

    @property
    def transformed_data_r(self):
        return self.__transformed_data_r

    @transformed_data_r.setter
    def transformed_data_r(self, value):
        self.__transformed_data_r = value

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

    def transform_data(self, user_transform_funcs):
        with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
            r_from_pd_df = ro.conversion.get_conversion().py2rpy(self.data)

        slice_names_ = robjects.StrVector(self.all_slice_names)
        user_transform_funcs_r = robjects.ListVector(user_transform_funcs)

        transforming_data = robjects.r('''
            transforming_data <- function(slice_names_, df, tf_dict){
                    yeo_johnson_wrapper <- function(x) {
                        if (length(unique(x)) == 1){
                            return(x)
                        }else{
                      # Estimate the optimal lambda using powerTransform()
                        yeo_transform <- powerTransform(x, family = "yjPower")
                        lambda_est <- yeo_transform$yjlambda
                      # Apply the Yeo-Johnson transformation using the estimated lambda
                        transformed_data <- yjPower(x, yeo_transform$lambda, jacobian.adjusted = FALSE)
                        }
                    }
                    
                    tf1 <- TxpTransFunc(function(x) sqrt(x))
                    tf2 <- TxpTransFunc(function(x) -log10(x)+6)
                    tf3 <- TxpTransFunc(yeo_johnson_wrapper)
                    trans_func <- TxpTransFuncList(sqrt_x = tf1, log10x_6 = tf2, yeo_johnson = tf3)

                    test_slice <- list()
                    slice_names <- c()

                    for (x in slice_names_){
                        slice_names <- c(slice_names, x)

                        if (grepl("1st",x,ignore.case=TRUE)){
                            test_slice <- append(test_slice, x = TxpSlice(x, trans_func[rep(tf_dict[["1st"]], 1)]))
                        }else if (grepl("auc",x,ignore.case=TRUE)){
                            test_slice <- append(test_slice, x = TxpSlice(x, trans_func[rep(tf_dict[["auc"]], 1)]))
                        } else if (grepl("max",x,ignore.case=TRUE)){
                            test_slice <- append(test_slice, x = TxpSlice(x, trans_func[rep(tf_dict[["max"]], 1)]))
                        }
                    }

                    names(test_slice) <- rev(slice_names)
                    model <- TxpModel(txpSlices = test_slice)
                    results <- txpCalculateScores(model = model, input = df, id.var = 'material')

                    return (as.data.frame((sort(results)), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
            }
        ''')
        self.transformed_data_r = transforming_data(slice_names_, r_from_pd_df, user_transform_funcs_r)

        with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
            self.transformed_data = ro.conversion.get_conversion().rpy2py(self.transformed_data_r)

    @staticmethod
    def _extract_endpoint(item):
        suffix_pattern = re.compile(r'(.+)(_w\d+)$')
        match = suffix_pattern.search(item)
        if match:
            # If a suffix is found, extract the part just before it
            item = match.group(1)
        return item.split('_')[-1]

    def generate_auto_slices(self, slicing_pattern='by_time_endpoint'):
        cell = set([item.split('_')[0] for item in self.all_slice_names])
        time = set([item.split('_')[1] for item in self.all_slice_names])
        endpoint = set([TOX5._extract_endpoint(item) for item in self.all_slice_names])
        self.slices = []

        if slicing_pattern == 'by_time_endpoint':
            self.slice_names = [f"{cell_str}_{time_str}_{endpoint_str}" for cell_str, time_str, endpoint_str in
                                product(cell, time, endpoint)]
            for cell_val, time_val, endpoint_val in product(cell, time, endpoint):
                tmp = []
                for string in self.all_slice_names:
                    pattern = fr'^(?=.*{cell_val})(?=.*{time_val})(?=.*{endpoint_val}).*'
                    if re.match(pattern, string):
                        tmp.append(string)
                if tmp:
                    self.slices.append(tmp)
        elif slicing_pattern == 'by_endpoint':
            self.slice_names = [f"{cell_str}_{endpoint_str}" for cell_str, endpoint_str in
                                product(cell, endpoint)]
            for cell_val, endpoint_val in product(cell, endpoint):
                tmp = []
                for string in self.all_slice_names:
                    pattern = fr'^(?=.*{cell_val})(?=.*{endpoint_val}).*'
                    if re.match(pattern, string):
                        tmp.append(string)
                if tmp:
                    self.slices.append(tmp)

    def add_weight(self, weight_factor, parameter):
        # parameter could be one of this: MAX, AUC, 1st_3SD, 1st_2SD
        cols_to_duplicate = [col for col in self.data.columns if parameter in col]

        for i in range(2, weight_factor + 1):
            for col in cols_to_duplicate:
                new_col_name = f'{col}_w{i}'
                self.data[new_col_name] = self.data[col]

    def calculate_tox5_scores(self, manual_slicing=False):
        if manual_slicing:
            slices_names = self.manual_names
            slices = self.manual_slices
        else:
            slices_names = self.slice_names
            slices = self.slices

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

        result = calculate_scores(self.transformed_data_r, slices_names_r, slices_r)

        with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
            self.tox5_scores = ro.conversion.get_conversion().rpy2py(result)

    def ci_slices(self, n_boot=1000, ci_level=0.95):
        ci_intervals = {}

        for group_name, group_columns in zip(self.slice_names, self.slices):
            group_data = self.transformed_data[group_columns]
            bootstrap_scores = []

            for _ in range(n_boot):
                resampled_data = resample(group_data, replace=True)
                statistic = np.mean(resampled_data)
                bootstrap_scores.append(statistic)

            # Compute confidence intervals
            # calculate the tail probability
            ci_low = np.percentile(bootstrap_scores, (1 - ci_level) / 2 * 100) #2.5%
            ci_high = np.percentile(bootstrap_scores, (1 + ci_level) / 2 * 100) #97.5%
            ci_intervals[group_name] = [ci_low, ci_high]

        df = pd.DataFrame.from_dict(ci_intervals, orient='index', columns=['low_ci', 'high_ci']).reset_index()
        df.rename(columns={'index': 'slice'}, inplace=True)

        return ci_intervals, df

    def ci_scores(self, n_boot=1000, ci_level=0.95):
        ci_intervals = {}
        for index, row in self.tox5_scores.iloc[:, 3:].iterrows():
            bootstrap_scores = []

            for _ in range(n_boot):
                resampled_row = resample(row, replace=True)
                statistic = np.mean(resampled_row)
                bootstrap_scores.append(statistic)

            ci_low = np.percentile(bootstrap_scores, (1 - ci_level) / 2 * 100)
            ci_high = np.percentile(bootstrap_scores, (1 + ci_level) / 2 * 100)

            material = self.tox5_scores.at[index, 'Material']
            ci_intervals[material] = [ci_low, ci_high]

        df = pd.DataFrame.from_dict(ci_intervals, orient='index', columns=['low_ci', 'high_ci']).reset_index()
        df.rename(columns={'index': 'slice'}, inplace=True)

        return ci_intervals, df
    