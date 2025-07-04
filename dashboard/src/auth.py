import requests
from .const import (
    ACCESS_TOKEN_URL,
    CLIENT_ID,
    CLIENT_SECRET
)
from datetime import datetime, timedelta


class Auth():

    def __init__(self, username: str, password: str):
        self._get_bearer_token(username, password)

    def _get_bearer_token(self, username: str, password: str) -> str:
        response = requests.post(
            ACCESS_TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "username": username,
                "password": password,
                "scope": "all"
            }
        )
        self.access_token = response.json()['access_token']
        expires_in = response.json()['expires_in']

        hours = expires_in // 3600
        minutes = (expires_in % 3600) // 60
        seconds = expires_in % 60
        self.access_token_expiration = datetime.now() \
            + timedelta(hours=hours, minutes=minutes, seconds=seconds)

        self.refresh_token = response.json()['refresh_token']
