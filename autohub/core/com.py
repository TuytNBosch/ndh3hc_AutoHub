"""COM apartment management for worker threads that drive Excel."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

try:
    import pythoncom
except ImportError:  # non-Windows environments (e.g. CI) have no COM
    pythoncom = None


@contextmanager
def com_session() -> Iterator[None]:
    """Initialise COM for the current thread and always release it."""
    if pythoncom is None:
        yield
        return
    pythoncom.CoInitialize()
    try:
        yield
    finally:
        pythoncom.CoUninitialize()
