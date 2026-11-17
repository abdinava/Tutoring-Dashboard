"""Background thread that sends queued check-ins to the relay.

Network problems never affect the UI: events wait in the outbox and are
retried. Logs contain event IDs only, never student data.
"""

from __future__ import annotations

import logging
import threading
import time

import requests

from .config import Config
from .outbox import Outbox

log = logging.getLogger(__name__)

RETRY_SECONDS = 10


def send_pending(outbox: Outbox, session: requests.Session, relay_url: str) -> None:
    """Try to send every pending event once. Raises on network/server errors."""
    for event in outbox.pending():
        resp = session.post(relay_url + "/v1/events", json=event, timeout=10)
        if resp.status_code == 202:
            outbox.delete(event["event_id"])
        elif 400 <= resp.status_code < 500 and resp.status_code != 429:
            log.error("Relay rejected event %s (HTTP %s)", event["event_id"], resp.status_code)
            outbox.reject(event["event_id"])
        else:
            resp.raise_for_status()  # 5xx / 429: stop and retry later


def start_sync(outbox: Outbox, cfg: Config) -> None:
    session = requests.Session()
    session.headers.update(
        {"Authorization": "Bearer " + cfg.device_token, "X-Device-ID": cfg.device_id}
    )

    def run() -> None:
        while True:
            try:
                send_pending(outbox, session, cfg.relay_url)
            except requests.RequestException as exc:
                log.warning("Relay unavailable (%s); will retry", type(exc).__name__)
            time.sleep(RETRY_SECONDS)

    threading.Thread(target=run, daemon=True, name="sync").start()
