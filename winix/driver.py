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
            "cognitoClientSecretKey": auth.COGNITO_CLIENT_SECRET_KEY,
            "accessToken": self.access_token,
            "uuid": self.get_uuid(),
            "osVersion": "26",  # oreo
            "mobileLang": "en",
        }

        resp = requests.post(
            "https://us.mobile.winix-iot.com/checkAccessToken", json=payload
        )

        if resp.status_code != 200:
            raise Exception(
                f"Error while performing RPC checkAccessToken ({resp.status_code}): {resp.text}"
            )

    def get_device_info_list(self):
        resp = requests.post(
            "https://us.mobile.winix-iot.com/getDeviceInfoList",
            json={"accessToken": self.access_token, "uuid": self.get_uuid(),},
        )

        if resp.status_code != 200:
            raise Exception(
                f"Error while performing RPC checkAccessToken ({resp.status_code}): {resp.text}"
            )

        return [
            WinixDeviceStub(
                id=d["deviceId"],
                mac=d["mac"],
                alias=d["deviceAlias"],
                location_code=d["deviceLocCode"],
                filter_replace_date=d["filterReplaceDate"],
            )
            for d in resp.json()["deviceInfoList"]
        ]

    def register_user(self, email: str):
        """Register the logged-in android login/android user uuid with the backend"""
        # Call after getting a cognito token but before check_access_token
        # necessary for the winix backend to recognize the Android "uuid" we send
        # in most API requests
        from winix import auth

        resp = requests.post(
            "https://us.mobile.winix-iot.com/registerUser",
            json={
                "cognitoClientSecretKey": auth.COGNITO_CLIENT_SECRET_KEY,
                "accessToken": self.access_token,
                "uuid": self.get_uuid(),
                "email": email,
                "osType": "android",
                "osVersion": "29",
                "mobileLang": "en",
            },
        )

        if resp.status_code != 200:
            raise Exception(
                f"Error while performing RPC registerUser ({resp.status_code}): {resp.text}"
            )

    def get_uuid(self) -> str:
        # We construct our fake secure Android ID as
        # CRC32("github.com/hfern/winixctl" + userid) + CRC32("HGF" + userid)
        # where userid is the formatted uuid string from cognito

        if self._uuid is None:
            from jose import jwt

            userid_b = jwt.get_unverified_claims(self.access_token)["sub"].encode()
            p1 = crc32(b"github.com/hfern/winixctl" + userid_b)
            p2 = crc32(b"HGF" + userid_b)
            self._uuid = f"{p1:08x}{p2:08x}"

        return self._uuid


class WinixDevice:
    URL = "https://us.api.winix-iot.com/common/control/devices/{deviceid}/A211/{attribute}:{value}"

    K_POWER = "A02"
    V_POWER_STATES = {
        "off": "0",
        "on": "1",
    }

    K_MODE = "A03"
    V_MODE_STATES = {"auto": "01", "manual": "02"}

    K_AIRFLOW = "A04"
    V_AIRFLOW_STATES = {
        "low": "01",
        "medium": "02",
        "high": "03",
        "turbo": "05",
        "sleep": "06",
    }

    K_PLASMAWAVE = "A07"
    V_PLASMAWAVE_STATES = {
        "off": "0",
        "on": "1",
    }

    K_PLASMA = "A07"
    V_PLASMA_STATES = {
        "off": "0",
        "on": "1",
    }

    def __init__(self, id):
        self.id = id

    def off(self):
        self._rpc_attr(self.K_POWER, self.V_POWER_STATES["off"])

    def on(self):
        self._rpc_attr(self.K_POWER, self.V_POWER_STATES["on"])

    def auto(self):
        self._rpc_attr(self.K_MODE, self.V_MODE_STATES["auto"])

    def manual(self):
        self._rpc_attr(self.K_MODE, self.V_MODE_STATES["manual"])

    def plasmawave_off(self):
        self._rpc_attr(self.K_PLASMAWAVE, self.V_PLASMAWAVE_STATES["off"])

    def plasmawave_on(self):
        self._rpc_attr(self.K_PLASMAWAVE, self.V_PLASMAWAVE_STATES["on"])

    def low(self):
        self._rpc_attr(self.K_AIRFLOW, self.V_AIRFLOW_STATES["low"])

    def medium(self):
        self._rpc_attr(self.K_AIRFLOW, self.V_AIRFLOW_STATES["medium"])

    def high(self):
        self._rpc_attr(self.K_AIRFLOW, self.V_AIRFLOW_STATES["high"])

    def turbo(self):
        self._rpc_attr(self.K_AIRFLOW, self.V_AIRFLOW_STATES["turbo"])

    def sleep(self):
        self._rpc_attr(self.K_AIRFLOW, self.V_AIRFLOW_STATES["sleep"])

    def plasma_off(self):
        self._rpc_attr(self.K_PLASMA, self.V_PLASMA_STATES["off"])

    def plasma_on(self):
        self._rpc_attr(self.K_PLASMA, self.V_PLASMA_STATES["on"])

    def _rpc_attr(self, attr: str, value: str):
        requests.get(self.URL.format(deviceid=self.id, attribute=attr, value=value))
