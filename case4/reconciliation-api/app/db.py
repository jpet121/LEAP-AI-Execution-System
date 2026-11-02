"""Explicit migration entrypoint, invoked by operator before serving requests."""
from pathlib import Path
import psycopg

def migrate(dsn: str, migration: Path = Path('migrations/001_initial.sql')) -> None:
    with psycopg.connect(dsn) as connection:
        connection.execute(migration.read_text())
