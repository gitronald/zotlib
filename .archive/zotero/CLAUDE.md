# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project extracts bibliographic data from a local Zotero SQLite database and formats it for CV/publication lists. It reads the Zotero database, joins tables to reconstruct item metadata, and outputs APA-formatted references.

## Running the Scripts

```bash
# Extract data from Zotero database to CSV files
python zotero.py

# Format CV items as APA references (requires cv.csv from zotero.py)
python apa.py

# Analyze publication counts by year (Jupyter/IPython)
python analysis.py
```

## Dependencies

Install from requirements.txt. Key dependencies:
- pandas, sqlite3 for data handling
- beautifulsoup4, requests for DOI scraping
- utils package from git+https://github.com/gitronald/utils

## Architecture

**zotero.py** - Main extraction script
- Connects to Zotero SQLite database at `/mnt/c/Users/rer/Zotero/zotero.sqlite`
- Joins `itemData`, `fieldsCombined`, `itemDataValues` tables to reconstruct item metadata
- Exports: items.csv, creators.csv, collections.csv, libraries.csv, cv.csv
- The `cv.csv` output filters to items in the 'rer' collection

**apa.py** - APA reference formatter
- Reads cv.csv and formats each item as an APA citation
- Outputs apa.md with references grouped by publication type (journalArticle, conferencePaper, etc.)
- Generates HTML hyperlinks for DOIs/URLs

**Data flow**: Zotero DB → zotero.py → cv.csv → apa.py → apa.md