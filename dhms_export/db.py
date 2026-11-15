"""Database connection and table reading."""

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

from .config import Config


def get_engine(cfg: Config) -> Engine:
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=cfg.db_user,
        password=cfg.db_password,
        host=cfg.db_host,
        port=cfg.db_port,
        database=cfg.db_name,
    )
    return create_engine(url)


def read_table(engine: Engine, table: str, schema: str) -> pd.DataFrame:
    return pd.read_sql_table(table, engine, schema=schema)
