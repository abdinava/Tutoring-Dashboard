"""Relay API.

POST /v1/events  kiosk sends a check-in (requires device token)
GET  /healthz    uptime check
"""

import logging

import httpx
from fastapi import Depends, FastAPI, HTTPException

from .auth import authenticate_device
from .config import Settings, get_settings
from .models import CheckinEvent
from .qualtrics import send_to_qualtrics

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("relay")

# No public API docs: only kiosks use this service.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.post("/v1/events", status_code=202)
async def receive_event(
    event: CheckinEvent,
    device_id: str = Depends(authenticate_device),
    settings: Settings = Depends(get_settings),
) -> dict:
    if event.device_id != device_id:
        raise HTTPException(403, "device_id does not match credentials")
    if event.course not in settings.allowed_courses:
        raise HTTPException(422, "unknown course")

    values = event.model_dump(mode="json")
    try:
        await send_to_qualtrics(settings, values)
    except httpx.HTTPError as exc:
        log.warning("Qualtrics failed for event %s: %s", event.event_id, type(exc).__name__)
        raise HTTPException(503, "Qualtrics unavailable, retry later") from exc

    log.info("Forwarded event %s from %s", event.event_id, device_id)  # no student data
    return {"event_id": str(event.event_id)}
