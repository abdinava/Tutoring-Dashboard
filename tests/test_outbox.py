from tutoring_kiosk.outbox import Outbox
from tutoring_kiosk.sync import send_pending


def event(n):
    return {"event_id": "id-%d" % n, "course": "CS 10A"}


def test_events_survive_restart(tmp_path):
    path = str(tmp_path / "outbox.db")
    Outbox(path).add([event(1), event(2), event(1)])  # duplicate ignored
    assert [e["event_id"] for e in Outbox(path).pending()] == ["id-1", "id-2"]


class FakeSession:
    def __init__(self, status):
        self.status = status

    def post(self, url, json, timeout):
        return type("Resp", (), {"status_code": self.status,
                                 "raise_for_status": lambda self: None})()


def test_accepted_events_are_deleted(tmp_path):
    box = Outbox(str(tmp_path / "o.db"))
    box.add([event(1)])
    send_pending(box, FakeSession(202), "https://relay")
    assert box.pending() == []


def test_rejected_events_are_kept_but_not_retried(tmp_path):
    box = Outbox(str(tmp_path / "o.db"))
    box.add([event(1)])
    send_pending(box, FakeSession(422), "https://relay")
    assert box.pending() == []
    assert box._db.execute("SELECT status FROM outbox").fetchone()[0] == "rejected"


def test_server_errors_keep_events_pending(tmp_path):
    box = Outbox(str(tmp_path / "o.db"))
    box.add([event(1)])
    send_pending(box, FakeSession(503), "https://relay")
    assert len(box.pending()) == 1
