# import pandas as pd
# import rpy2
#
# from Orange.data import table_from_frame, table_to_frame
#
# from rpy2 import robjects
# from rpy2.robjects.packages import importr, data
# from rpy2.robjects import pandas2ri
# import rpy2.robjects as ro
# import warnings

# from tox_orange_demo.toxpi_data_prep import *
# from tox_orange_demo.toxpi_r import *
#
# warnings.filterwarnings('ignore')
#
# base = importr("base")
# utils = importr("utils")
# utils.chooseCRANmirror(ind=1)
# toxpiR = importr("toxpiR")
#
# df_test = pd.read_csv("tox_preprocessing.csv")
# print(df_test)
#
# df, slice_names_ = calculate_first_tox5(df_test, 'A549')
# df2 = calculate_second_tox5_by_endpoint_time(df, slice_names_)
# print(df2)




