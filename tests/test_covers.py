"""Tests for cover and thumbnail generation."""

import os
from pathlib import Path

import fitz
import pytest

from zotlib.covers import generate_thumbnails, is_current, render_first_page


def set_mtime(path: Path, mtime: float) -> None:
    os.utime(path, (mtime, mtime))


@pytest.fixture
def pdf_path(tmp_path: Path) -> Path:
    path = tmp_path / "smith2023study.pdf"
    doc = fitz.open()
    page = doc.new_page(width=200, height=300)
    page.insert_text((20, 40), "A Study")
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def covers_dir(tmp_path: Path, pdf_path: Path) -> Path:
    path = tmp_path / "fullsize"
    path.mkdir()
    render_first_page(pdf_path, path / "smith2023study-cover.png", dpi=72)
    return path


def test_is_current_missing_output(tmp_path: Path, pdf_path: Path):
    assert not is_current(tmp_path / "missing.png", pdf_path)


def test_is_current_newer_output(covers_dir: Path, pdf_path: Path):
    cover = covers_dir / "smith2023study-cover.png"
    set_mtime(pdf_path, 1_000)
    set_mtime(cover, 2_000)
    assert is_current(cover, pdf_path)


def test_is_current_older_output(covers_dir: Path, pdf_path: Path):
    cover = covers_dir / "smith2023study-cover.png"
    set_mtime(pdf_path, 2_000)
    set_mtime(cover, 1_000)
    assert not is_current(cover, pdf_path)


def test_thumbnails_skip_current(tmp_path: Path, covers_dir: Path):
    thumbs_dir = tmp_path / "thumbnails"
    assert generate_thumbnails(covers_dir, thumbs_dir, width=50) == 1
    thumb = thumbs_dir / "smith2023study-thumb.png"
    set_mtime(covers_dir / "smith2023study-cover.png", 1_000)
    set_mtime(thumb, 2_000)

    assert generate_thumbnails(covers_dir, thumbs_dir, width=50) == 0
    assert thumb.stat().st_mtime == 2_000


def test_thumbnails_rewrite_stale(tmp_path: Path, covers_dir: Path):
    thumbs_dir = tmp_path / "thumbnails"
    generate_thumbnails(covers_dir, thumbs_dir, width=50)
    set_mtime(thumbs_dir / "smith2023study-thumb.png", 1_000)
    set_mtime(covers_dir / "smith2023study-cover.png", 2_000)

    assert generate_thumbnails(covers_dir, thumbs_dir, width=50) == 1


def test_thumbnails_force(tmp_path: Path, covers_dir: Path):
    thumbs_dir = tmp_path / "thumbnails"
    generate_thumbnails(covers_dir, thumbs_dir, width=50)

    assert generate_thumbnails(covers_dir, thumbs_dir, width=50, force=True) == 1
