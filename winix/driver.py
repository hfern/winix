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
            json={
                "accessToken": self.access_token,
                "uuid": self.get_uuid(),
            },
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
    CTRL_URL = "https://us.api.winix-iot.com/common/control/devices/{deviceid}/A211/{attribute}:{value}"
    STATE_URL = "https://us.api.winix-iot.com/common/event/sttus/devices/{deviceid}"

    category_keys = {
        "power": "A02",
        "mode": "A03",
        "airflow": "A04",
        "aqi": "A05",
        "plasma": "A07",
        "filter_hour": "A21",
        "air_quality": "S07",
        "air_qvalue": "S08",
        "ambient_light": "S14",
    }

    state_keys = {
        "power": {"off": "0", "on": "1"},
        "mode": {"auto": "01", "manual": "02"},
        "airflow": {
            "low": "01",
            "medium": "02",
            "high": "03",
            "turbo": "05",
            "sleep": "06",
        },
        "plasma": {"off": "0", "on": "1"},
        "air_quality": {"good": "01", "fair": "02", "poor": "03"},
    }

    def __init__(self, id):
        self.id = id

    def off(self):
        self._rpc_attr(self.category_keys["power"], self.state_keys["power"]["off"])

    def on(self):
        self._rpc_attr(self.category_keys["power"], self.state_keys["power"]["on"])

    def auto(self):
        self._rpc_attr(self.category_keys["mode"], self.state_keys["mode"]["auto"])

    def manual(self):
        self._rpc_attr(self.category_keys["mode"], self.state_keys["mode"]["manual"])

    def plasmawave_off(self):
        self._rpc_attr(self.category_keys["plasma"], self.state_keys["plasma"]["off"])

    def plasmawave_on(self):
        self._rpc_attr(self.category_keys["plasma"], self.state_keys["plasma"]["on"])

    def low(self):
        self._rpc_attr(self.category_keys["airflow"], self.state_keys["airflow"]["low"])

    def medium(self):
        self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["medium"]
        )

    def high(self):
        self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["high"]
        )

    def turbo(self):
        self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["turbo"]
        )

    def sleep(self):
        self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["sleep"]
        )

    def _rpc_attr(self, attr: str, value: str):
        requests.get(
            self.CTRL_URL.format(deviceid=self.id, attribute=attr, value=value)
        )

    def get_state(self):
        r = requests.get(self.STATE_URL.format(deviceid=self.id))
        payload = r.json()["body"]["data"][0]["attributes"]

        output = dict()
        for (payload_key, attribute) in payload.items():
            for (category, local_key) in self.category_keys.items():
                if payload_key == local_key:
                    if category in self.state_keys.keys():
                        for (value_key, value) in self.state_keys[category].items():
                            if attribute == value:
                                output[category] = value_key
                    else:
                        output[category] = int(attribute)

        return output
