"""Send one check-in to Qualtrics as a survey response.

Uses "Create a New Response". The keys in `values` are Embedded Data fields
that must exist in the survey flow. The event_id is sent as Idempotency-Key,
so a retried event never creates a duplicate response.
"""

import logging

import httpx

from .config import Settings

log = logging.getLogger(__name__)


async def send_to_qualtrics(settings: Settings, values: dict) -> None:
    """Raises httpx.HTTPError if Qualtrics is unreachable or returns an error."""
    if settings.dry_run:
        log.info("[dry run] event %s not sent", values["event_id"])
        return
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.qualtrics_base_url}/surveys/{settings.qualtrics_survey_id}/responses",
            headers={
                "X-API-TOKEN": settings.qualtrics_api_token.get_secret_value(),
                "Idempotency-Key": values["event_id"],
            },
            json={"values": values},
        )
        resp.raise_for_status()
