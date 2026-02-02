"""Pytest fixtures for zotlib tests."""

import pytest
import pandas as pd


@pytest.fixture
def sample_cv_row():
    """Sample CV item row for testing APA formatting."""
    return pd.Series({
        "itemID": 1,
        "typeName": "journalArticle",
        "authors": "John Smith, Jane Doe",
        "title": "A Study of Something Important",
        "year": 2023,
        "publication": "Journal of Examples",
        "volume": "10",
        "issue": "2",
        "pages": "100-115",
        "DOI": "10.1234/example.2023",
        "url": None,
        "date": pd.Timestamp("2023-06-15"),
    })


@pytest.fixture
def sample_cv_items(sample_cv_row):
    """Sample CV items DataFrame for testing."""
    rows = [
        sample_cv_row,
        pd.Series({
            "itemID": 2,
            "typeName": "conferencePaper",
            "authors": "Alice Johnson",
            "title": "Conference Presentation Title",
            "year": 2022,
            "publication": "Proceedings of Example Conference",
            "volume": None,
            "issue": None,
            "pages": "50-55",
            "DOI": None,
            "url": "https://example.com/paper",
            "date": pd.Timestamp("2022-03-10"),
        }),
    ]
    return pd.DataFrame(rows)
