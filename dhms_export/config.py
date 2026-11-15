"""Loads settings from environment variables / .env file.

The DB password comes from AWS Secrets Manager when DB_SECRET_NAME is set,
otherwise from DB_PASSWORD.
"""

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_schema: str
    tables: list[str]
    output_dir: str
    output_format: str
    aws_region: str


def _get_secret_password(secret_name: str, region: str) -> str:
    import boto3  # only needed when using Secrets Manager

    client = boto3.client("secretsmanager", region_name=region)
    value = client.get_secret_value(SecretId=secret_name)["SecretString"]
    # RDS-managed secrets are JSON: {"username": "...", "password": "..."}
    try:
        return json.loads(value)["password"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return value  # plain-text secret


def load_config() -> Config:
    tables = [t.strip() for t in os.getenv("DB_TABLES", "").split(",") if t.strip()]
    if not tables:
        raise ValueError("DB_TABLES is empty. Set it in your .env file.")

    output_format = os.getenv("OUTPUT_FORMAT", "csv").strip().lower()
    if output_format not in ("csv", "parquet"):
        raise ValueError("OUTPUT_FORMAT must be 'csv' or 'parquet'.")

    region = os.getenv("AWS_REGION", "ap-south-1")
    secret_name = os.getenv("DB_SECRET_NAME", "").strip()
    password = (
        _get_secret_password(secret_name, region)
        if secret_name
        else os.getenv("DB_PASSWORD", "")
    )

    return Config(
        db_host=os.environ["DB_HOST"],
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.environ["DB_NAME"],
        db_user=os.environ["DB_USER"],
        db_password=password,
        db_schema=os.getenv("DB_SCHEMA", "public"),
        tables=tables,
        output_dir=os.getenv("OUTPUT_DIR", "DHMS").rstrip("/"),
        output_format=output_format,
        aws_region=region,
    )
