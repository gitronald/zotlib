"""Tests for backup module."""

import tarfile
from pathlib import Path

import pytest
from rich.console import Console

from zotlib.backup import create_backup, default_backup_path, get_directory_stats


@pytest.fixture
def fake_zotero_dir(tmp_path):
    """Create a fake Zotero directory structure."""
    zotero = tmp_path / "Zotero"
    zotero.mkdir()
    (zotero / "zotero.sqlite").write_bytes(b"fake-database-content")
    storage = zotero / "storage" / "ABCD1234"
    storage.mkdir(parents=True)
    (storage / "paper.pdf").write_bytes(b"fake-pdf-content")
    return zotero


@pytest.fixture
def quiet_console():
    return Console(quiet=True)


def test_get_directory_stats(fake_zotero_dir):
    file_count, total_bytes = get_directory_stats(fake_zotero_dir)
    assert file_count == 2
    assert total_bytes == len(b"fake-database-content") + len(b"fake-pdf-content")


def test_get_directory_stats_empty(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    file_count, total_bytes = get_directory_stats(empty)
    assert file_count == 0
    assert total_bytes == 0


def test_create_backup(fake_zotero_dir, tmp_path, quiet_console):
    output = tmp_path / "test-backup.tar.bz2"
    result = create_backup(fake_zotero_dir, output, quiet_console)

    assert result == output
    assert output.exists()

    with tarfile.open(output, "r:bz2") as tar:
        names = tar.getnames()
        assert names[0] == "Zotero"
        assert "Zotero/zotero.sqlite" in names
        assert "Zotero/storage/ABCD1234/paper.pdf" in names


def test_create_backup_already_exists(fake_zotero_dir, tmp_path, quiet_console):
    output = tmp_path / "existing.tar.bz2"
    output.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        create_backup(fake_zotero_dir, output, quiet_console)


def test_create_backup_missing_source(tmp_path, quiet_console):
    with pytest.raises(FileNotFoundError):
        create_backup(tmp_path / "nonexistent", tmp_path / "out.tar.bz2", quiet_console)


def test_default_backup_path():
    path = default_backup_path()
    assert path.parent == Path("data") / "backups"
    assert path.name.startswith("zotero-")
    assert path.name.endswith(".tar.bz2")
