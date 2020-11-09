from dataclasses import dataclass
import boto3

import boto3
from botocore import UNSIGNED
from botocore.client import Config

# Pulled from Winix Home v1.0.8 APK
COGNITO_APP_CLIENT_ID = "14og512b9u20b8vrdm55d8empi"
COGNITO_CLIENT_SECRET_KEY = "k554d4pvgf2n0chbhgtmbe4q0ul4a9flp3pcl6a47ch6rripvvr"
COGNITO_USER_POOL_ID = "us-east-1_Ofd50EosD"
COGNITO_REGION = "us-east-1"


@dataclass
class WinixAuthResponse:
    user_id: str
    access_token: str
    refresh_token: str
    id_token: str


def login(username: str, password: str, **kwargs):
    """Generate fresh credentials"""
    from warrant_lite import WarrantLite
    from jose import jwt

    wl = WarrantLite(
        username=username,
        password=password,
        pool_id=kwargs.get("pool_id", COGNITO_USER_POOL_ID),
        client_id=kwargs.get("client_id", COGNITO_APP_CLIENT_ID),
        client_secret=kwargs.get("client_secret", COGNITO_CLIENT_SECRET_KEY),
        client=_boto_client(kwargs.get("pool_region")),
    )

    resp = wl.authenticate_user()
    return WinixAuthResponse(
        user_id=jwt.get_unverified_claims(resp["AuthenticationResult"]["AccessToken"])[
            "sub"
        ],
        access_token=resp["AuthenticationResult"]["AccessToken"],
        refresh_token=resp["AuthenticationResult"]["RefreshToken"],
        id_token=resp["AuthenticationResult"]["IdToken"],
    )


def refresh(user_id: str, refresh_token: str, **kwargs) -> WinixAuthResponse:
    """Refresh """
    from warrant_lite import WarrantLite

    client_id = kwargs.get("client_id", COGNITO_APP_CLIENT_ID)

    auth_params = {
        "REFRESH_TOKEN": refresh_token,
        "SECRET_HASH": WarrantLite.get_secret_hash(
            username=user_id,
            client_id=client_id,
            client_secret=kwargs.get("client_secret", COGNITO_CLIENT_SECRET_KEY),
        ),
    }

    resp = _boto_client(kwargs.get("pool_region")).initiate_auth(
        ClientId=client_id,
        AuthFlow="REFRESH_TOKEN",
        AuthParameters=auth_params,
    )

    return WinixAuthResponse(
        user_id=user_id,
        access_token=resp["AuthenticationResult"]["AccessToken"],
        refresh_token=refresh_token,
        id_token=resp["AuthenticationResult"]["IdToken"],
    )


def _boto_client(region):
    """Get an uncredentialed boto"""
    return boto3.client(
        "cognito-idp",
        config=Config(signature_version=UNSIGNED),
        region_name=region or COGNITO_REGION,
    )
