"""Removes Excel's "read-only recommended" flag from an .xlsx (the prompt "The author would like you to open ... read-only")."""
from __future__ import annotations

import os
import re
import tempfile
import zipfile

_FLAG = re.compile(rb'<fileSharing\b[^>]*\breadOnlyRecommended="(?:1|true)"[^>]*/>')
_WORKBOOK = "xl/workbook.xml"


def has_read_only_recommended(path: str) -> bool:
    try:
        with zipfile.ZipFile(path) as package:
            return bool(_FLAG.search(package.read(_WORKBOOK)))
    except (OSError, KeyError, zipfile.BadZipFile):
        return False


def clear_read_only_recommended(path: str) -> bool:
    """Rewrites `path` without the flag; True when it was removed. Other content is copied unchanged.

    Returns False (and leaves the file alone) when there is no flag or the file cannot be rewritten (e.g. locked)."""
    if not has_read_only_recommended(path):
        return False
    handle, temp_path = tempfile.mkstemp(suffix=".xlsx", dir=os.path.dirname(os.path.abspath(path)))
    os.close(handle)
    try:
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == _WORKBOOK:
                    data = _FLAG.sub(b"", data)
                target.writestr(item, data)
        os.replace(temp_path, path)
        return True
    except OSError:
        return False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
