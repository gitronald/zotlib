"""Database connection and query utilities for Zotero SQLite."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator

import pandas as pd


class ZoteroDatabase:
    """Read-only interface to Zotero SQLite database."""

    def __init__(self, database_path: Path | str):
        """Initialize database connection.

        Args:
            database_path: Path to zotero.sqlite file.

        Raises:
            FileNotFoundError: If database file doesn't exist.
        """
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Zotero database not found: {self.database_path}"
            )

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for read-only database connection."""
        # Use file URI with mode=ro for read-only access
        uri = f"file:{self.database_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            yield conn
        finally:
            conn.close()

    def get_table_names(self) -> list[str]:
        """Get all table names in the database."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in cursor.fetchall()]

    def get_column_names(self, table_name: str) -> list[str]:
        """Get column names for a table."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
            return [desc[0] for desc in cursor.description]

    def query(self, sql: str) -> pd.DataFrame:
        """Execute a query and return results as DataFrame.

        Args:
            sql: SQL query string.

        Returns:
            DataFrame with query results.
        """
        with self.connection() as conn:
            return pd.read_sql_query(sql, conn)
