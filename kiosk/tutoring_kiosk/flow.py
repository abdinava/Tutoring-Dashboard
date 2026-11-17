"""The check-in steps as a small state machine.

    HOME -> swipe -> CONFIRM -> yes -> CLASSES -> done -> MESSAGE -> HOME
    HOME -> "no card" -> MANUAL -> valid ID -> CLASSES
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional, Set

from .rcard import ID_LENGTH, Card

HOME, CONFIRM, MANUAL, CLASSES, MESSAGE = "home", "confirm", "manual", "classes", "message"


@dataclass
class State:
    screen: str = HOME
    student_id: Optional[str] = None
    name: Optional[str] = None
    method: Optional[str] = None  # "swipe" or "manual"
    selected: Set[str] = field(default_factory=set)
    message: str = ""


class Flow:
    def __init__(self, save: Callable[[List[dict]], None], device_id: str) -> None:
        self.save = save
        self.device_id = device_id
        self.state = State()

    def reset(self) -> None:
        self.state = State()

    def show_message(self, text: str) -> None:
        self.state = State(screen=MESSAGE, message=text)

    def swipe(self, card: Optional[Card]) -> None:
        if self.state.screen != HOME:
            return
        if card is None:
            self.show_message("Card not recognized. Please try again.")
        else:
            self.state = State(CONFIRM, card.student_id, card.name, "swipe")

    def confirm(self, is_me: bool) -> None:
        if self.state.screen != CONFIRM:
            return
        if is_me:
            self.state.screen = CLASSES
        else:
            self.show_message("Please ask a tutor for help.")

    def start_manual(self) -> None:
        if self.state.screen == HOME:
            self.state = State(screen=MANUAL, method="manual")

    def enter_id(self, text: str) -> bool:
        text = text.strip()
        if self.state.screen != MANUAL or len(text) != ID_LENGTH or not text.isdigit():
            return False
        self.state.student_id = text
        self.state.screen = CLASSES
        return True

    def toggle(self, course: str) -> None:
        if self.state.screen == CLASSES:
            self.state.selected ^= {course}

    def finish(self) -> bool:
        if self.state.screen != CLASSES or not self.state.selected:
            return False
        now = datetime.now(timezone.utc).isoformat()
        self.save([
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "tutoring_checkin",
                "method": self.state.method,
                "student_id": self.state.student_id,
                "course": course,
                "timestamp": now,
                "device_id": self.device_id,
            }
            for course in sorted(self.state.selected)
        ])
        self.show_message("You're checked in. Thanks!")
        return True
