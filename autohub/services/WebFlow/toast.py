"""Reading the result of a save from WebFlow's toast message (no Selenium)."""
from __future__ import annotations

_SEVERITIES = ("success", "error", "warn", "info")


def toast_severity(css_class: str | None) -> str | None:
    """"success" / "error" / "warn" / "info" for a PrimeNG ``p-toast-message-<severity>`` class, else None."""
    classes = (css_class or "").split()
    for severity in _SEVERITIES:
        if f"p-toast-message-{severity}" in classes:
            return severity
    return None
