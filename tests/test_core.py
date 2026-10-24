import json
import os
import pathlib
import tempfile
import unittest

from agent_replay import build_steps, load_spans, summary, to_html, to_markdown

TRACE = pathlib.Path(__file__).resolve().parent.parent / "examples" / "trace.jsonl"


class Tests(unittest.TestCase):
    def setUp(self):
        self.spans = load_spans(str(TRACE))

    def test_steps_and_retry(self):
        root, steps = build_steps(self.spans)
        self.assertEqual(root["name"], "research-agent")
        self.assertEqual([s["name"] for s in steps], ["plan", "web_search", "fetch_page", "fetch_page", "summarise"])
        self.assertTrue(steps[3]["retry"])

    def test_summary(self):
        sm = summary(*build_steps(self.spans))
        self.assertEqual(sm["errors"], 1)
        self.assertTrue(sm["recovered"])
        self.assertEqual(sm["slowest"][0], "summarise")
        self.assertAlmostEqual(sm["cost_usd"], 0.3458)

    def test_markdown(self):
        md = to_markdown(self.spans)
        self.assertIn("**Goal:** Find 3 competitors", md)
        self.assertIn("after recovering from errors", md)
        self.assertIn("Retried. Called tool `fetch_page`", md)
        self.assertIn("TimeoutError", md)

    def test_html_escapes_and_steps(self):
        spans = [
            *self.spans,
            {
                "trace_id": "t1",
                "span_id": "z",
                "parent_id": "a",
                "name": "<script>x</script>",
                "kind": "step",
                "start": 1043,
                "duration_ms": 1,
                "attrs": {},
                "status": "ok",
            },
        ]
        page = to_html(spans)
        self.assertNotIn("<script>x</script>", page)
        self.assertEqual(page.count('class="step'), 6)

    def test_simple_steps_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "steps.json")
            with open(p, "w") as fh:
                json.dump(
                    [
                        {"name": "open", "kind": "tool", "duration_ms": 500},
                        {"name": "click", "kind": "tool", "duration_ms": 200},
                    ],
                    fh,
                )
            spans = load_spans(p)
            self.assertEqual(len(build_steps(spans)[1]), 2)
            self.assertIn("2 steps", to_markdown(spans))


if __name__ == "__main__":
    unittest.main()
