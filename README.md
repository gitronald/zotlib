# Zotero 7 Annotation Extraction Scripts

JavaScript utilities for extracting PDF annotations from Zotero 7 and saving them as markdown files.

## File Structure

```
zotero/
├── extract-annotations.js       # Interactive version with file picker dialog
├── extract-annotations-cli.js   # CLI version, writes to fixed directory
├── extract-annotations-debug.js # Debug script for troubleshooting
└── run-extract.sh               # Shell wrapper for CLI execution
```

---

## extract-annotations.js

**Interactive annotation extractor with file save dialog.**

Run this script in Zotero's JavaScript console (Tools → Developer → Run JavaScript) to extract all annotations from a selected item's PDF and save them to a markdown file of your choice.

### Usage

1. Select a single item in Zotero (the parent item or its PDF attachment)
2. Open Tools → Developer → Run JavaScript
3. Paste the script contents and click "Run"
4. Choose where to save the markdown file in the file picker dialog

### Features

- Extracts highlights, notes, underlines, and image annotations
- Preserves annotation comments
- Color-coded labels for highlights (yellow, red, green, blue, purple)
- Sorted by page number and position within page
- Includes item metadata (title, authors, year)

### Output Format

```markdown
# Annotations: Paper Title

**Authors:** Smith, John; Doe, Jane
**Year:** 2024
**Extracted:** 1/17/2026
**Total Annotations:** 15

---

## Page 1

[yellow] **Highlight:**
> This is the highlighted text from the PDF

**Note:** My comment about this highlight

## Page 2

[red] **Highlight:**
> Another highlight with a different color

...
```

---

## extract-annotations-cli.js

**Headless annotation extractor for CLI/automation use.**

This version skips the file picker dialog and writes directly to a predetermined directory, making it suitable for command-line invocation via Zotero's HTTP debug API.

### Configuration

Edit the `OUTPUT_DIR` variable at the top of the script:

```javascript
var OUTPUT_DIR = '/path/to/your/output/directory/';
```

Default: `~/Desktop/zotero-annotations/`

### Output Filename

Files are named with the pattern:
```
{Title}_{Timestamp}.md
```

Example: `My_Research_Paper_2026-01-17T14-30-00.md`

---

## run-extract.sh

**Shell script to invoke the CLI extractor remotely.**

### Prerequisites

1. Zotero 7 must be running
2. Enable remote debugging: Settings → Advanced → "Allow other applications to communicate with Zotero"
3. Select an item in Zotero before running

### Usage

```bash
./run-extract.sh
```

### How It Works

The script sends the JavaScript file to Zotero's local debug endpoint:

```bash
curl -X POST "http://127.0.0.1:23119/debug" \
    -H "Content-Type: application/javascript" \
    --data-binary @extract-annotations-cli.js
```

---

## extract-annotations-debug.js

**Diagnostic script for troubleshooting.**

Use this if the main scripts aren't working. It outputs step-by-step debug information about:

- Whether ZoteroPane is accessible
- Selected items and their types
- Attachment details and content types
- Annotation data structure

### Usage

1. Select an item in Zotero
2. Run in Tools → Developer → Run JavaScript
3. Check the return value for diagnostic output

---

## Annotation Types Supported

| Type | Extracted Data |
|------|----------------|
| Highlight | Text + comment + color |
| Note | Comment text |
| Underline | Text + comment |
| Image | Comment only (image not exported) |

## Color Labels

The scripts convert Zotero's hex colors to readable labels:

| Hex Code | Label |
|----------|-------|
| `#ffd400` | [yellow] |
| `#ff6666` | [red] |
| `#5fb236` | [green] |
| `#2ea8e5` | [blue] |
| `#a28ae5` | [purple] |
| `#e56eee` | [magenta] |
| `#f19837` | [orange] |

---

## Safety

These scripts are **read-only** with respect to your Zotero database. They only:

- Read item metadata and annotations
- Write to external markdown files

No Zotero data is modified.

---

## Troubleshooting

### "undefined" with no output

The async IIFE pattern can cause silent failures. Use `extract-annotations-debug.js` to diagnose.

### No file picker appears

The FilePicker API may have changed. Try the CLI version (`extract-annotations-cli.js`) which bypasses the dialog.

### curl connection refused

Ensure Zotero is running and remote debugging is enabled in Settings → Advanced.

### No annotations found

- Make sure the PDF has annotations made in Zotero's PDF reader (not imported from the original PDF)
- Check that you selected the parent item or its PDF attachment
