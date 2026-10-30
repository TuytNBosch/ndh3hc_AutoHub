"""Which event the newest variant belongs to (pure)."""
from __future__ import annotations

from typing import Sequence

NO_EVENT = "(No event)"


def latest_event(variants: Sequence[dict]) -> str | None:
    """Event of the variant with the newest ``created_at``; without usable dates, of the last variant listed."""
    if not variants:
        return None
    newest = variants[-1]
    dated = [v for v in variants if v.get("created_at") is not None]
    try:
        newest = max(reversed(dated), key=lambda v: v["created_at"]) if dated else newest
    except TypeError:  # dates of mixed kinds can't be compared; keep the last listed
        pass
    return newest.get("event") or NO_EVENT
