"""Kiosk settings"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    relay_url: str
    device_id: str
    device_token: str
    courses: List[str]
    reader_device: str
    data_dir: Path


def load_config() -> Config:
    load_dotenv()
    env = os.environ

    missing = [k for k in ("RELAY_URL", "DEVICE_ID", "DEVICE_TOKEN", "COURSES") if not env.get(k)]
    if missing:
        raise RuntimeError("Missing settings: " + ", ".join(missing))

    relay_url = env["RELAY_URL"].rstrip("/")
    if not relay_url.startswith("https://") and env.get("ALLOW_INSECURE_RELAY") != "1":
        raise RuntimeError("RELAY_URL must use https://")

    return Config(
        relay_url=relay_url,
        device_id=env["DEVICE_ID"],
        device_token=env["DEVICE_TOKEN"],
        courses=[c.strip() for c in env["COURSES"].split(",") if c.strip()],
        reader_device=env.get("READER_DEVICE", "/dev/rcard-reader"),
        data_dir=Path(os.path.expanduser(env.get("DATA_DIR", "~/.local/share/tutoring-kiosk"))),
    )
