"""Run the published local n8n mock workflow against localhost."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://localhost:5678"
WEBHOOK_URL = f"{BASE_URL}/webhook/production-flow/events-local"


def post(payload: dict) -> tuple[int, dict]:
    request = Request(WEBHOOK_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())
    except URLError as error:
        raise SystemExit(f"n8n is unreachable at {WEBHOOK_URL}: {error.reason}") from error


def main() -> int:
    run_id = str(int(time.time()))
    valid = {"event_id": f"e2e-created-{run_id}", "order_id": f"ORD-E2E-{run_id}", "stage": "order", "event_type": "order_created", "event_timestamp": "2026-10-07T09:00:00Z", "source": "simulated"}
    invalid = {"event_id": f"e2e-invalid-{run_id}", "order_id": f"ORD-E2E-INVALID-{run_id}", "stage": "unknown", "event_type": "stage_entered", "event_timestamp": "not-a-time", "source": "simulated"}
    out_of_order = {"event_id": f"e2e-stage-{run_id}", "order_id": f"ORD-E2E-{run_id}", "stage": "supplier_sourcing", "event_type": "stage_entered", "event_timestamp": "2026-10-07T08:00:00Z", "source": "simulated"}
    cases = [("valid", valid, 200), ("invalid", invalid, 400), ("duplicate", valid, 200), ("out_of_order", out_of_order, 200)]
    failures = []
    for name, payload, expected_status in cases:
        status, body = post(payload)
        print(f"{name}: http={status} body={json.dumps(body, sort_keys=True)}")
        if status != expected_status:
            failures.append(f"{name}: expected HTTP {expected_status}, got {status}")
        if name == "valid" and (body.get("accepted") is not True or body.get("duplicate_delivery") is not False):
            failures.append("valid: expected accepted=true and duplicate_delivery=false")
        if name == "invalid" and (body.get("accepted") is not False or "captured_events" in body):
            failures.append("invalid: expected rejected response without local capture")
        if name == "duplicate" and body.get("duplicate_delivery") is not True:
            failures.append("duplicate: expected duplicate_delivery=true")
        if name == "out_of_order" and body.get("accepted") is not True:
            failures.append("out_of_order: expected event to be retained")
    print("LOCAL N8N E2E: PASS" if not failures else "LOCAL N8N E2E: FAIL")
    for failure in failures:
        print(f"FAILURE: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
