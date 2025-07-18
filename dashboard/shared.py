from src.helpers import get_env_variables
from src.monitor import Monitor
import logging


m = Monitor()
cid, usr, pwd = get_env_variables()


def get_df():

    if not m.auth:
        m.authenticate(usr, pwd)

    df = m.get_flow_data_in_time_range(cid)
    df = m.find_outliers(df)

    return m.save_data(df, "data.csv", ret_df=True)


logging.info("Fetching irrigation data.")
df = get_df()
