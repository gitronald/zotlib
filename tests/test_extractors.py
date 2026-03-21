"""Tests for the extractors module."""

import polars as pl

from zotlib.extractors import _add_authors, _clean_items


class TestCleanItems:
    def test_condenses_publication_title(self):
        items = pl.DataFrame(
            {
                "itemID": [1, 2],
                "date": ["2024-01-15", "2023-06-01"],
                "publicationTitle": ["Nature", None],
                "bookTitle": [None, "ML Handbook"],
            }
        )
        result = _clean_items(items)
        assert result["publication"].to_list() == ["Nature", "ML Handbook"]

    def test_extracts_year_and_month(self):
        items = pl.DataFrame({"itemID": [1], "date": ["2024-03-15"]})
        result = _clean_items(items)
        assert result["year"][0] == 2024
        assert result["month"][0] == 3

    def test_handles_null_date(self):
        items = pl.DataFrame({"itemID": [1], "date": [None]})
        result = _clean_items(items)
        assert result["year"][0] is None

    def test_handles_malformed_date(self):
        items = pl.DataFrame({"itemID": [1], "date": ["2024-00-00"]})
        result = _clean_items(items)
        # -00 gets replaced with -01
        assert result["year"][0] == 2024

    def test_cleans_pages_en_dash(self):
        items = pl.DataFrame({"itemID": [1], "date": ["2024-01-01"], "pages": ["1\u20135"]})
        result = _clean_items(items)
        assert result["pages"][0] == "1-5"


class TestAddAuthors:
    def test_joins_authors(self):
        items = pl.DataFrame({"itemID": [1, 2]})
        creators = pl.DataFrame(
            {
                "itemID": [1, 1, 2],
                "firstName": ["Alice", "Bob", "Carol"],
                "lastName": ["Smith", "Jones", "Lee"],
            }
        )
        result = _add_authors(items, creators)
        authors = result.sort("itemID")["authors"].to_list()
        assert "Alice Smith" in authors[0]
        assert "Bob Jones" in authors[0]
        assert authors[1] == "Carol Lee"

    def test_no_authors(self):
        items = pl.DataFrame({"itemID": [1]})
        creators = pl.DataFrame({"itemID": [2], "firstName": ["X"], "lastName": ["Y"]})
        result = _add_authors(items, creators)
        assert result["authors"][0] is None
