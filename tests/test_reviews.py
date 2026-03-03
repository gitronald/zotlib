"""Tests for the reviews module."""

import json
from pathlib import Path

import fitz
import pandas as pd
import pytest

from zotlib.reviews import (
    ANNOTATION_TYPES,
    COLOR_LABELS,
    bake_annotations,
    convert_zotero_rect,
    format_annotations_markdown,
    get_color_label,
    hex_to_rgb,
    make_review_dirname,
)


# --- Fixtures ---


@pytest.fixture
def sample_item_row():
    """Sample item metadata for markdown generation."""
    return pd.Series({
        "itemID": 42,
        "title": "Social Media Effects on Youth",
        "authors": "John Smith, Jane Doe",
        "year": 2024,
        "publicationTitle": "Journal of Communication",
        "DOI": "10.1234/joc.2024.001",
        "url": "https://example.com/paper",
        "dateAdded": "2024-06-15 10:30:00",
        "tags": "review, social media, youth",
    })


@pytest.fixture
def sample_annotations():
    """Sample annotation rows for testing."""
    return pd.DataFrame([
        {
            "itemID": 100,
            "parentItemID": 50,
            "type": 1,  # highlight
            "text": "This is a highlighted passage",
            "comment": "Important finding",
            "color": "#ffd400",
            "pageLabel": "3",
            "sortIndex": "00003|000100|00200",
            "position": json.dumps({"pageIndex": 2, "rects": [[100, 200, 400, 220]]}),
            "paperItemID": 42,
        },
        {
            "itemID": 101,
            "parentItemID": 50,
            "type": 2,  # note
            "text": "",
            "comment": "Remember to follow up on this method",
            "color": "#ffd400",
            "pageLabel": "3",
            "sortIndex": "00003|000200|00300",
            "position": json.dumps({"pageIndex": 2, "rects": [[100, 300, 400, 320]]}),
            "paperItemID": 42,
        },
        {
            "itemID": 102,
            "parentItemID": 50,
            "type": 1,  # highlight
            "text": "Another key finding on page five",
            "comment": "",
            "color": "#ff6666",
            "pageLabel": "5",
            "sortIndex": "00005|000100|00100",
            "position": json.dumps({"pageIndex": 4, "rects": [[50, 400, 500, 420]]}),
            "paperItemID": 42,
        },
    ])


@pytest.fixture
def simple_pdf(tmp_path):
    """Create a minimal multi-page PDF for testing."""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    for _ in range(6):
        doc.new_page(width=612, height=792)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# --- Unit tests ---


class TestConvertZoteroRect:
    def test_basic_conversion(self):
        """Y coordinates should be flipped from bottom-left to top-left origin."""
        rect = convert_zotero_rect([100, 200, 300, 220], 792)
        assert rect.x0 == 100
        assert rect.x1 == 300
        assert rect.y0 == pytest.approx(572)
        assert rect.y1 == pytest.approx(592)

    def test_full_page_width(self):
        rect = convert_zotero_rect([0, 0, 612, 792], 792)
        assert rect.x0 == 0
        assert rect.x1 == 612
        assert rect.y0 == pytest.approx(0)
        assert rect.y1 == pytest.approx(792)

    def test_small_rect_near_top(self):
        """A rect near the top in PDF coords should be near the top in PyMuPDF."""
        rect = convert_zotero_rect([100, 770, 200, 790], 792)
        assert rect.y0 == pytest.approx(2)
        assert rect.y1 == pytest.approx(22)


class TestColorHelpers:
    def test_known_colors(self):
        assert get_color_label("#ffd400") == "yellow"
        assert get_color_label("#ff6666") == "red"
        assert get_color_label("#5fb236") == "green"
        assert get_color_label("#2ea8e5") == "blue"
        assert get_color_label("#a28ae5") == "purple"
        assert get_color_label("#e56eee") == "magenta"
        assert get_color_label("#f19837") == "orange"

    def test_case_insensitive(self):
        assert get_color_label("#FFD400") == "yellow"

    def test_empty_color(self):
        assert get_color_label("") == ""

    def test_unknown_color(self):
        assert get_color_label("#123456") == "#123456"

    def test_hex_to_rgb(self):
        assert hex_to_rgb("#ff0000") == pytest.approx((1.0, 0.0, 0.0))
        assert hex_to_rgb("#00ff00") == pytest.approx((0.0, 1.0, 0.0))
        assert hex_to_rgb("#ffffff") == pytest.approx((1.0, 1.0, 1.0))


class TestAnnotationTypes:
    def test_type_mapping(self):
        assert ANNOTATION_TYPES[1] == "highlight"
        assert ANNOTATION_TYPES[2] == "note"
        assert ANNOTATION_TYPES[3] == "image"
        assert ANNOTATION_TYPES[5] == "underline"


class TestMakeReviewDirname:
    def test_basic(self):
        row = pd.Series({"authors": "John Smith, Jane Doe", "year": 2024, "title": "A Study"})
        result = make_review_dirname(row)
        assert result == "smith-2024-a-study"

    def test_no_author(self):
        row = pd.Series({"authors": "", "year": 2024, "title": "Some Title"})
        result = make_review_dirname(row)
        assert result.startswith("unknown-2024-")

    def test_no_year(self):
        row = pd.Series({"authors": "John Smith", "year": float("nan"), "title": "Title"})
        result = make_review_dirname(row)
        assert "nd" in result

    def test_long_title_truncated(self):
        row = pd.Series({
            "authors": "Smith",
            "year": 2024,
            "title": "A" * 100,
        })
        result = make_review_dirname(row)
        # 60 char title limit + author + year
        assert len(result) < 80


class TestFormatAnnotationsMarkdown:
    def test_yaml_frontmatter(self, sample_item_row, sample_annotations):
        md = format_annotations_markdown(sample_item_row, sample_annotations)
        assert md.startswith("---\n")
        assert 'title: "Social Media Effects on Youth"' in md
        assert 'authors: "John Smith, Jane Doe"' in md
        assert "year: 2024" in md
        assert 'publication: "Journal of Communication"' in md
        assert 'doi: "10.1234/joc.2024.001"' in md
        assert 'date_added: "2024-06-15 10:30:00"' in md
        assert "annotation_count: 3" in md

    def test_page_grouping(self, sample_item_row, sample_annotations):
        md = format_annotations_markdown(sample_item_row, sample_annotations)
        assert "## Page 3" in md
        assert "## Page 5" in md

    def test_highlight_format(self, sample_item_row, sample_annotations):
        md = format_annotations_markdown(sample_item_row, sample_annotations)
        assert "[yellow] **Highlight:**" in md
        assert "> This is a highlighted passage" in md
        assert "**Note:** Important finding" in md

    def test_note_format(self, sample_item_row, sample_annotations):
        md = format_annotations_markdown(sample_item_row, sample_annotations)
        assert "**Note:**" in md
        assert "Remember to follow up on this method" in md

    def test_red_highlight(self, sample_item_row, sample_annotations):
        md = format_annotations_markdown(sample_item_row, sample_annotations)
        assert "[red] **Highlight:**" in md
        assert "> Another key finding on page five" in md

    def test_empty_annotations(self, sample_item_row):
        empty = pd.DataFrame(columns=[
            "itemID", "type", "text", "comment", "color",
            "pageLabel", "sortIndex", "position", "paperItemID",
        ])
        md = format_annotations_markdown(sample_item_row, empty)
        assert "annotation_count: 0" in md
        assert "## Page" not in md


class TestBakeAnnotations:
    def test_highlight_baked(self, simple_pdf, sample_annotations, tmp_path):
        output_pdf = tmp_path / "output.pdf"
        warnings = bake_annotations(simple_pdf, sample_annotations, output_pdf)
        assert output_pdf.exists()

        doc = fitz.open(str(output_pdf))
        # Page 3 (index 2) should have annotations
        page = doc[2]
        annots = list(page.annots())
        assert len(annots) >= 1
        doc.close()

    def test_output_has_all_pages(self, simple_pdf, sample_annotations, tmp_path):
        output_pdf = tmp_path / "output.pdf"
        bake_annotations(simple_pdf, sample_annotations, output_pdf)

        doc = fitz.open(str(output_pdf))
        assert len(doc) == 6
        doc.close()

    def test_no_annotations(self, simple_pdf, tmp_path):
        empty = pd.DataFrame(columns=[
            "itemID", "type", "text", "comment", "color",
            "pageLabel", "sortIndex", "position", "paperItemID",
        ])
        output_pdf = tmp_path / "output.pdf"
        warnings = bake_annotations(simple_pdf, empty, output_pdf)
        assert output_pdf.exists()
        assert warnings == []

    def test_bad_position_json(self, simple_pdf, tmp_path):
        bad_ann = pd.DataFrame([{
            "itemID": 200,
            "type": 1,
            "text": "test",
            "comment": "",
            "color": "#ffd400",
            "position": "not valid json",
            "paperItemID": 42,
        }])
        output_pdf = tmp_path / "output.pdf"
        warnings = bake_annotations(simple_pdf, bad_ann, output_pdf)
        assert any("Bad position JSON" in w for w in warnings)

    def test_page_out_of_range(self, simple_pdf, tmp_path):
        ann = pd.DataFrame([{
            "itemID": 201,
            "type": 1,
            "text": "test",
            "comment": "",
            "color": "#ffd400",
            "position": json.dumps({"pageIndex": 99, "rects": [[100, 200, 300, 220]]}),
            "paperItemID": 42,
        }])
        output_pdf = tmp_path / "output.pdf"
        warnings = bake_annotations(simple_pdf, ann, output_pdf)
        assert any("out of range" in w for w in warnings)
