from dashboard.src.monitor import Monitor
from dashboard.src.helpers import get_env_variables


def main():
    m = Monitor()
    cid, usr, pwd = get_env_variables()

    m.authenticate(usr, pwd)
    dt = m.get_flow_data_in_time_range(cid)
    dt = m.find_outliers(dt)

    m.save_data(dt, "data.csv")


if __name__ == "__main__":
    main()
