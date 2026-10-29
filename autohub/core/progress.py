"""Progress reporting port: a window that shows the steps of a long action and its final result."""
from __future__ import annotations

from typing import Callable, Protocol


class ProgressWindow(Protocol):
    def step(self, text: str) -> None:
        """Show what is being done now. Safe to call from a worker thread."""
        ...

    def succeed(self, text: str) -> None:
        """Show the result; the window may be closed from now on."""
        ...

    def fail(self, text: str) -> None:
        """Show the error; the window may be closed from now on."""
        ...


#: Reports one step of a running action; services take it so they stay free of any UI.
ProgressCallback = Callable[[str], None]


def no_progress(_text: str) -> None:
    pass
