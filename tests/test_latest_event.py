from datetime import datetime

from autohub.core.latest_event import latest_event


def v(event, created):
    return {"event": event, "created_at": created}


def test_newest_created_at_wins():
    variants = [v("A", datetime(2025, 3, 1)), v("B", datetime(2025, 5, 1)), v("C", datetime(2025, 4, 1))]
    assert latest_event(variants) == "B"


def test_without_dates_the_last_listed_wins():
    assert latest_event([v("A", None), v("B", None)]) == "B"


def test_mixed_date_kinds_fall_back_to_the_last_listed():
    assert latest_event([v("A", datetime(2025, 1, 1)), v("B", "x")]) == "B"


def test_empty_event_and_no_variants():
    assert latest_event([v("", None)]) == "(No event)"
    assert latest_event([]) is None
