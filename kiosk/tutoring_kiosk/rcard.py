"""Parse a UCR R'Card swipe (ISO/IEC 7813 Track 1).

    %B<card number, starts 6012>^<LAST/FIRST>^<12 shared digits><9-digit ID><padding>?

Only the student ID and a display name are returned. The card number is
discarded. Raw swipe text must never be logged or stored.
Verify these rules against ucr_rcard_decoder.py from the prototype.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

CARD_PREFIX = "6012"
SHARED_DIGITS = 12
ID_LENGTH = 9

_TRACK1 = re.compile(r"%B(?P<pan>\d{12,19})\^(?P<name>[^\^?]{0,26})\^(?P<disc>[0-9 ]*)")


@dataclass(frozen=True)
class Card:
    student_id: str
    name: Optional[str]  # shown on the confirm screen only


def format_name(field: str) -> Optional[str]:
    """'O'BRIEN/MARY ANN' -> "Mary Ann O'Brien". Never raises."""
    last, _, first = " ".join(field.split()).partition("/")
    first = first.split(".", 1)[0]  # drop optional ".TITLE"
    name = " ".join(p.strip() for p in (first, last) if p.strip()).strip(" .")
    if not name:
        return None
    return re.sub(r"[A-Za-z]+", lambda m: m.group(0).capitalize(), name.lower())


def parse_card(raw: str) -> Optional[Card]:
    """Return a Card for a valid R'Card swipe, otherwise None."""
    match = _TRACK1.search(raw or "")
    if not match or not match.group("pan").startswith(CARD_PREFIX):
        return None
    disc = match.group("disc").replace(" ", "")
    student_id = disc[SHARED_DIGITS:SHARED_DIGITS + ID_LENGTH]
    if len(student_id) != ID_LENGTH or not student_id.isdigit():
        return None
    return Card(student_id=student_id, name=format_name(match.group("name")))


def fake_swipe(student_id: str = "999999901") -> str:
    """Synthetic swipe for development and tests. Not real card data."""
    return "%B6012000000000000^TESTER/PAT^" + "0" * SHARED_DIGITS + student_id + "0000?"
