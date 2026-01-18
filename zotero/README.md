# Zotero CV Export

Extract bibliographic data from a local Zotero SQLite database and format it for CV/publication lists.

## Scripts

### Zotero Database Extraction

- `zotero.py`
  - **Description**
    - Extracts bibliographic data from a local Zotero SQLite database by joining item tables to reconstruct full metadata
  - **Inputs**
    - `/mnt/c/Users/rer/Zotero/zotero.sqlite`: Zotero SQLite database file
  - **Outputs**
    - `data/items.csv`: All Zotero items with merged field values and item types
    - `data/creators.csv`: Item-creator relationships with author names
    - `data/collections.csv`: Item-collection memberships
    - `data/libraries.csv`: Library metadata
    - `data/cv.csv`: Filtered items from the 'rer' collection with selected columns

### APA Reference Formatter

- `apa.py`
  - **Description**
    - Formats CV items as APA-style references with HTML hyperlinks for DOIs/URLs
  - **Inputs**
    - `data/cv.csv`: CV items exported from zotero.py
  - **Outputs**
    - `output/apa.md`: APA-formatted references grouped by publication type (journalArticle, conferencePaper, etc.)

### Publication Count Analysis

- `analysis.py`
  - **Description**
    - Analyzes publication counts by year from CV data
  - **Inputs**
    - `data/cv.csv`: CV items with publication dates
  - **Outputs**
    - Year-by-count frequency table displayed in console

### PsycNET DOI Scraper

- `get_psycnet_doi.py`
  - **Description**
    - Scrapes DOI from APA PsycNET record pages using BeautifulSoup
  - **Inputs**
    - PsycNET URL (hardcoded in script)
  - **Outputs**
    - DOI printed to console
