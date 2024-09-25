import click
from sqlalchemy import text

from src.cli.databases.utils import engine
from src.config import settings
from src.logger import setup_logger

setup_logger()


@click.command()
def main() -> None:
    """Create a new database."""
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        conn.execute(text(f"CREATE DATABASE {settings.PG_DATABASE}"))

        click.echo(f"[{settings.PG_DATABASE}]: database created")


if __name__ == "__main__":
    main()
