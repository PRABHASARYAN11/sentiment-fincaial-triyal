"""Loader for demo data (seed events + uploads)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import BASE_DIR
from ..api.demo import router

DATA_DIR = BASE_DIR / "data"
FILES_DIR = DATA_DIR / "files"

SEED_EVENTS_PATH = BASE_DIR / "backend" / "app" / "demo" / "events.json"
SEED_DIVERGENCE_PATH = BASE_DIR / "backend" / "demo" / "divergence.json"


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)


def _load_seed_events() -> list[dict[str, Any]]:
    try:
        with open(SEED_EVENTS_PATH, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if isinstance(payload, dict):
            for key in ("events", "data", "items"):
                if isinstance(payload.get(key), list):
                    return payload[key]
            return [payload]
        return payload
    except Exception:
        return []


def _load_seed_divergence() -> dict[str, Any]:
    try:
        with open(SEED_DIVERGENCE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _events() -> list[dict[str, Any]]:
    events = _load_seed_events()
    try:
        events_file = FILES_DIR / "events.json"
        if events_file.exists():
            with open(events_file, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if isinstance(payload, list):
                events.extend(payload)
            elif isinstance(payload, dict):
                for key in ("events", "data", "items"):
                    if isinstance(payload.get(key), list):
                        events.extend(payload[key])
    except Exception:
        pass
    return events


@router.get("/demo/events/seed")
def seed_events():
    return {"events": _load_seed_events()}


@router.get("/demo/divergence/seed")
def seed_divergence():
    return {"divergence": _load_seed_divergence()}


@router.get("/demo/data/events")
def list_events():
    _ensure_dirs()
    events = _events()
    if not events:
        return _load_seed_events()
    return events


@router.get("/demo/data/divergence")
def get_divergence():
    _ensure_dirs()
    return _load_seed_divergence()


@router.get("/demo/data/artifacts")
def artifacts():
    _ensure_dirs()
    return {"uploaded_files": [], "exports": []}


@router.get("/demo/pull/live-data")
def pull_live_data():
    """Trigger the scheduled live-data pull."""
    from .pull import _run_pull, _last_pulled
    import traceback
    import sys

    _run_pull()
    p = _last_pulled()
    print(f"DEBUG: type={type(p)}, repr={repr(p)}", file=sys.stderr)
    result = _last_pulled()
    import sys
    print(f"###UNIQUE_MARKER_12345###", file=sys.stderr)
    print(f"MARKER_TYPE: {type(result)}", file=sys.stderr)
    return {"ok": True, "pulled_at": str(result)}


@router.get("/demo/hello")
def hello():
    return {"message": "SignalRadar demo API is live."}


def map_query(query_text: str, events: list[dict[str, Any]], top_k: int = 5) -> QueryResponse:
    """Naive keyword-overlap query for the UI demo."""
    if not events:
        return QueryResponse(
            answer="No events available.",
            confidence=0.0,
            citations=[],
            related=[],
            sentiment="neutral",
            total_events=0,
        )
    q = query_text.lower()
    scored = []
    for event in events:
        text = (event.get("text") or " " + event.get("title") or " " + event.get("summary") or "")
        score = q.count(" ") + text.lower().count(q[:min(len(q), 6)])
        scored.append((score, event))
    scored.sort(key=lambda x: -x[0])
    top = [e for _, e in scored[:top_k]]
    return QueryResponse(
        answer="Matches found.",
        confidence=float(min(1.0, len(top) * 0.25)),
        citations=[{"id": e.get("id"), "title": e.get("title")} for e in top],
        related=[],
        sentiment="neutral",
        total_events=len(events),
    )
