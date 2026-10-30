"""WebFlow job links and the "WF<number>" text shown for them (no I/O, no Qt)."""
from __future__ import annotations

import re

_JOB_NUMBER = re.compile(r"(\d+)/?$")


def webflow_link_text(url: str) -> str:
    """"WF" + the job number at the end of the link, e.g. ".../app/ShowJob/16406" -> "WF16406"."""
    match = _JOB_NUMBER.search((url or "").strip())
    return f"WF{match.group(1)}" if match else ""


def job_number(url: str) -> int | None:
    """The job number at the end of a link (None when the link does not end in one)."""
    match = _JOB_NUMBER.search((url or "").strip())
    return int(match.group(1)) if match else None


def is_link(text: str) -> bool:
    return (text or "").strip().lower().startswith(("http://", "https://"))
