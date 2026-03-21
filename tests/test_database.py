"""Tests for the database module."""

import sqlite3

import polars as pl
import pytest

from zotlib.database import ZoteroDatabase


@pytest.fixture
def mock_db(tmp_path):
    """Create a minimal SQLite database for testing."""
    db_path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (itemID INTEGER, key TEXT, title TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'ABC', 'Test Item')")
    conn.execute("INSERT INTO items VALUES (2, 'DEF', 'Another Item')")
    conn.commit()
    conn.close()
    return db_path


class TestZoteroDatabase:
    def test_init(self, mock_db):
        db = ZoteroDatabase(mock_db)
        assert db.database_path == mock_db

    def test_init_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ZoteroDatabase(tmp_path / "missing.sqlite")

    def test_get_table_names(self, mock_db):
        db = ZoteroDatabase(mock_db)
        tables = db.get_table_names()
        assert "items" in tables

    def test_get_column_names(self, mock_db):
        db = ZoteroDatabase(mock_db)
        cols = db.get_column_names("items")
        assert cols == ["itemID", "key", "title"]

    def test_query(self, mock_db):
        db = ZoteroDatabase(mock_db)
        result = db.query("SELECT * FROM items")
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2
        assert result["title"].to_list() == ["Test Item", "Another Item"]

    def test_query_with_params(self, mock_db):
        db = ZoteroDatabase(mock_db)
        result = db.query("SELECT * FROM items WHERE itemID = ?", [1])
        assert len(result) == 1
        assert result["key"][0] == "ABC"

    def test_query_with_multiple_params(self, mock_db):
        db = ZoteroDatabase(mock_db)
        result = db.query("SELECT * FROM items WHERE itemID IN (?, ?)", [1, 2])
        assert len(result) == 2
