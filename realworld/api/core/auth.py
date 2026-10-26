import os
import jwt
import typing as typ

from flask import request
from functools import wraps, lru_cache
from datetime import datetime, timedelta, timezone


ISSUER = "realworld"
OVERRIDE_TOKEN_EXPIRATION = os.getenv(
    "OVERRIDE_TOKEN_EXPIRATION", "FALSE"
).upper()


@lru_cache(maxsize=1)
def _get_signing_key() -> str:
    secret_arn = os.getenv("JWT_SECRET_ARN")

    if secret_arn:
        import boto3

        key = boto3.client("secretsmanager").get_secret_value(
            SecretId=secret_arn
        )["SecretString"]
    else:
        key = os.getenv("SECRET_KEY")

    if not key or len(key) < 32:
        raise RuntimeError("A secure JWT signing key is required.")

    return key


def generate_jwt(user_id: str):
    now = datetime.now(tz=timezone.utc)

    expiration_minutes = (
        15 if OVERRIDE_TOKEN_EXPIRATION == "TRUE"
        else 1440
    )

    payload = {
        "iss": ISSUER,
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=expiration_minutes),
    }

    return jwt.encode(
        payload,
        _get_signing_key(),
        algorithm="HS256"
    )


def _decode_jwt(
    token: typ.Optional[str],
) -> typ.Tuple[bool, typ.Union[dict, str]]:

    if not token:
        return False, "No token provided."

    try:
        decoded = jwt.decode(
            token,
            _get_signing_key(),
            algorithms=["HS256"],
            issuer=ISSUER,
            options={"require": ["iss", "iat", "exp"]},
        )

        return True, decoded

    except jwt.InvalidTokenError as e:
        return False, str(e)


def _get_token_from_request() -> typ.Optional[str]:
    authorization = request.headers.get("Authorization", "")
    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "token":
        return None

    return parts[1]


def validate_token(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        encoded_token = _get_token_from_request()

        if not encoded_token:
            return {"error": "No token provided."}, 401

        is_valid, decoded = _decode_jwt(encoded_token)

        if not is_valid:
            return {"error": decoded}, 401

        return func(*args, **kwds)

    return wrapper


def get_user_id_from_token() -> typ.Optional[str]:
    is_valid, decoded = _decode_jwt(
        _get_token_from_request()
    )

    if is_valid:
        return decoded.get("user_id")

    return None
