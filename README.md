# Automation Toolkit

A modular, command-line Python toolkit for everyday file, PDF, and Excel automation — batch renaming, folder organizing, duplicate detection, PDF merging/splitting/encryption, and Excel report generation, all from one CLI.

Built as a portfolio project to demonstrate production-style Python: a clean package layout, typed function signatures, centralized config and logging, `argparse`-based CLI, and unit tests — not a single notebook of scripts.

> **Project status:** Part 2 of 3 complete — CLI, config, logging, and every automation module (file, PDF, Excel) are fully implemented and working end to end. Formal `pytest` unit tests and GitHub Actions CI ship in Part 3. See [Roadmap](#roadmap).

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
- [ ] Unit tests (`pytest`)
- [ ] GitHub Actions CI

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
├── tests/                     # pytest unit tests (Part 3)
└── notebooks/
    └── Demo.ipynb              # Optional interactive walkthrough (Part 3)
```

---

## Installation

```bash
git clone https://github.com/<your-username>/Automation-Toolkit.git
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

---

## Logging

Every run writes structured, timestamped logs to `logs/automation.log` (rotated automatically at ~2 MB, keeping 3 backups) and mirrors them to the console. Example line:

```
2026-07-11 09:31:51 | WARNING  | automation.file_renamer | Skipped 2 files: permission denied
```

---

## Testing

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=automation
```

*(Test suite ships in Part 3. Every command in this README has been manually smoke-tested against the sample data in `sample_data/`.)*

---

## Roadmap

This project is being built in three deliberate stages so each piece is reviewable on its own:

1. **Part 1 — Project setup** ✅: README, requirements, `.gitignore`, `config.py`, `automation/logger.py`, `cli.py`, `main.py`, and typed stub modules defining every function's signature.
2. **Part 2 — Automation modules** ✅ *(this commit)*: full, tqdm-backed implementations of `file_renamer`, `pdf_tools`, `excel_tools`, `folder_organizer`, `duplicate_finder`, and `backup`, plus sample data in `sample_data/` and hardened CLI error handling.
3. **Part 3 — Testing & polish**: `pytest` unit tests, example outputs in the README, GitHub Actions CI, and a final documentation pass.

**Future extensions:** scheduled/cron-triggered runs, a lightweight GUI, cloud storage integration (S3 / Google Drive), and a REST API wrapper around the same `automation/` modules.

---

## Tech Stack

Python 3 · `pathlib` · `argparse` · `logging` · `openpyxl` · `pypdf` · `pandas` · `shutil` · `hashlib` · `tqdm` · `pytest`

---

## License

Released under the [MIT License](LICENSE).
