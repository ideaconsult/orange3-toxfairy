import pandas as pd
from rpy2 import robjects
from rpy2.robjects.packages import importr, data
from rpy2.robjects import pandas2ri
import rpy2.robjects as ro
from rpy2.robjects.vectors import ListVector
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

        self.slice_names_ = []
        self.first_tox5_df = []
        self.tox5_score = pd.DataFrame()

    def calculate_first_tox5(self):
        df_by_cell = self.data.loc[:, self.data.columns.str.startswith(self.cell)]
        df_cells = (list(df_by_cell.keys()))

        with ro.default_converter + pandas2ri.converter:
            r_from_pd_df = ro.conversion.get_conversion().py2rpy(self.data)

        self.slice_names_ = robjects.StrVector(df_cells)

        first_part_tox5 = robjects.r('''
            first_part_tox5 <- function(slice_names_, df){
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
        self.first_tox5_df = first_part_tox5(self.slice_names_, r_from_pd_df)

    def calculate_manual_slicing(self):
        slice_manual_names = robjects.StrVector(self.manual_names)
        slices = ListVector([(str(i), x) for i, x in enumerate(self.manual_slices)])

        manual_slicing_tox5 = robjects.r('''
            manual_slicing_tox5 <- function(df, slice_manual_names, slices){
                toxpi_slices <- list()
                slice_names <- c()
                i<-1
                for (n in slice_manual_names){
                    tmp <- unlist(slices[i])
                    i<-i+1
                    toxpi_slices <- append(toxpi_slices, TxpSlice(tmp))
                }

                names(toxpi_slices) <- slice_manual_names
                model <- TxpModel(txpSlices = as.TxpSliceList(toxpi_slices))
                results <- txpCalculateScores(model = model, input = df, id.var = 'Material')
                return (as.data.frame((sort(results)), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
            }
        ''')
        result = manual_slicing_tox5(self.first_tox5_df, slice_manual_names, slices)

        with ro.default_converter + pandas2ri.converter:
            self.tox5_score = ro.conversion.get_conversion().rpy2py(result)

    def calculate_second_tox5_by_endpoint(self):
        second_part_tox5 = robjects.r('''
            second_part_tox5 <- function(df, slice_names_){

                pattern_dapi <- "Dapi"
                pattern_h2ax <- "H2AX"
                pattern_ctg <- "CTG"
                pattern_casp <- "Casp"
                pattern_ohg <- "8OHG"

                Dapi <- slice_names_[grepl(pattern_dapi, slice_names_)]
                H2AX <- slice_names_[grepl(pattern_h2ax, slice_names_)]
                CTG <- slice_names_[grepl(pattern_ctg, slice_names_)]
                CASP <- slice_names_[grepl(pattern_casp, slice_names_)]
                OHG <- slice_names_[grepl(pattern_ohg, slice_names_)]


                toxpi_slices <- TxpSliceList(
                                Dapi = TxpSlice(Dapi),
                                H2AX = TxpSlice(H2AX),
                                CTG = TxpSlice(CTG),
                                CASP = TxpSlice(CASP),
                                OHG = TxpSlice(OHG)
                              )
                model <- TxpModel(txpSlices = toxpi_slices)
                results <- txpCalculateScores(model = model, input = df, id.var = 'Material')

                return (as.data.frame(sort(results), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
            }
        ''')

        result = second_part_tox5(self.first_tox5_df, self.slice_names_)

        with ro.default_converter + pandas2ri.converter:
            self.tox5_score = ro.conversion.get_conversion().rpy2py(result)

    def calculate_second_tox5_by_endpoint_time(self):
        second_part_tox5 = robjects.r('''
            second_part_tox5 <- function(df, slice_names_){
                pattern_dapi <- "Dapi"
                pattern_h2ax <- "H2AX"
                pattern_ctg <- "CTG"
                pattern_casp <- "Casp"
                pattern_ohg <- "8OHG"

                dapi_6h <- slice_names_[grepl(pattern_dapi, slice_names_) & grepl("6H", slice_names_)]
                dapi_24h <- slice_names_[grepl(pattern_dapi, slice_names_) & grepl("24H", slice_names_)]
                dapi_72h <- slice_names_[grepl(pattern_dapi, slice_names_) & grepl("72H", slice_names_)]

                H2AX_6h <- slice_names_[grepl(pattern_h2ax, slice_names_) & grepl("6H", slice_names_)]
                H2AX_24h <- slice_names_[grepl(pattern_h2ax, slice_names_) & grepl("24H", slice_names_)]
                H2AX_72h <- slice_names_[grepl(pattern_h2ax, slice_names_) & grepl("72H", slice_names_)]

                CTG_6h <- slice_names_[grepl(pattern_ctg, slice_names_) & grepl("6H", slice_names_)]
                CTG_24h <- slice_names_[grepl(pattern_ctg, slice_names_) & grepl("24H", slice_names_)]
                CTG_72h <- slice_names_[grepl(pattern_ctg, slice_names_) & grepl("72H", slice_names_)]

                CASP_6h <- slice_names_[grepl(pattern_casp, slice_names_) & grepl("6H", slice_names_)]
                CASP_24h <- slice_names_[grepl(pattern_casp, slice_names_) & grepl("24H", slice_names_)]
                CASP_72h <- slice_names_[grepl(pattern_casp, slice_names_) & grepl("72H", slice_names_)]

                OHG_6h <- slice_names_[grepl(pattern_ohg, slice_names_) & grepl("6H", slice_names_)]
                OHG_24h <-slice_names_[grepl(pattern_ohg, slice_names_) & grepl("24H", slice_names_)]
                OHG_72h <- slice_names_[grepl(pattern_ohg, slice_names_) & grepl("72H", slice_names_)]

                toxpi_slices <- TxpSliceList(
                                Dapi_6h = TxpSlice(dapi_6h),
                                Dapi_24h = TxpSlice(dapi_24h),
                                Dapi_72h = TxpSlice(dapi_72h),
                                H2AX_6h = TxpSlice(H2AX_6h),
                                H2AX_24h = TxpSlice(H2AX_24h),
                                H2AX_72h = TxpSlice(H2AX_72h),
                                CTG_6h = TxpSlice(CTG_6h),
                                CTG_24h = TxpSlice(CTG_24h),
                                CTG_72h = TxpSlice(CTG_72h),
                                CASP_6h = TxpSlice(CASP_6h),
                                CASP_24h = TxpSlice(CASP_24h),
                                CASP_72h = TxpSlice(CASP_72h),
                                OHG_6h = TxpSlice(OHG_6h),
                                OHG_24h = TxpSlice(OHG_24h),
                                OHG_72h = TxpSlice(OHG_72h)
                                )

                model <- TxpModel(txpSlices = toxpi_slices)
                results <- txpCalculateScores(model = model, input = df, id.var = 'Material')

                return (as.data.frame(sort(results), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
            }
        ''')

        result = second_part_tox5(self.first_tox5_df, self.slice_names_)

        with ro.default_converter + pandas2ri.converter:
            self.tox5_score = ro.conversion.get_conversion().rpy2py(result)


