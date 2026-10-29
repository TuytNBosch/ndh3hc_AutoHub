"""Pure parsing of Kick Off Meeting deck tables into project facts (no pptx, files or logging).

Input is every table row of the deck as a list of cell texts. Each fact is one `Rule`: a cell matching
`label` followed, in the same row, by a cell whose text matches `value`. The first match in the deck wins,
so supporting another fact (or another wording of one) is a one-line change in `RULES`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from autohub.core.records import KickOffInfo


@dataclass(frozen=True)
class Rule:
    field: str
    label: re.Pattern
    value: re.Pattern
    #: turns the matched text (group 1 when the pattern has one) into the stored value.
    clean: Callable[[str], str] = str.strip


def _rule(field: str, label: str, value: str, clean: Callable[[str], str] = str.strip) -> Rule:
    return Rule(field, re.compile(label, re.I), re.compile(value, re.I), clean)


RULES: tuple[Rule, ...] = (
    _rule("power_kw", r"^(maximum\s+)?power\b", r"(\d+(?:\.\d+)?)\s*kW"),
    _rule("cylinders", r"^engine\s+type\b", r"\bL(\d{1,2})\b"),
    _rule("ecu_hw_name", r"^ecu$", r"^(MG1\s*[A-Z]{2}\d{3}|MED?17(?:\.\d+)*)$", lambda text: re.sub(r"\s+", "", text)),
)


def _cell_value(rule: Rule, cells: Sequence[str]) -> str | None:
    for index, cell in enumerate(cells):
        if not rule.label.search(cell.strip()):
            continue
        for candidate in cells[index + 1 :]:
            match = rule.value.search(candidate.strip())
            if match:
                return rule.clean(match.group(1) if match.groups() else match.group(0))
    return None


def parse_kick_off(rows: Iterable[Sequence[str]], rules: Sequence[Rule] = RULES) -> KickOffInfo:
    info: KickOffInfo = {}
    for cells in rows:
        for rule in rules:
            if rule.field not in info:
                value = _cell_value(rule, cells)
                if value:
                    info[rule.field] = value
    return info
