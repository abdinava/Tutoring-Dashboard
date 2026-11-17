import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.auth import hash_token
from app.config import Settings, get_settings
from app.main import app

TOKEN = "test-token"
HEADERS = {"Authorization": "Bearer " + TOKEN, "X-Device-ID": "ula-pi-01"}

app.dependency_overrides[get_settings] = lambda: Settings(
    allowed_courses=["CS 10A"],
    device_token_hashes={"ula-pi-01": hash_token(TOKEN)},
    dry_run=True,
)
client = TestClient(app)


def event(**changes):
    e = {
        "event_id": str(uuid.uuid4()), "event_type": "tutoring_checkin", "method": "swipe",
        "student_id": "999999901", "course": "CS 10A",
        "timestamp": datetime.now(timezone.utc).isoformat(), "device_id": "ula-pi-01",
    }
    e.update(changes)
    return e


def test_accepts_valid_event():
    assert client.post("/v1/events", json=event(), headers=HEADERS).status_code == 202


@pytest.mark.parametrize("headers", [
    {},
    {"Authorization": "Bearer wrong", "X-Device-ID": "ula-pi-01"},
    {"Authorization": "Bearer " + TOKEN, "X-Device-ID": "unknown-pi"},
])
def test_rejects_bad_credentials(headers):
    assert client.post("/v1/events", json=event(), headers=headers).status_code == 401


def test_rejects_spoofed_device():
    r = client.post("/v1/events", json=event(device_id="other-pi"), headers=HEADERS)
    assert r.status_code == 403


@pytest.mark.parametrize("bad", [
    {"course": "FAKE 101"},
    {"student_id": "123"},
    {"method": "other"},
    {"timestamp": "2026-11-11T10:00:00"},  # no time zone
    {"extra_field": "x"},
])
def test_rejects_invalid_events(bad):
    assert client.post("/v1/events", json=event(**bad), headers=HEADERS).status_code == 422
