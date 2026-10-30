"""Explains why a workbook cannot be written (pure file checks, no Excel)."""
from __future__ import annotations

import os
from pathlib import Path


def write_block_reason(path: str) -> str:
    """The most likely reason `path` cannot be written, or an empty string when none is found."""
    file = Path(path)
    if not file.exists():
        return "the file does not exist"
    if not os.access(file, os.W_OK):
        return "the file has the Read-only attribute (clear it in the file Properties)"
    try:
        with file.open("r+b"):
            pass
    except PermissionError:
        return "the file is open in Excel or another program (close it there)"
    except OSError as error:
        return f"the file cannot be opened for writing ({error})"
    if (file.parent / f"~${file.name}").exists():
        return "an Excel lock file (~$...) exists; the file is open elsewhere, or Excel closed badly (delete the lock file)"
    return ""
