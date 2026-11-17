"""Start the kiosk.

    python -m tutoring_kiosk.app
    python -m tutoring_kiosk.app --simulate
"""

from __future__ import annotations

import argparse
import logging
import queue
import tkinter as tk

from .config import load_config
from .flow import Flow
from .outbox import Outbox
from .rcard import fake_swipe, parse_card
from .reader import start_reader
from .sync import start_sync
from .ui import KioskUI


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true", help="no card reader, windowed")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config()
    cfg.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    outbox = Outbox(str(cfg.data_dir / "outbox.db"))
    swipes: queue.Queue = queue.Queue()
    start_sync(outbox, cfg)

    root = tk.Tk()
    if args.simulate:
        root.bind_all("<F2>", lambda _e: swipes.put(parse_card(fake_swipe())))
    else:
        start_reader(cfg.reader_device, swipes)

    KioskUI(root, Flow(outbox.add, cfg.device_id), cfg.courses, swipes,
            fullscreen=not args.simulate)
    root.mainloop()


if __name__ == "__main__":
    main()
