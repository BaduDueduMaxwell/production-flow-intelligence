import json
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parents[1] / "python"))
from quality_summary import elapsed_hours, summarize


class QualityContractTests(unittest.TestCase):
    def test_summary_counts_reconcile_to_detail_records(self):
        records = [
            {"record_origin": "raw_events", "stage": "sampling", "quality_issue": None},
            {"record_origin": "raw_events", "stage": "sampling", "quality_issue": "invalid_transition"},
            {"record_origin": "rejected_events", "stage": None, "quality_issue": "invalid_timestamp"},
        ]
        summary = summarize(records)
        self.assertEqual(sum(row["record_count"] for row in summary), len(records))

    def test_missing_completion_is_unavailable_not_zero(self):
        now = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
        record = {"stage_entered_at": datetime(2026, 10, 10, 12, tzinfo=timezone.utc), "stage_exited_at": None}
        self.assertEqual(elapsed_hours(record, now), 48)
        self.assertIsNone(elapsed_hours({"stage_entered_at": None}, now))
        self.assertIsNone(elapsed_hours({"stage_entered_at": record["stage_entered_at"], "stage_exited_at": now}, now))

    def test_workflow_contains_quarantine_branch(self):
        workflow = json.loads((Path(__file__).parents[1] / "n8n/workflows/ingest-events.json").read_text())
        names = {node["name"] for node in workflow["nodes"]}
        self.assertIn("Quarantine rejected event", names)
        self.assertIn("Rejected response", names)
        self.assertIn("Quarantine rejected event", workflow["connections"]["Valid event?"]["main"][1][0]["node"])


if __name__ == "__main__":
    unittest.main()
