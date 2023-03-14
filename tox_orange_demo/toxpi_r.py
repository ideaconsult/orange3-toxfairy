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


def calculate_first_tox5(df, cell):
    df_by_cell = df.loc[:, df.columns.str.startswith(cell)]
    df_cells = (list(df_by_cell.keys()))

    with ro.default_converter + pandas2ri.converter:
        r_from_pd_df = ro.conversion.get_conversion().py2rpy(df)

    slice_names_ = robjects.StrVector(df_cells)

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
    result = first_part_tox5(slice_names_, r_from_pd_df)

    return result,  slice_names_


def calculate_manual_slicing(df, manual_names, manual_slices):
    slice_manual_names = robjects.StrVector(manual_names)
    slices = ListVector([(str(i), x) for i, x in enumerate(manual_slices)])

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
            
            print(toxpi_slices)
            print(typeof(toxpi_slices))
            print(length(toxpi_slices))
            print(slice_manual_names)
            
            names(toxpi_slices) <- slice_manual_names
            toxpi_slice_list = as.TxpSliceList(toxpi_slices)
            
            
            print(toxpi_slice_list)
            print(length(toxpi_slice_list))
            
            model <- TxpModel(txpSlices = toxpi_slice_list)
            results <- txpCalculateScores(model = model, input = df, id.var = 'material')

            return (as.data.frame((sort(results)), id.name = "Material", score.name = "toxpi_score", rank.name = "rnk"))
        }
    ''')

    # TODO: length(TxpIDx) != length(object)

    result = manual_slicing_tox5(df, slice_manual_names, slices)

    with ro.default_converter + pandas2ri.converter:
        pd_from_r_df = ro.conversion.get_conversion().rpy2py(result)

    return pd_from_r_df


def calculate_second_tox5_by_endpoint(df, slice_names_):
    second_part_tox5 = robjects.r('''
        second_part_tox5 <- function(df, slice_names_){

            Dapi <- c()
            H2AX <- c()
            CTG <- c()
            CASP <- c()
            OHG <- c()

            for (x in slice_names_){
                if (grepl('DAPI', x)){
                    Dapi <- c(Dapi, x)
                }

                if (grepl('H2AX', x)){
                    H2AX<- c(H2AX, x)
                }

                if (grepl('CTG', x)){
                    CTG <- c(CTG, x)
                }

                if (grepl('CASP', x) ){
                    CASP <- c(CASP, x)
                }

                if (grepl('OHG-1', x)){
                    OHG <- c(OHG, x)
                }

            }

            toxpi_slices <- TxpSliceList(
                            Dapi = TxpSlice(Dapi),
                            H2AX = TxpSlice(H2AX),
                            CTG = TxpSlice(CTG),
                            CASP = TxpSlice(CASP),
                            OHG = TxpSlice(OHG)
                          )
            # print(toxpi_slices)
            # print(length(toxpi_slices))

            model <- TxpModel(txpSlices = toxpi_slices)
            results <- txpCalculateScores(model = model, input = df, id.var = 'Material')


            return (as.data.frame(sort(results), id.name = "material", score.name = "toxpi_score", rank.name = "rnk"))
        }
    ''')

    result = second_part_tox5(df, slice_names_)

    with ro.default_converter + pandas2ri.converter:
        pd_from_r_df = ro.conversion.get_conversion().rpy2py(result)

    return pd_from_r_df


def calculate_second_tox5_by_endpoint_time(df, slice_names_):
    second_part_tox5 = robjects.r('''
        second_part_tox5 <- function(df, slice_names_){

            dapi_6h <- c()
            dapi_24h <- c()
            dapi_72h <- c()

            H2AX_6h <- c()
            H2AX_24h <- c()
            H2AX_72h <- c()

            CTG_6h <- c()
            CTG_24h <- c()
            CTG_72h <- c()

            CASP_6h <- c()
            CASP_24h <- c()
            CASP_72h <- c()

            OHG_6h <- c()
            OHG_24h <- c()
            OHG_72h <- c()

            for (x in slice_names_){
                if (grepl('DAPI', x)){
                    dapi_6h <- c(dapi_6h, x)
                }
                if (grepl('DAPI', x) && grepl('24H', x)){
                    dapi_24h <- c(dapi_24h, x)
                }
                if (grepl('DAPI', x) && grepl('72H', x)){
                    dapi_72h <- c(dapi_72h, x)
                }

                if (grepl('H2AX', x) && grepl('6H', x)){
                    H2AX_6h <- c(H2AX_6h, x)
                }
                if (grepl('H2AX', x) && grepl('24H', x)){
                    H2AX_24h <- c(H2AX_24h, x)
                }
                if (grepl('H2AX', x) && grepl('72H', x)){
                    H2AX_72h <- c(H2AX_72h, x)
                }
                if (grepl('CTG', x) && grepl('6H', x)){
                    CTG_6h <- c(CTG_6h, x)
                }
                if (grepl('CTG', x) && grepl('24H', x)){
                    CTG_24h <- c(CTG_24h, x)
                }
                if (grepl('CTG', x) && grepl('72H', x)){
                    CTG_72h <- c(CTG_72h, x)
                }
                if (grepl('CASP', x) && grepl('6H', x)){
                    CASP_6h <- c(CASP_6h, x)
                }
                if (grepl('CASP', x) && grepl('24H', x)){
                    CASP_24h <- c(CASP_24h, x)
                }
                if (grepl('CASP', x) && grepl('72H', x)){
                    CASP_72h <- c(CASP_72h, x)
                }
                if (grepl('OHG-1', x) && grepl('6H', x)){
                    OHG_6h <- c(OHG_6h, x)
                }
                if (grepl('OHG-1', x) && grepl('24H', x)){
                    OHG_24h <- c(OHG_24h, x)
                }
                if (grepl('OHG-1', x) && grepl('72H', x)){
                    OHG_72h <- c(OHG_72h, x)
                }
            }

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

            return (as.data.frame(sort(results), id.name = "material", score.name = "toxpi_score", rank.name = "rnk"))
        }
    ''')

    result = second_part_tox5(df, slice_names_)

    with ro.default_converter + pandas2ri.converter:
        pd_from_r_df = ro.conversion.get_conversion().rpy2py(result)

    return pd_from_r_df
