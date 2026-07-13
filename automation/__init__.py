"""
automation
==========
Core automation modules for the Automation Toolkit:

    file_renamer.py      Batch renaming (prefix/suffix/timestamp/etc.)
    folder_organizer.py  Organize a directory by file type
    duplicate_finder.py  Find/remove duplicate files by content hash
    pdf_tools.py         Merge, split, rotate, encrypt, decrypt, inspect PDFs
    excel_tools.py       Read, build, format, filter, and export Excel data
    backup.py            Create and rotate timestamped backups
    logger.py            Shared logging configuration

These modules are intentionally decoupled from the CLI: every public
function takes plain arguments (paths, strings, ints) and returns plain
data, so they can be imported and used directly from other Python code
or from tests, not just from the command line.
"""

__version__ = "1.0.0"
