import dataclasses
from binascii import crc32
from typing import Optional

import requests


@dataclasses.dataclass
class WinixDeviceStub:
    id: str
    mac: str
    alias: str
    location_code: str
    filter_replace_date: str


class WinixAccount:
    def __init__(self, access_token: str):
        self._uuid: Optional[str] = None
        self.access_token = access_token

    def check_access_token(self):
        """Register the Cognito Token with the Winix backen (again)"""
        from winix import auth

        payload = {
            'cognitoClientSecretKey': auth.COGNITO_CLIENT_SECRET_KEY,
            'accessToken': self.access_token,
            'uuid': self.get_uuid(),
            'osVersion': '26',  # oreo
            'mobileLang': 'en',
        }

        resp = requests.post('https://us.mobile.winix-iot.com/checkAccessToken', json=payload)

        if resp.status_code != 200:
            raise Exception(f'Error while performing RPC checkAccessToken ({resp.status_code}): {resp.text}')

    def get_device_info_list(self):
        resp = requests.post('https://us.mobile.winix-iot.com/getDeviceInfoList', json={
            'accessToken': self.access_token,
            'uuid': self.get_uuid(),
        })

        if resp.status_code != 200:
            raise Exception(f'Error while performing RPC checkAccessToken ({resp.status_code}): {resp.text}')

        return [
            WinixDeviceStub(
                id=d['deviceId'],
                mac=d['mac'],
                alias=d['deviceAlias'],
                location_code=d['deviceLocCode'],
                filter_replace_date=d['filterReplaceDate'],
            )
            for d in resp.json()['deviceInfoList']
        ]

    def register_user(self, email: str):
        """Register the logged-in android login/android user uuid with the backend"""
        # Call after getting a cognito token but before check_access_token
        # necessary for the winix backend to recognize the Android "uuid" we send
        # in most API requests
        from winix import auth
        resp = requests.post('https://us.mobile.winix-iot.com/registerUser', json={
            'cognitoClientSecretKey': auth.COGNITO_CLIENT_SECRET_KEY,
            'accessToken': self.access_token,
            'uuid': self.get_uuid(),
            'email': email,
            'osType': 'android',
            'osVersion': '29',
            'mobileLang': 'en',
        })

        if resp.status_code != 200:
            raise Exception(f'Error while performing RPC registerUser ({resp.status_code}): {resp.text}')

    def get_uuid(self) -> str:
        # We construct our fake secure Android ID as
        # CRC32("github.com/hfern/winixctl" + userid) + CRC32("HGF" + userid)
        # where userid is the formatted uuid string from cognito

        if self._uuid is None:
            from jose import jwt
            userid_b = jwt.get_unverified_claims(self.access_token)['sub'].encode()
            p1 = crc32(b'github.com/hfern/winixctl' + userid_b)
            p2 = crc32(b'HGF' + userid_b)
            self._uuid = f'{p1:08x}{p2:08x}'

        return self._uuid


class WinixDevice:
    URL = 'https://us.api.winix-iot.com/common/control/devices/{deviceid}/A211/A04:{level}'

    def __init__(self, id):
        self.id = id

    def low(self):
        return self._set_airflow('01')

    def medium(self):
        return self._set_airflow('02')

    def high(self):
        return self._set_airflow('03')

    def turbo(self):
        return self._set_airflow('05')

    def _set_airflow(self, level: str):
        requests.get(self.URL.format(deviceid=self.id, level=level))
