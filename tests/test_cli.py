"""Smoke tests for CLI commands."""

from typer.testing import CliRunner

from zotlib.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Extract and format" in result.output


def test_show_tables():
    result = runner.invoke(app, ["show-tables"])
    assert result.exit_code == 0
    assert "items" in result.output


def test_show_tables_single():
    result = runner.invoke(app, ["show-tables", "items"])
    assert result.exit_code == 0
    assert "itemID" in result.output


def test_show_tables_unknown():
    result = runner.invoke(app, ["show-tables", "nonexistent"])
    assert result.exit_code == 0
    assert "Unknown table" in result.output


def test_show_collections_help():
    result = runner.invoke(app, ["show-collections", "--help"])
    assert result.exit_code == 0


def test_export_csv_help():
    result = runner.invoke(app, ["export-csv", "--help"])
    assert result.exit_code == 0


def test_export_apa_help():
    result = runner.invoke(app, ["export-apa", "--help"])
    assert result.exit_code == 0


def test_export_covers_help():
    result = runner.invoke(app, ["export-covers", "--help"])
    assert result.exit_code == 0


def test_export_annotations_help():
    result = runner.invoke(app, ["export-annotations", "--help"])
    assert result.exit_code == 0


def test_backup_help():
    result = runner.invoke(app, ["backup", "--help"])
    assert result.exit_code == 0
