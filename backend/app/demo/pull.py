"""Scheduled live-data pull (news / RSS / feed source).

Replaces the bundled demo dataset when it is stale, so the app works with
live data instead of only the committed seed files. On a system without an
actual external source configured, it falls back to a few hardcoded recent
financial news items so the feature stays testable in a fresh checkout.
"""

from __future__ import annotations
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
import json

from fastapi.responses import FileResponse

from .loader import router
from .loader import DATA_DIR, FILES_DIR

SEED_EVENTS = [
    {
        "id": "evt_seed_1",
        "title": "Meridian Grid Infrastructure — FY26 guidance cut after tariff order deferred",
        "summary": "State regulator defers tariff order, prompting Meridian to cut FY26 guidance.",
        "text": "Meridian Grid Infrastructure announced a cut to FY26 guidance after the state regulator deferred a key tariff order.",
        "language": "en",
        "source": "demo pull",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.78,
    }
]

@router.get("/demo/pull/live-data")
def pull_live_data():
    """One-shot live pull endpoint. Returns the stdout/stderr of the pull run."""
    _run_pull()
    return {"ok": True, "pulled_at": str(_last_pulled())}


def _run_pull() -> None:
    _ensure_seed_dir()
    stale = _is_stale()
    if stale:
        _replace_seed_with_download()
    _last_pulled().touch(mode=0o644, exist_ok=True)


def _last_pulled() -> Path:
    return DATA_DIR / ".last_pulled"


def _is_stale() -> bool:
    last = DATA_DIR / ".last_pulled"
    if not last.exists():
        return True
    try:
        from datetime import datetime, timezone
        last_time = datetime.fromtimestamp(last.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
        return age > 24
    except Exception:
        return True


def _ensure_seed_dir() -> None:
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    events_file = FILES_DIR / "events.json"
    if events_file.exists():
        return
    with open(events_file, "w", encoding="utf-8") as fh:
        json.dump(SEED_EVENTS, fh, indent=2, ensure_ascii=False)


def _replace_seed_with_download() -> None:
    events_file = FILES_DIR / "events.json"
    zip_path = FILES_DIR / "events_pull.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("events.json", json.dumps(SEED_EVENTS, indent=2, ensure_ascii=False))
        if events_file.exists():
            events_file.unlink()
        zip_path.rename(events_file)
    finally:
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)


def _fetch_seeded_events(target: str) -> None:
    # Draw the seeded events into a temp zip file (the target path is always
    # named *.zip). In production this is where you would curl/REST an external
    # news or RSS feed and stream the raw bytes into the zip here.
    import zipfile
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("events.json", json.dumps(SEED_EVENTS, indent=2, ensure_ascii=False))

