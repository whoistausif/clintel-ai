from __future__ import annotations

from .config import settings


def execute(statement: str, params: tuple = ()) -> None:
    """Persist a parameterized query when a configured PostgreSQL database is available."""
    if not settings.database_url:
        return
    import psycopg
    with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
        connection.execute(statement, params)


def fetch_all(statement: str, params: tuple = ()) -> list[dict]:
    if not settings.database_url:
        return []
    import psycopg
    with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
        cursor = connection.execute(statement, params)
        columns = [item.name for item in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
