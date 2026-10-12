"""Cloud-free adapters used by the reproducible local test workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

ALLOWED_STAGES = {"order", "supplier_sourcing", "quotation", "sampling", "customer_approval", "production", "fulfillment"}
ALLOWED_TYPES = {"order_created", "stage_entered", "stage_exited", "order_cancelled"}
ALLOWED_PRODUCT_TYPES = {"hoodie", "t_shirt", "tote_bag", "baseball_cap", "sweatshirt", "polo_shirt", "canvas_jacket"}


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode()).hexdigest()


@dataclass
class MockRawEventCapture:
    """In-memory substitute for the raw_events BigQuery insert."""

    rows: list[dict[str, Any]] = field(default_factory=list)
    rejected_rows: list[dict[str, Any]] = field(default_factory=list)

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ("event_id", "order_id", "stage", "event_type", "event_timestamp", "source", "product_id", "product_name", "product_type", "variant", "quantity")
        missing = [key for key in required if not payload.get(key)]
        issues: list[str] = []
        if missing:
            issues.append("missing_fields:" + ",".join(missing))
        if payload.get("stage") not in ALLOWED_STAGES:
            issues.append("invalid_stage")
        if payload.get("event_type") not in ALLOWED_TYPES:
            issues.append("invalid_event_type")
        if payload.get("product_type") not in ALLOWED_PRODUCT_TYPES:
            issues.append("invalid_product_type")
        if payload.get("quantity", 0) <= 0:
            issues.append("invalid_quantity")
        try:
            timestamp = datetime.fromisoformat(str(payload.get("event_timestamp", "")).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError
            timestamp = timestamp.astimezone(timezone.utc)
        except ValueError:
            issues.append("invalid_timestamp")
            timestamp = None

        row = dict(payload)
        row["event_timestamp"] = timestamp.isoformat().replace("+00:00", "Z") if timestamp else payload.get("event_timestamp")
        row["ingested_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        row["payload_hash"] = payload.get("payload_hash") or _hash_payload(payload)
        row["validation_status"] = "rejected" if issues else "pending_state_machine"
        if issues:
            self.rejected_rows.append({
                "quarantine_id": f"quarantine:{payload.get('event_id') or len(self.rejected_rows) + 1}",
                "event_id": payload.get("event_id"),
                "order_id": payload.get("order_id"),
                "raw_payload": dict(payload),
                "issue_codes": issues,
                "validation_status": "rejected",
                "received_at": row["ingested_at"],
            })
        else:
            self.rows.append(row)
        return {"accepted": not issues, "issues": issues, "event_id": payload.get("event_id"), "row": row}


@dataclass
class MockBigQueryDelaySource:
    """Fixed response used instead of querying v_delayed_orders."""

    rows: list[dict[str, Any]]

    def query_delayed_orders(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]


def mock_gemini_response(question: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic grounded response; no network call and no model claim."""

    stages: dict[str, int] = {}
    for row in rows:
        stages[row["stage"]] = stages.get(row["stage"], 0) + 1
    return {
        "mode": "mock",
        "question": question,
        "simulated_data": True,
        "result": {"delayed_order_count": len(rows), "delays_by_stage": stages, "orders": rows},
    }
