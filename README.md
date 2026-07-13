# Automation Toolkit

![Tests](https://github.com/kunalkirtak/Automation-Toolkit/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

A modular, command-line Python toolkit for everyday file, PDF, and Excel automation — batch renaming, folder organizing, duplicate detection, PDF merging/splitting/encryption, and Excel report generation, all from one CLI.

Built as a portfolio project to demonstrate production-style Python: a clean package layout, typed function signatures, centralized config and logging, an `argparse`-based CLI, and an 82-test `pytest` suite backed by CI — not a single notebook of scripts.

> **Project status:** Feature-complete. All three build phases are done — CLI, config, and logging (Part 1); every automation module (Part 2); and an 82-test `pytest` suite with GitHub Actions CI (Part 3). See [Roadmap](#roadmap) for how it was built in stages, and [Testing](#testing) for how to run the suite yourself.

---

## Features

### File Automation
- [x] Batch file renaming (prefix / suffix)
- [x] Rename using timestamps
- [x] Remove spaces from filenames
- [x] Bulk change file extensions
- [x] Organize a folder by file type
- [x] Detect duplicate files by content hash (not just filename)

### PDF Automation
- [x] Merge multiple PDFs
- [x] Split a PDF into individual pages
- [x] Extract text from a PDF
- [x] Rotate pages
- [x] Encrypt / password-protect a PDF
- [x] Decrypt a PDF
- [x] Extract PDF metadata

### Excel Automation
- [x] Read Excel workbooks into DataFrames
- [x] Create new workbooks with headers
- [x] Update specific cells
- [x] Apply formatting (bold headers, autofit columns)
- [x] Create grouped summary sheets
- [x] Filter data by column value
- [x] Export reports to XLSX / CSV

### Engineering
- [x] `argparse`-based CLI with per-feature subcommands
- [x] Centralized, rotating file + console logging
- [x] Dataclass-driven configuration (JSON overrides supported)
- [x] Full type hints across the codebase
- [x] Exception handling with clean CLI error messages (no raw tracebacks for expected input errors)
- [x] Modular package (`automation/`) — importable independent of the CLI
- [x] Progress indicators (`tqdm`) for batch operations
- [x] Sample data + example outputs (`sample_data/`)
- [x] Unit tests (`pytest`, 82 tests / 94% coverage)
- [x] GitHub Actions CI (matrix-tested on Python 3.10 – 3.12)

---

## Project Structure

```
Automation-Toolkit/
│
├── README.md
├── requirements.txt
├── .gitignore
├── config.py                 # Central dataclass config (paths, defaults, JSON overrides)
├── cli.py                    # argparse CLI definition (all subcommands)
├── main.py                   # Entry point: parses args, dispatches to automation/
│
├── automation/
│   ├── __init__.py
│   ├── logger.py              # Rotating file + console logging setup
│   ├── file_renamer.py        # Batch renaming (prefix/suffix/timestamp/etc.)
│   ├── folder_organizer.py    # Organize by file type
│   ├── duplicate_finder.py    # Content-hash duplicate detection
│   ├── pdf_tools.py           # Merge/split/rotate/encrypt PDFs
│   ├── excel_tools.py         # Read/build/format/filter Excel
│   └── backup.py              # Timestamped zip backups + rotation
│
├── sample_data/                # Sample inputs used by the usage examples below
│   ├── files/                   # Mixed file types for rename/organize/duplicate demos
│   ├── pdfs/                    # Sample PDFs for pdf_tools demos
│   └── excel/                   # Sample workbook for excel_tools demos
│
├── output/                    # Generated files land here
├── logs/                      # automation.log (rotating)
│
├── tests/                     # 82 tests, 94% coverage — see Testing below
│   ├── conftest.py             # Shared fixtures (isolated tmp_path-based test data)
│   ├── test_file_renamer.py
│   ├── test_folder_organizer.py
│   ├── test_duplicate_finder.py
│   ├── test_pdf_tools.py
│   ├── test_excel_tools.py
│   ├── test_backup.py
│   └── test_cli.py             # argparse parsing + full CLI integration tests
│
├── .github/workflows/
   └── tests.yml               # CI: pytest matrix (3.10–3.12) + CLI smoke test

```

---

## Installation

```bash
git clone https://github.com/kunalkirtak/Automation-Toolkit.git
cd Automation-Toolkit

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Requires **Python 3.10+** (uses `X | None`-style type hints).

---

## Usage

All commands run through `main.py`. Use `--help` on any command or subcommand to see its full options.

```bash
python main.py --help
```

### File automation

```bash
# Preview a batch rename before touching disk
python main.py rename prefix --dir ./sample_data/files --prefix "IMG_" --dry-run

# Actually rename
python main.py rename suffix --dir ./sample_data/files --suffix "_v2"
python main.py rename timestamp --dir ./sample_data/files --format "%Y%m%d_%H%M%S"
python main.py rename clean-spaces --dir ./sample_data/files --replacement "_"
python main.py rename extension --dir ./sample_data/files --old-ext .txt --new-ext .md

# Organize a messy folder into Images/, Documents/, Spreadsheets/, etc.
python main.py organize --dir ./Downloads --dry-run

# Find duplicate files by content (SHA-256), optionally delete extras
python main.py duplicates --dir ./sample_data/files
python main.py duplicates --dir ./sample_data/files --delete --keep first --dry-run
```

### PDF automation

```bash
python main.py pdf merge --files a.pdf b.pdf c.pdf --output merged.pdf
python main.py pdf split --file merged.pdf --output-dir ./output/pages
python main.py pdf extract-text --file report.pdf --output report.txt
python main.py pdf rotate --file scan.pdf --degrees 90 --output scan_rotated.pdf
python main.py pdf encrypt --file report.pdf --password "secret123" --output report_locked.pdf
python main.py pdf decrypt --file report_locked.pdf --password "secret123" --output report_open.pdf
python main.py pdf metadata --file report.pdf
```

### Excel automation

```bash
python main.py excel read --file data.xlsx --sheet Sheet1
python main.py excel create --file new.xlsx --headers Name Age Email
python main.py excel format --file new.xlsx --sheet Sheet1
python main.py excel summary --file sales.xlsx --sheet Sheet1 --group-by Region --agg-column Revenue
python main.py excel filter --file data.xlsx --sheet Sheet1 --column Status --value Active --output active.xlsx
python main.py excel export --file data.xlsx --sheet Sheet1 --format csv --output report.csv
```

### Backup

```bash
python main.py backup --source ./important_docs --destination ./backups --max-keep 5
```

### Global flags

```bash
python main.py -v ...              # verbose (DEBUG-level) logging
python main.py --config config.local.json ...   # load config overrides from JSON
```

---

## Configuration

All paths and defaults live in `config.py` as a single `Config` dataclass. To override any value without editing source code, write a JSON file:

```json
{
  "log_level": "DEBUG",
  "hash_algorithm": "md5",
  "max_backups_to_keep": 10
}
```

and pass it in:

```bash
python main.py --config config.local.json organize --dir ./Downloads
```

## Testing

The suite has 82 tests covering every automation module plus CLI argument parsing and full end-to-end dispatch (calling `main.main()` the same way the command line does, not just the underlying functions). Every fixture builds its own isolated data in pytest's `tmp_path`, so tests never touch the real `sample_data/` folder.

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=automation --cov=cli --cov=main --cov=config --cov-report=term-missing
```

Current coverage:

```
Name                             Stmts   Miss  Cover
--------------------------------------------------------------
automation/__init__.py               1      0   100%
automation/backup.py                41      2    95%
automation/duplicate_finder.py      55      5    91%
automation/excel_tools.py           94      1    99%
automation/file_renamer.py          86      5    94%
automation/folder_organizer.py      50     13    74%
automation/logger.py                38      1    97%
automation/pdf_tools.py            111      0   100%
cli.py                             114      0   100%
config.py                           59      7    88%
main.py                            101      9    91%
--------------------------------------------------------------
TOTAL                              750     43    94%
============================== 82 passed in 5.99s ==============================
```

CI (`.github/workflows/tests.yml`) runs this same suite on every push and PR across Python 3.10, 3.11, and 3.12, plus a separate smoke-test job that runs the actual CLI against the shipped `sample_data/`.

---

## Example Output

Real, unedited output from running the toolkit against the sample data in this repo:

**Duplicate detection** (`sample_data/files/` has two intentionally duplicated files):

```
$ python main.py duplicates --dir ./sample_data/files
2026-07-13 10:12:05 | INFO | automation.duplicate_finder | Found 2 duplicate group(s), 2 redundant file(s)
```

**PDF metadata:**

```
$ python main.py pdf metadata --file ./sample_data/pdfs/report_a.pdf
Producer: pypdf
Title: Sample report_a.pdf
Author: Automation Toolkit
page_count: 2
encrypted: False
file_size_bytes: 615
```

**Excel read:**

```
$ python main.py excel read --file ./sample_data/excel/sales.xlsx
    Name Region  Revenue    Status
0   Asha  North    12000    Active
1   Ravi  South     9500    Active
2  Meera  North    15200  Inactive
3  Karan   West     8700    Active
4  Priya  South    11000  Inactive
5    Dev   West     9900    Active
```

---

## Logging

Every run writes structured, timestamped logs to `logs/automation.log` (rotated automatically at ~2 MB, keeping 3 backups) and mirrors them to the console. Example line:

```
2026-07-11 09:31:51 | WARNING  | automation.file_renamer | Skipped 2 files: permission denied
```

---

## Roadmap

This project was built in three deliberate stages so each piece was reviewable on its own:

1. **Part 1 — Project setup** ✅: README, requirements, `.gitignore`, `config.py`, `automation/logger.py`, `cli.py`, `main.py`, and typed stub modules defining every function's signature.
2. **Part 2 — Automation modules** ✅: full, tqdm-backed implementations of `file_renamer`, `pdf_tools`, `excel_tools`, `folder_organizer`, `duplicate_finder`, and `backup`, plus sample data in `sample_data/` and hardened CLI error handling.
3. **Part 3 — Testing & polish** ✅ *(this commit)*: an 82-test `pytest` suite (94% coverage) covering every module and full CLI integration, GitHub Actions CI across Python 3.10–3.12, real example output in this README, and a final documentation pass.

**Future extensions:** scheduled/cron-triggered runs, a lightweight GUI, cloud storage integration (S3 / Google Drive), and a REST API wrapper around the same `automation/` modules.

---

## Tech Stack

Python 3 · `pathlib` · `argparse` · `logging` · `openpyxl` · `pypdf` · `pandas` · `shutil` · `hashlib` · `tqdm` · `pytest`

---

## License

Released under the [MIT License](LICENSE).
