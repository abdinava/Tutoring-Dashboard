"""All card data here is fake. Never put real swipe data in tests."""

import pytest

from tutoring_kiosk.rcard import fake_swipe, format_name, parse_card


def test_parses_valid_card():
    card = parse_card(fake_swipe("999999901"))
    assert card.student_id == "999999901"
    assert card.name == "Pat Tester"


@pytest.mark.parametrize("field,expected", [
    ("O'BRIEN-SMITH/MARY ANN", "Mary Ann O'Brien-Smith"),
    ("CHER", "Cher"),
    ("TESTER/PAT.MR", "Pat Tester"),
    ("", None),
])
def test_unusual_names(field, expected):
    assert format_name(field) == expected


@pytest.mark.parametrize("raw", [
    "",
    "not a card",
    ";6012000000000000=0000?",                                # Track 2 only
    fake_swipe().replace("%B6012", "%B4111"),                 # not an R'Card
    "%B6012000000000000^TESTER/PAT^" + "0" * 12 + "12345?",   # ID too short
])
def test_rejects_invalid_swipes(raw):
    assert parse_card(raw) is None
