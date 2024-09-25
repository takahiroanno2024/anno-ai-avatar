import click
from sqlalchemy import text

from src.cli.databases.utils import engine
from src.config import settings
from src.logger import setup_logger

setup_logger()


@click.command()
def main() -> None:
    """Drop database."""
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # This will drop existing connections
        conn.execute(
            text(
                """SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = :db_name
                        AND pid <> pg_backend_pid()"""
            ).bindparams(db_name=settings.PG_DATABASE),
        )

        conn.execute(text(f"DROP DATABASE IF EXISTS {settings.PG_DATABASE}"))

        click.echo(f"[{settings.PG_DATABASE}]: database dropped")


if __name__ == "__main__":
    main()
