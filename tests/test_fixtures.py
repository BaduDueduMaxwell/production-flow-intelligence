import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "python"))
from generate_synthetic_events import fixtures


class FixtureTests(unittest.TestCase):
    def test_fixtures_are_deterministic_and_simulated(self):
        first = fixtures()
        second = fixtures()
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first), 6)
        self.assertTrue(all(event["source"] == "simulated" for rows in first.values() for event in rows))

    def test_required_cases_exist(self):
        data = fixtures()
        for name in ("normal", "delayed", "duplicate_entry", "pre_creation", "invalid_then_valid", "orphan_exit", "conflicting_id"):
            self.assertIn(name, data)

    def test_delayed_fixture_reaches_an_open_sampling_stage(self):
        delayed = fixtures()["delayed"]
        self.assertEqual(delayed[-1]["stage"], "sampling")
        self.assertEqual(delayed[-1]["event_type"], "stage_entered")

    def test_fashion_product_metadata_covers_existing_orders(self):
        data = fixtures()
        orders = {event["order_id"] for rows in data.values() for event in rows}
        self.assertEqual(orders, {f"ORD-{1000 + index}" for index in range(1, 8)})
        for rows in data.values():
            for event in rows:
                self.assertTrue(event["product_id"].startswith("PROD-"))
                self.assertTrue(event["product_name"])
                self.assertTrue(event["product_type"])
                self.assertTrue(event["variant"])
                self.assertGreater(event["quantity"], 0)


if __name__ == "__main__":
    unittest.main()
