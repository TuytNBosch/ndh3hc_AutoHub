"""WebFlow job creation with ownership of the browser session (no Qt)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass(frozen=True)
class WebFlowConfig:
    driver_path: str
    base_url: str
    tool_version: str
    routing: str


class WebFlowSession(Protocol):
    """The part of the WebFlow browser automation this service uses."""

    def create_and_fill_jobs(self, variants: list, tool_version: str, routing: str) -> list: ...

    def quit(self) -> None: ...


class WebFlowJobService:
    def __init__(self, webflow_factory: Callable[..., WebFlowSession]):
        self._webflow_factory = webflow_factory
        self._webflow: WebFlowSession | None = None

    def create_jobs(self, variants: list[dict], config: WebFlowConfig) -> list[dict]:
        self.shutdown()
        self._webflow = self._webflow_factory(driver_path=config.driver_path, base_url=config.base_url)
        return self._webflow.create_and_fill_jobs(variants, tool_version=config.tool_version, routing=config.routing)

    def shutdown(self) -> None:
        if self._webflow is None:
            return
        try:
            self._webflow.quit()
        except Exception:
            pass
        self._webflow = None
