"""Tests for the config module."""

from pathlib import Path

import pytest

from zotlib.config import (
    _windows_to_wsl_path,
    get_database_path,
    get_pdfs_dir,
    load_config,
    write_config,
)


class TestWindowsToWslPath:
    def test_drive_d(self):
        assert _windows_to_wsl_path("D:\\Dropbox\\zotero-pdfs") == Path(
            "/mnt/d/Dropbox/zotero-pdfs"
        )

    def test_drive_c(self):
        assert _windows_to_wsl_path("C:\\Users\\rer\\docs") == Path("/mnt/c/Users/rer/docs")


class TestLoadConfig:
    def test_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert load_config() == {}

    def test_valid_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "zotlib.toml").write_text(
            '[zotlib]\ndatabase = "/path/to/db"\npdfs_dir = "/path/to/pdfs"\n'
        )
        config = load_config()
        assert config["database"] == "/path/to/db"
        assert config["pdfs_dir"] == "/path/to/pdfs"


class TestWriteConfig:
    def test_write_with_pdfs_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = write_config(Path("/path/to/db"), Path("/path/to/pdfs"))
        assert result.exists()
        content = result.read_text()
        assert 'database = "/path/to/db"' in content
        assert 'pdfs_dir = "/path/to/pdfs"' in content

    def test_write_without_pdfs_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = write_config(Path("/path/to/db"))
        content = result.read_text()
        assert "pdfs_dir" not in content


class TestGetDatabasePath:
    def test_explicit_path(self, tmp_path):
        db = tmp_path / "zotero.sqlite"
        db.touch()
        assert get_database_path(db) == db

    def test_explicit_path_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found at"):
            get_database_path(tmp_path / "missing.sqlite")

    def test_env_var(self, tmp_path, monkeypatch):
        db = tmp_path / "zotero.sqlite"
        db.touch()
        monkeypatch.setenv("ZOTERO_DATABASE", str(db))
        monkeypatch.chdir(tmp_path)
        assert get_database_path() == db

    def test_env_var_missing_raises(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZOTERO_DATABASE", str(tmp_path / "missing.sqlite"))
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError, match="ZOTERO_DATABASE"):
            get_database_path()

    def test_not_found_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("ZOTERO_DATABASE", raising=False)
        monkeypatch.setattr("zotlib.config.discover_zotero_database", lambda: None)
        with pytest.raises(FileNotFoundError, match="Could not find"):
            get_database_path()


class TestGetPdfsDir:
    def test_explicit_path(self, tmp_path):
        pdfs = tmp_path / "pdfs"
        pdfs.mkdir()
        assert get_pdfs_dir(pdfs) == pdfs

    def test_explicit_path_missing(self, tmp_path):
        assert get_pdfs_dir(tmp_path / "missing") is None

    def test_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert get_pdfs_dir() is None
