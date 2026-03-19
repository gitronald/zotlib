"""Smoke tests for CLI commands."""

from typer.testing import CliRunner

from zotlib.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Extract and format" in result.output


def test_schema_all():
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert "items" in result.output


def test_schema_single_table():
    result = runner.invoke(app, ["schema", "items"])
    assert result.exit_code == 0
    assert "itemID" in result.output


def test_schema_unknown_table():
    result = runner.invoke(app, ["schema", "nonexistent"])
    assert result.exit_code == 0
    assert "Unknown table" in result.output


def test_extract_help():
    result = runner.invoke(app, ["extract", "--help"])
    assert result.exit_code == 0


def test_collections_help():
    result = runner.invoke(app, ["collections", "--help"])
    assert result.exit_code == 0


def test_covers_help():
    result = runner.invoke(app, ["covers", "--help"])
    assert result.exit_code == 0


def test_thumbnails_help():
    result = runner.invoke(app, ["thumbnails", "--help"])
    assert result.exit_code == 0


def test_backup_help():
    result = runner.invoke(app, ["backup", "--help"])
    assert result.exit_code == 0


def test_export_help():
    result = runner.invoke(app, ["export", "--help"])
    assert result.exit_code == 0


def test_tables_help():
    result = runner.invoke(app, ["tables", "--help"])
    assert result.exit_code == 0
