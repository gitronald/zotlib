"""Tests for the covers module."""

from pathlib import Path

import pytest

from zotlib.covers import resolve_pdf_path, sanitize_filename


class TestResolvePdfPath:
    def test_storage_path(self):
        result = resolve_pdf_path(Path("/data/storage"), "ABC123", "storage:paper.pdf")
        assert result == Path("/data/storage/ABC123/paper.pdf")

    def test_attachments_path(self):
        result = resolve_pdf_path(
            Path("/data/storage"), "ABC123", "attachments:sub/paper.pdf", pdfs_dir=Path("/pdfs")
        )
        assert result == Path("/pdfs/sub/paper.pdf")

    def test_attachments_no_pdfs_dir_raises(self):
        with pytest.raises(ValueError, match="--pdfs-dir"):
            resolve_pdf_path(Path("/data/storage"), "ABC123", "attachments:sub/paper.pdf")

    def test_windows_absolute_path(self):
        result = resolve_pdf_path(Path("/data/storage"), "ABC123", "D:\\Dropbox\\lit\\paper.pdf")
        assert result == Path("/mnt/d/Dropbox/lit/paper.pdf")


class TestSanitizeFilename:
    def test_removes_special_chars(self):
        assert sanitize_filename('file<>:"/\\|?*name') == "filename"

    def test_strips_dots_and_spaces(self):
        assert sanitize_filename("  ..hello.. ") == "hello"

    def test_truncates_long_names(self):
        long_name = "a" * 250
        assert len(sanitize_filename(long_name)) == 200

    def test_empty_returns_untitled(self):
        assert sanitize_filename("") == "untitled"

    def test_only_special_chars_returns_untitled(self):
        assert sanitize_filename(':<>"/\\|?*') == "untitled"
