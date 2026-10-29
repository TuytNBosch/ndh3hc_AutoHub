"""Destination codes of the Honda ECU part numbers and the markets they stand for (pure)."""
from __future__ import annotations

import re

#: Destination code -> countries. The leading "K" of a part-number destination ("KJ", "KA") only marks it
#: as a destination, so "KJ" is looked up as "J" when the full code is not listed.
DESTINATION_MARKETS: dict[str, str] = {
    "A": "US/Guam/Saipan/NATO/Puerto Rico/American Samoa",
    "C": "Canada",
    "K": "Bahamas/Bolivia/Colombia/Costa Rica/Ecuador/Panama/Peru",
    "X": "Mexico",
    "Q": "Australia/New Zealand",
    "IN": "Indonesia",
    "N": "Kenya/Namibia/South Africa/Tanzania/Uganda/Zambia",
    "J": "Japan",
    "U": "Hong Kong/Macau",
    "MA": "Malaysia",
    "PH": "Cambodia/Laos/Philippines",
    "S": "Singapore",
    "FO": "Taiwan",
    "E": "UK",
    "G": "Germany/Greece/Hungary/Israel/Poland/Portugal",
    "H": "China",
    "M": "Brazil",
    "Z": "Thailand",
    "VT": "Vietnam",
    "Y": "Saudi",
    "P": "Argentina",
    "ID": "India/Sri Lanka/Nepal/Bhutan",  # a full code of its own, unlike the K-prefixed ones
}

_SEPARATORS = re.compile(r"[/,;|\s]+")
_CODE = re.compile(r"[A-Z]{1,3}")


def market_for_code(code: str) -> str | None:
    code = code.strip().upper()
    if code in DESTINATION_MARKETS:
        return DESTINATION_MARKETS[code]
    if code.startswith("K"):
        return DESTINATION_MARKETS.get(code[1:])
    return None


def market_from_destination(destination) -> str:
    """"KE/KG" -> "UK|Germany/Greece/Hungary/Israel/Poland/Portugal"; unknown codes stay as written, notes are dropped."""
    text = "" if destination is None else str(destination)
    markets: list[str] = []
    for token in _SEPARATORS.split(text.strip()):
        code = token.upper()
        if not _CODE.fullmatch(code):
            continue  # e.g. the "with Fusion" remark
        markets.append(market_for_code(code) or code)
    return "|".join(dict.fromkeys(markets))
