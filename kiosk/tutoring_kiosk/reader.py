"""Read swipes from the ID Tech TM3 card reader.

The reader acts like a keyboard. We read its Linux input device directly and
"grab" it, so swipes don't type into other windows and no sudo is needed
(see deploy/99-rcard-reader.rules). Swipes are parsed here, so raw card data
never leaves this thread.
"""

from __future__ import annotations

import logging
import queue
import string
import threading
import time

from .rcard import parse_card

log = logging.getLogger(__name__)

KEY_GAP_SECONDS = 1.0  # longer pause between keys = abandoned partial swipe


def _keymap(ecodes) -> dict:
    keys = {}
    for i, d in enumerate("0123456789"):
        keys[getattr(ecodes, "KEY_" + d)] = (d, ")!@#$%^&*("[i])
    for c in string.ascii_lowercase:
        keys[getattr(ecodes, "KEY_" + c.upper())] = (c, c.upper())
    for name, pair in [("SEMICOLON", ";:"), ("SLASH", "/?"), ("EQUAL", "=+"), ("MINUS", "-_"),
                       ("SPACE", "  "), ("APOSTROPHE", "'\""), ("DOT", ".>"), ("COMMA", ",<")]:
        keys[getattr(ecodes, "KEY_" + name)] = (pair[0], pair[1])
    return keys


def read_swipes(device_path: str):
    """Yield one raw string per swipe (blocks). Linux only."""
    from evdev import InputDevice, ecodes

    keys = _keymap(ecodes)
    device = InputDevice(device_path)
    device.grab()
    try:
        buf, shift, last = [], False, 0.0
        for ev in device.read_loop():
            if ev.type != ecodes.EV_KEY:
                continue
            if ev.code in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
                shift = ev.value != 0
                continue
            if ev.value != 1:  # key-down only
                continue
            if buf and ev.timestamp() - last > KEY_GAP_SECONDS:
                buf = []
            last = ev.timestamp()
            if ev.code in (ecodes.KEY_ENTER, ecodes.KEY_KPENTER):
                if buf:
                    yield "".join(buf)
                buf = []
            elif ev.code in keys and len(buf) < 512:
                buf.append(keys[ev.code][1 if shift else 0])
    finally:
        try:
            device.ungrab()
        except OSError:
            pass


def start_reader(device_path: str, out: queue.Queue) -> None:
    """Background thread: puts a Card (or None for an unreadable card) on `out`."""

    def run() -> None:
        while True:
            try:
                for raw in read_swipes(device_path):
                    out.put(parse_card(raw))
            except OSError as exc:
                log.warning("Card reader unavailable (%s); retrying", type(exc).__name__)
            time.sleep(5)

    threading.Thread(target=run, daemon=True, name="reader").start()
