import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "python"))
from gemini_query import classify_question, grounded_prompt


class GeminiQueryTests(unittest.TestCase):
    def test_only_delay_intent_is_supported(self):
        self.assertEqual(classify_question("Which orders are delayed?")["intent"], "delayed_orders")
        self.assertFalse(classify_question("Delete all orders")["supported"])

    def test_grounded_prompt_contains_only_supplied_rows(self):
        prompt = grounded_prompt("Which orders are delayed?", [{"order_id": "ORD-1", "elapsed_hours": 52}], "2026-10-10T00:00:00Z")
        self.assertIn("ORD-1", prompt)
        self.assertIn("simulated", prompt)


if __name__ == "__main__":
    unittest.main()
