"""Tests for citation formatters."""

from zotlib.formatters.apa import format_apa_reference, format_cv_as_apa


def test_format_apa_reference_journal(sample_cv_row):
    """Test APA formatting for journal article."""
    result = format_apa_reference(sample_cv_row)

    assert "John Smith, Jane Doe" in result
    assert "(2023)" in result
    assert "A Study of Something Important" in result
    assert "_Journal of Examples, 10_" in result
    assert "(2)" in result
    assert "100-115" in result
    assert "10.1234/example.2023" in result


def test_format_apa_reference_conference(sample_cv_items):
    """Test APA formatting for conference paper."""
    conf_row = sample_cv_items.row(1, named=True)
    result = format_apa_reference(conf_row)

    assert "Alice Johnson" in result
    assert "(2022)" in result
    assert "Conference Presentation Title" in result
    assert "https://example.com/paper" in result


def test_format_cv_as_apa(sample_cv_items):
    """Test formatting multiple items as APA."""
    result = format_cv_as_apa(sample_cv_items)

    # Should have section headers for each type
    assert "## journalArticle" in result
    assert "## conferencePaper" in result

    # Should have both references
    assert "John Smith" in result
    assert "Alice Johnson" in result
