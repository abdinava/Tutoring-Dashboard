"""Local SQLite queue: check-ins are saved here first, so none are lost offline.

Rows are deleted once the relay accepts them. Rows the relay rejects are kept
as 'rejected' for a person to look at.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from typing import List


class Outbox:
    def __init__(self, path: str) -> None:
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        with self._lock, self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS outbox ("
                " event_id TEXT PRIMARY KEY,"
                " payload TEXT NOT NULL,"
                " status TEXT NOT NULL DEFAULT 'pending')"
            )

    def add(self, events: List[dict]) -> None:
        with self._lock, self._db:
            self._db.executemany(
                "INSERT OR IGNORE INTO outbox (event_id, payload) VALUES (?, ?)",
                [(e["event_id"], json.dumps(e)) for e in events],
            )

    def pending(self) -> List[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT payload FROM outbox WHERE status = 'pending' ORDER BY rowid"
            ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete(self, event_id: str) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM outbox WHERE event_id = ?", (event_id,))

    def reject(self, event_id: str) -> None:
        with self._lock, self._db:
            self._db.execute(
                "UPDATE outbox SET status = 'rejected' WHERE event_id = ?", (event_id,)
            )
