import pytest

from autohub.core.markets import market_from_destination


@pytest.mark.parametrize(
    "destination, expected",
    [
        ("KJ", "Japan"),
        ("M", "Brazil"),
        ("FO", "Taiwan"),
        ("KE/KG", "UK|Germany/Greece/Hungary/Israel/Poland/Portugal"),
        ("KA/KC", "US/Guam/Saipan/NATO/Puerto Rico/American Samoa|Canada"),
        ("MA/IN", "Malaysia|Indonesia"),
        ("MA/IN/\nKK/PH", "Malaysia|Indonesia|Bahamas/Bolivia/Colombia/Costa Rica/Ecuador/Panama/Peru|Cambodia/Laos/Philippines"),
        ("KQ\nwith Fusion", "Australia/New Zealand"),
        ("ID", "India/Sri Lanka/Nepal/Bhutan"),
        ("kvt", "Vietnam"),
        ("KX/KX", "Mexico"),
        ("QQQ", "QQQ"),
        ("", ""),
        (None, ""),
    ],
)
def test_destination_codes_become_markets(destination, expected):
    assert market_from_destination(destination) == expected
