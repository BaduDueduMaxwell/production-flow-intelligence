import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "python"))
sys.path.insert(0, str(Path(__file__).parent))

from generate_synthetic_events import fixtures
from local_test_mode import MockBigQueryDelaySource, MockRawEventCapture, mock_gemini_response
from test_state_machine import classify


class LocalE2ETests(unittest.TestCase):
    def test_ingestion_accepts_valid_and_captures_duplicates_and_out_of_order(self):
        capture = MockRawEventCapture()
        events = fixtures()["normal"]
        results = [capture.ingest(event) for event in reversed(events[:4])]
        results.append(capture.ingest(events[2]))
        self.assertTrue(all(result["accepted"] for result in results))
        self.assertEqual(len(capture.rows), 5)
        accepted, issues = classify(capture.rows)
        self.assertGreaterEqual(len(accepted), 3)
        self.assertTrue(any(issue[1] in {"duplicate_event", "pending_order_creation"} for issue in issues))

    def test_invalid_event_is_captured_and_rejected(self):
        capture = MockRawEventCapture()
        result = capture.ingest({"event_id": "bad-1", "order_id": "ORD-BAD", "stage": "unknown", "event_type": "stage_entered", "event_timestamp": "not-a-time", "source": "simulated"})
        self.assertFalse(result["accepted"])
        self.assertEqual(result["row"]["validation_status"], "rejected")
        self.assertEqual(len(capture.rows), 0)
        self.assertEqual(len(capture.rejected_rows), 1)
        self.assertEqual(capture.rejected_rows[0]["raw_payload"]["stage"], "unknown")
        self.assertIn("invalid_timestamp", capture.rejected_rows[0]["issue_codes"])

    def test_invalid_product_metadata_is_quarantined(self):
        capture = MockRawEventCapture()
        payload = fixtures()["normal"][0].copy()
        payload.update({"product_name": "", "product_type": "unknown", "quantity": 0})
        result = capture.ingest(payload)
        self.assertFalse(result["accepted"])
        self.assertTrue(any(issue.startswith("missing_fields:product_name") for issue in result["issues"]))
        self.assertIn("invalid_product_type", result["issues"])
        self.assertIn("invalid_quantity", result["issues"])
        self.assertEqual(len(capture.rejected_rows), 1)

    def test_mock_delay_query_and_gemini_response_are_grounded(self):
        rows = [{"order_id": "ORD-1002", "stage": "sampling", "elapsed_hours": 67, "threshold_hours": 48, "alert_key": "ORD-1002:sampling:stage_delay"}]
        delayed = MockBigQueryDelaySource(rows).query_delayed_orders()
        response = mock_gemini_response("Which orders are delayed?", delayed)
        self.assertEqual(response["result"]["delayed_order_count"], 1)
        self.assertEqual(response["result"]["delays_by_stage"], {"sampling": 1})
        self.assertTrue(response["simulated_data"])


if __name__ == "__main__":
    unittest.main()
