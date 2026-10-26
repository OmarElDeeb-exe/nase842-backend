import json
import os
import typing as typ
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session, Connection


@lru_cache(maxsize=1)
def _get_engine():
    secret_arn = os.getenv("DB_SECRET_ARN")

    if secret_arn:
        # AWS: retrieve credentials from Secrets Manager
        import boto3

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response["SecretString"])

        username = secret["username"]
        password = secret["password"]
        host = os.getenv("POSTGRES_HOST") or secret["host"]

    else:
        # Local Docker: use existing environment variables
        username = os.environ["POSTGRES_USER"]
        password = os.environ["POSTGRES_PASSWORD"]
        host = os.environ["POSTGRES_HOST"]

    url = URL.create(
        "postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=5432,
        database=os.getenv("POSTGRES_DB", "realworlddb"),
    )

    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


def _create_db_connection() -> typ.Tuple[Session, Connection]:
    session = sessionmaker(bind=_get_engine())()
    conn = session.connection()
    return session, conn


@contextmanager
def get_db_connection():
    session, conn = _create_db_connection()

    try:
        yield conn
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
