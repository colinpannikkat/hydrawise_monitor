from src.helpers import get_env_variables
from src.monitor import Monitor
import logging


def get_df():

    m = Monitor()
    cid, usr, pwd = get_env_variables()

    m.authenticate(usr, pwd)
    df = m.get_flow_data_in_time_range(cid)
    df = m.find_outliers(df)

    m.save_data(df, "data.csv")

    return df


logging.info("Fetching irrigation data.")
df = get_df()
