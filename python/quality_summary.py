"""Deterministic local quality summary used by tests and reviewer demos."""

from __future__ import annotations

from collections import Counter
from typing import Any


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group quality detail records by origin, stage, and quality status."""
    counts = Counter(
        (
            record.get("record_origin", "unknown"),
            record.get("stage") or "unknown",
            record.get("quality_issue") or "valid_or_pending",
        )
        for record in records
    )
    return [
        {
            "record_origin": origin,
            "stage": stage,
            "quality_status": status,
            "record_count": count,
        }
        for (origin, stage, status), count in sorted(counts.items())
    ]


def elapsed_hours(record: dict[str, Any], now: Any) -> int | None:
    """Return elapsed hours only when a valid stage start exists and completion is absent."""
    entered = record.get("stage_entered_at")
    if not entered:
        return None
    if record.get("stage_exited_at"):
        return None
    return int((now - entered).total_seconds() // 3600)
