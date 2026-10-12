import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "python"))
from generate_synthetic_events import fixtures


STAGES = ["supplier_sourcing", "quotation", "sampling", "customer_approval", "production", "fulfillment"]


def classify(events):
    rank = {"order_created": 0, "stage_entered": 1, "stage_exited": 2, "order_cancelled": 3}
    ordered = sorted(events, key=lambda e: (e["event_timestamp"], rank[e["event_type"]], e["event_id"], e["payload_hash"]))
    by_id = {}
    conflicting = set()
    for item in ordered:
        prior = by_id.get(item["event_id"])
        if prior and prior["payload_hash"] != item["payload_hash"]:
            conflicting.add(item["event_id"])
        else:
            by_id[item["event_id"]] = item

    if not ordered:
        return [], []
    creation = [e for e in ordered if e["event_type"] == "order_created"]
    if not creation:
        return [], [(e["event_id"], "pending_order_creation") for e in ordered]
    created_at = min(e["event_timestamp"] for e in creation)
    accepted = []
    issues = []
    state = "order_created"
    open_stage = None
    seen = set()
    for e in ordered:
        eid = e["event_id"]
        if eid in conflicting:
            issues.append((eid, "conflicting_event_id")); continue
        if eid in seen:
            issues.append((eid, "duplicate_event")); continue
        seen.add(eid)
        if e["event_timestamp"] < created_at:
            issues.append((eid, "pending_order_creation")); continue
        typ = e["event_type"]
        stage = e["stage"]
        if typ == "order_created":
            if accepted:
                issues.append((eid, "duplicate_order_created"))
            else:
                accepted.append(e)
            continue
        if typ == "stage_entered":
            expected = STAGES[0] if state == "order_created" else STAGES[STAGES.index(state) + 1] if state in STAGES and not open_stage else None
            if open_stage == stage:
                issues.append((eid, "duplicate_event")); continue
            if open_stage or expected != stage:
                issues.append((eid, "invalid_transition")); continue
            open_stage = stage; accepted.append(e); continue
        if typ == "stage_exited":
            if open_stage != stage:
                issues.append((eid, "orphan_exit")); continue
            open_stage = None; state = stage; accepted.append(e); continue
        issues.append((eid, "invalid_event"))
    return accepted, issues


class StateMachineTests(unittest.TestCase):
    def test_pre_creation_event_is_retained_for_reconciliation(self):
        accepted, issues = classify(fixtures()["pre_creation"])
        self.assertEqual([e["event_id"] for e in accepted], ["evt-pending-created"])
        self.assertIn(("evt-pending-in", "pending_order_creation"), issues)

    def test_invalid_transition_does_not_block_later_valid_transition(self):
        accepted, issues = classify(fixtures()["invalid_then_valid"])
        self.assertEqual([e["event_id"] for e in accepted], ["evt-state-created", "evt-state-valid"])
        self.assertIn(("evt-state-invalid", "invalid_transition"), issues)

    def test_duplicate_entry_accepts_one(self):
        accepted, issues = classify(fixtures()["duplicate_entry"])
        self.assertEqual([e["event_id"] for e in accepted], ["evt-dup-created", "evt-dup-in-1"])
        self.assertIn(("evt-dup-in-2", "duplicate_event"), issues)

    def test_orphan_exit_is_quarantined(self):
        accepted, issues = classify(fixtures()["orphan_exit"])
        self.assertEqual([e["event_id"] for e in accepted], ["evt-orphan-created"])
        self.assertIn(("evt-orphan-exit", "orphan_exit"), issues)

    def test_conflicting_event_id_is_quarantined(self):
        accepted, issues = classify(fixtures()["conflicting_id"])
        self.assertEqual([e["event_id"] for e in accepted], ["evt-conflict-created"])
        self.assertIn(("evt-conflict", "conflicting_event_id"), issues)


if __name__ == "__main__":
    unittest.main()
