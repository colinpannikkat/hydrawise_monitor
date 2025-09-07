from .auth import Auth
from .const import (
    API_URL,
    GET_FLOW_DATA_QUERY
)
from datetime import (
    datetime,
    timezone,
)
from .helpers import (
    get_end_of_current_month_in_epoch_seconds,
    get_start_of_year_in_epoch_seconds
)
import requests
import pandas as pd
from pathlib import Path
import os
from typing import Any


class Monitor:

    def __init__(self):
        self.auth = None
        self.std_threshold = 2
        self.mad_threshold = 10
        self.save_path = os.path.expanduser("~/Documents/hydrawise_monitor")

    def authenticate(self, username: str, password: str):
        self.auth = Auth(username, password)

    @staticmethod
    def _generate_query_variables(controller_id, start_time: int, end_time: int) -> dict:
        v = {
            "controllerId": controller_id,
            "option": 3,
            "startTime": start_time,
            "endTime": end_time,
            "type": "FLOW_METER_MEASUREMENT_TYPE"
        }
        return v

    @staticmethod
    def _zone_num_from_name(zone_name: str):
        zone_name_num = zone_name.split("# ")[1]
        num_idx = zone_name_num.find(" ", 0, len(zone_name_num))
        zone_num, zone_name = int(zone_name_num[:num_idx]), zone_name_num[num_idx+1:].strip()
        return (zone_num, zone_name) if zone_num != "" else (0, zone_name)

    @staticmethod
    def _parse_flow_data_response(response: dict) -> tuple[pd.DataFrame, dict[str, int]]:
        results = response["data"]["controller"]["reporting"]["chartType"]["results"]
        zones = response["data"]['controller']["zones"]

        def build_zone_id_map(zones: dict[str, Any]) -> dict[str, int]:
            zone_map = {}

            for zone in zones:
                _, name = Monitor._zone_num_from_name(zone['name'])
                zone_map[name] = int(zone['id'])

            return zone_map

        zone_id_map = build_zone_id_map(zones)

        records = []

        def get_runtime_from_note(note: str) -> int:
            if 'minutes' in note:
                return int(note.split("Run time: ")[1].split(" minutes")[0])
            elif 'minute' in note:
                return int(note.split("Run time: ")[1].split(" minute")[0])
            elif 'hours' in note:
                return int(note.split("Run time: ")[1].split(" hours")[0]) * 60
            elif 'hour' in note:
                return int(note.split("Run time: ")[1].split(" hour")[0]) * 60
            elif 'seconds' in note:
                return int(note.split("Run time: ")[1].split(" seconds")[0]) / 60
            elif 'second' in note:
                return int(note.split("Run time: ")[1].split(" second")[0]) / 60
            else:
                raise (Exception(f"Cannot parse note: {note}"))

            return 0

        for zone_data in results:
            zone_name = zone_data["name"]
            zone_num, zone_name = Monitor._zone_num_from_name(zone_name)
            zone_id = zone_id_map[zone_name]
            for entry in zone_data["data"]:
                runtime = get_runtime_from_note(entry['note'])
                records.append({
                    "zone_id": zone_id,
                    "zone_num": zone_num,
                    "zone": zone_name,
                    "datetime": datetime.fromtimestamp(
                        entry["x"] / 1000,
                        tz=timezone.utc
                    ),
                    "gpm": entry["y"] / runtime,
                    "gallons": entry["y"],
                    "runtime": runtime,
                    "note": entry.get("note", "")
                })

        flow_data = pd.DataFrame(records)
        flow_data = flow_data.sort_values(by="datetime").reset_index(drop=True)

        return flow_data, zone_id_map

    def get_flow_data_in_time_range(
        self,
        controller_id,
        start_day: datetime = None,
        end_day: datetime = None
    ) -> pd.DataFrame:

        assert self.auth is not None

        if start_day is None:
            start_day = get_start_of_year_in_epoch_seconds()

        if end_day is None:
            end_day = get_end_of_current_month_in_epoch_seconds()

        variables = self._generate_query_variables(
            controller_id,
            start_day,
            end_day
        )

        payload = {
            "query": GET_FLOW_DATA_QUERY,
            "variables": variables
        }

        headers = {
            "Authorization": f"Bearer {self.auth.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload
        )

        flow_data, zone_id_map = self._parse_flow_data_response(response.json())
        self.zone_id_map = zone_id_map

        return flow_data

    def find_outliers(self, data: pd.DataFrame) -> pd.DataFrame:

        mean = data.groupby('zone_id')['gpm'].mean()
        median = data.groupby('zone_id')['gpm'].median()
        stddev = data.groupby('zone_id')['gpm'].std()

        data['std_z-score'] = (data['gpm'] - data['zone_id'].map(mean)) / data['zone_id'].map(stddev)
        data['outlier_std'] = data['std_z-score'] > self.std_threshold

        mad = data.groupby('zone_id')['gpm'].apply(lambda x: (x - x.median()).abs().median())

        def mad_zscore(row):
            zone_id = row['zone_id']
            median_val = median.loc[zone_id]
            mad_val = mad.loc[zone_id]
            if mad_val == 0:  # Avoid divide-by-zero
                return 0
            return (row['gpm'] - median_val) / mad_val

        # Apply MAD z-score and flag outliers
        data['mad_z-score'] = data.apply(mad_zscore, axis=1)
        data['outlier_mad'] = data['mad_z-score'] > self.mad_threshold
        return data

    def _backup_csv(self, filename: str):
        save_file = Path(os.path.join(self.save_path, filename))
        backup_dir = Path(self.save_path) / "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{save_file.stem}_{timestamp}{save_file.suffix}"
        save_file.replace(backup_file)

    def save_data(self, data: pd.DataFrame, filename: str, ret_df: bool = True) -> None | pd.DataFrame:
        save_file = Path(os.path.join(self.save_path, filename))

        if save_file.exists():
            old_data = pd.read_csv(
                save_file,
                dtype={
                    "zone_id": "Int64",
                    "zone_num": "Int64",
                    "zone": "string",
                    "gpm": "float",
                    "gallons": "float",
                    "runtime": "float",
                    "note": "string",
                    "std_z-score": "float",
                    "outlier_std": "boolean",
                    "mad_z-score": "float",
                    "outlier_mad": "boolean"
                },
                parse_dates=["datetime"]
            )
            self._backup_csv(filename)
            data = pd.concat(
                [old_data, data],
                ignore_index=True
                ).drop_duplicates(
                    ['zone_id', 'zone_num', 'datetime']
                )
            data.to_csv(save_file, index=False)
        else:
            os.makedirs(self.save_path, exist_ok=True)
            data.to_csv(save_file, index=False)

        if ret_df:
            return data
