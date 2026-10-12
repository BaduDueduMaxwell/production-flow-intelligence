"""Grounded Gemini query adapter for the single Milestone A intent.

This module is intentionally not executed without an explicitly supplied API key.
It never accepts arbitrary SQL from the model.
"""

from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

ALLOWED_INTENT = "delayed_orders"
QUERY = """SELECT order_id, stage, elapsed_hours, threshold_hours
FROM `PROJECT.DATASET.v_delayed_orders`
ORDER BY elapsed_hours DESC
LIMIT 100"""


def classify_question(question: str) -> dict:
    text = question.lower()
    if "delay" in text or "stuck" in text or "bottleneck" in text:
        return {"intent": ALLOWED_INTENT, "supported": True}
    return {"intent": None, "supported": False}


def grounded_prompt(question: str, rows: list[dict], data_as_of: str) -> str:
    return json.dumps({
        "question": question,
        "data_as_of": data_as_of,
        "rows": rows,
        "instruction": "Summarize only the supplied rows. Do not invent metrics or records. State that data is simulated.",
    })


def call_gemini(prompt: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set; external Gemini execution is intentionally disabled.")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    request = Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + api_key,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read())
