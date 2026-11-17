"""What a valid check-in looks like. Anything else is rejected (HTTP 422)."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class CheckinEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: Literal["tutoring_checkin"]  # later: "ai_tutor_session", ...
    method: Literal["swipe", "manual"]
    student_id: str = Field(pattern=r"^\d{9}$")
    course: str = Field(max_length=32)
    timestamp: AwareDatetime  # must include a time zone
    device_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
