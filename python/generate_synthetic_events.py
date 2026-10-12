"""Generate deterministic simulated workflow events for local tests and demos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

UTC = timezone.utc
STAGES = ["supplier_sourcing", "quotation", "sampling", "customer_approval", "production", "fulfillment"]
PRODUCTS = {
    "ORD-1001": {"product_id": "PROD-HOODIE-001", "product_name": "Custom branded hoodie", "product_type": "hoodie", "variant": "Black fleece, size L", "quantity": 24},
    "ORD-1002": {"product_id": "PROD-TSHIRT-001", "product_name": "Embroidered T-shirt", "product_type": "t_shirt", "variant": "White cotton, size M", "quantity": 48},
    "ORD-1003": {"product_id": "PROD-TOTE-001", "product_name": "Branded tote bag", "product_type": "tote_bag", "variant": "Natural canvas, one size", "quantity": 60},
    "ORD-1004": {"product_id": "PROD-CAP-001", "product_name": "Custom baseball cap", "product_type": "baseball_cap", "variant": "Black cotton twill, adjustable", "quantity": 36},
    "ORD-1005": {"product_id": "PROD-SWEAT-001", "product_name": "Custom sweatshirt", "product_type": "sweatshirt", "variant": "Grey fleece, size XL", "quantity": 20},
    "ORD-1006": {"product_id": "PROD-POLO-001", "product_name": "Branded polo shirt", "product_type": "polo_shirt", "variant": "Navy piqué, size L", "quantity": 30},
    "ORD-1007": {"product_id": "PROD-JACKET-001", "product_name": "Canvas jacket", "product_type": "canvas_jacket", "variant": "Olive canvas, size M", "quantity": 12},
}


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def event(event_id, order_id, stage, event_type, timestamp, supplier_id="SUP-001"):
    payload = {
        "event_id": event_id,
        "order_id": order_id,
        "stage": stage,
        "event_type": event_type,
        "event_timestamp": iso(timestamp),
        "supplier_id": supplier_id,
        "source": "simulated",
    }
    payload.update(PRODUCTS[order_id])
    payload["payload_hash"] = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return payload


def fixtures() -> dict[str, list[dict]]:
    # Fixed historical date keeps the delayed fixture beyond the 48-hour
    # threshold while preserving deterministic replay across machines.
    base = datetime(2026, 10, 7, 9, tzinfo=UTC)
    normal = [event("evt-normal-created", "ORD-1001", "order", "order_created", base)]
    for index, stage in enumerate(STAGES):
        start = base + timedelta(hours=index * 12)
        normal.extend([
            event(f"evt-normal-{stage}-in", "ORD-1001", stage, "stage_entered", start),
            event(f"evt-normal-{stage}-out", "ORD-1001", stage, "stage_exited", start + timedelta(hours=6)),
        ])

    delayed = [
        event("evt-delay-created", "ORD-1002", "order", "order_created", base),
        event("evt-delay-source-in", "ORD-1002", "supplier_sourcing", "stage_entered", base + timedelta(hours=1)),
        event("evt-delay-source-out", "ORD-1002", "supplier_sourcing", "stage_exited", base + timedelta(hours=8)),
        event("evt-delay-quotation-in", "ORD-1002", "quotation", "stage_entered", base + timedelta(hours=9)),
        event("evt-delay-quotation-out", "ORD-1002", "quotation", "stage_exited", base + timedelta(hours=10)),
        event("evt-delay-sampling-in", "ORD-1002", "sampling", "stage_entered", base + timedelta(hours=11)),
    ]
    return {
        "normal": normal,
        "delayed": delayed,
        "duplicate_entry": [
            event("evt-dup-created", "ORD-1003", "order", "order_created", base),
            event("evt-dup-in-1", "ORD-1003", "supplier_sourcing", "stage_entered", base + timedelta(hours=1)),
            event("evt-dup-in-2", "ORD-1003", "supplier_sourcing", "stage_entered", base + timedelta(hours=1)),
        ],
        "pre_creation": [
            event("evt-pending-in", "ORD-1004", "supplier_sourcing", "stage_entered", base),
            event("evt-pending-created", "ORD-1004", "order", "order_created", base + timedelta(hours=1)),
        ],
        "invalid_then_valid": [
            event("evt-state-created", "ORD-1005", "order", "order_created", base),
            event("evt-state-invalid", "ORD-1005", "production", "stage_entered", base + timedelta(hours=1)),
            event("evt-state-valid", "ORD-1005", "supplier_sourcing", "stage_entered", base + timedelta(hours=2)),
        ],
        "orphan_exit": [
            event("evt-orphan-created", "ORD-1006", "order", "order_created", base),
            event("evt-orphan-exit", "ORD-1006", "quotation", "stage_exited", base + timedelta(hours=1)),
        ],
        "conflicting_id": [
            event("evt-conflict-created", "ORD-1007", "order", "order_created", base),
            event("evt-conflict", "ORD-1007", "supplier_sourcing", "stage_entered", base + timedelta(hours=1)),
            {**event("evt-conflict", "ORD-1007", "production", "stage_entered", base + timedelta(hours=2)), "payload_hash": "conflicting"},
        ],
    }


def write_json(path: str | Path) -> None:
    Path(path).write_text(json.dumps(fixtures(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_json(Path(__file__).parent / "fixtures.json")
