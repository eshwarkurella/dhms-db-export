"""Builds the output paths and writes files, locally or to S3."""

import io
import os
from datetime import date

import pandas as pd

_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3

        _s3_client = boto3.client("s3")
    return _s3_client


def is_s3(path: str) -> bool:
    return path.startswith("s3://")


def _join(base: str, *parts: str) -> str:
    # S3 keys always use "/", local paths use the OS separator
    return "/".join([base, *parts]) if is_s3(base) else os.path.join(base, *parts)


def get_output_dirs(base_dir: str, run_date: date) -> tuple[str, str]:
    dated_dir = _join(
        base_dir,
        f"year={run_date.year}",
        f"month={run_date.month:02d}",
        f"day={run_date.day:02d}",
    )
    latest_dir = _join(base_dir, "Latest")
    if not is_s3(base_dir):
        os.makedirs(dated_dir, exist_ok=True)
        os.makedirs(latest_dir, exist_ok=True)
    return dated_dir, latest_dir


def to_bytes(df: pd.DataFrame, fmt: str) -> bytes:
    buf = io.BytesIO()
    if fmt == "parquet":
        df.to_parquet(buf, index=False)
    else:
        df.to_csv(buf, index=False)
    return buf.getvalue()


def write_bytes(data: bytes, folder: str, table: str, fmt: str) -> str:
    path = _join(folder, f"{table}.{fmt}")
    if is_s3(path):
        bucket, key = path[len("s3://"):].split("/", 1)
        _s3().put_object(Bucket=bucket, Key=key, Body=data)
    else:
        with open(path, "wb") as f:
            f.write(data)
    return path
