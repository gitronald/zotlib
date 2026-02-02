"""Tests for utility functions."""

from zotlib.utils import unlist


def test_unlist_simple():
    """Test flattening simple nested list."""
    nested = [[1, 2], [3, 4], [5]]
    assert unlist(nested) == [1, 2, 3, 4, 5]


def test_unlist_empty():
    """Test flattening empty list."""
    assert unlist([]) == []


def test_unlist_single():
    """Test flattening single-element nested list."""
    assert unlist([[1, 2, 3]]) == [1, 2, 3]


def test_unlist_strings():
    """Test flattening list of strings (characters)."""
    result = unlist([["a", "b"], ["c"]])
    assert result == ["a", "b", "c"]
