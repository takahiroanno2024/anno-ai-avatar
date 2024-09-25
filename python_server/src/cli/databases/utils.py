from pydantic import PostgresDsn
from sqlalchemy import create_engine

from src.config import settings
from src.logger import setup_logger

setup_logger()

DEFAULT_DATABASE_URI = PostgresDsn.build(
    scheme="postgresql+psycopg",
    host=settings.PG_HOST,
    port=settings.PG_PORT,
    username=settings.PG_USER,
    password=settings.PG_PASSWORD,
    path="",
)

engine = create_engine(str(DEFAULT_DATABASE_URI))
