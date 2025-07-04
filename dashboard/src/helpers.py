from datetime import (
    datetime,
    date,
    time,
    timezone,
    timedelta
)
from dateutil.relativedelta import relativedelta

import pandas as pd

from dotenv import load_dotenv
from getpass import getpass
import os


def convert_datetime_to_epoch_seconds(dt: datetime) -> int:
    return int(dt.timestamp())


def get_start_of_year_in_datetime() -> datetime:
    today = date.today()
    return datetime.combine(
        date(today.year, 1, 1),
        time.min,
        tzinfo=timezone.utc
    )


def get_start_of_year_in_epoch_seconds() -> int:
    return convert_datetime_to_epoch_seconds(get_start_of_year_in_datetime())


def get_end_of_current_month_in_datetime() -> datetime:
    today = date.today()
    first_day_this_month = today.replace(day=1)

    if first_day_this_month.month == 12:
        first_day_next_month = first_day_this_month.replace(
            year=first_day_this_month.year + 1,
            month=1
        )
    else:
        first_day_next_month = first_day_this_month.replace(
            month=first_day_this_month.month + 1
        )
    last_day_this_month = first_day_next_month - timedelta(days=1)

    return datetime.combine(last_day_this_month, time.max, tzinfo=timezone.utc)


def get_end_of_current_month_in_epoch_seconds() -> int:
    return convert_datetime_to_epoch_seconds(get_end_of_current_month_in_datetime())


def get_start_of_current_month_in_datetime() -> datetime:
    today = date.today()
    first_day_this_month = today.replace(day=1)
    return datetime.combine(first_day_this_month, time.min, tzinfo=timezone.utc)


def get_start_of_current_month_in_epoch_seconds() -> int:
    return convert_datetime_to_epoch_seconds(get_start_of_current_month_in_datetime())


def get_one_month_back_in_datetime() -> datetime:
    return datetime.now() - relativedelta(months=1)


def filter_dataframe_by_date(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    # Ensure start and end are datetime with UTC timezone
    start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end, time.max, tzinfo=timezone.utc)
    mask = (df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)
    return df[mask]


def get_env_variables():

    load_dotenv()

    cid = os.getenv("CONTROLLER_ID")
    usr = os.getenv("USERNAME")
    pwd = os.getenv("PASSWORD")

    if cid is None or usr is None or pwd is None:
        cid = input("Input controller ID: ")
        usr = input("Input username: ")
        pwd = getpass("Input password: ")

    return cid, usr, pwd
