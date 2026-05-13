import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from report import format_summary, summarize


def make_row(variant, model, activated, prompt="p1", rep=0):
    return {
        "variant_id": variant,
        "model": model,
        "prompt_id": prompt,
        "rep": rep,
        "activated": activated,
        "harness_validated": True,
        "first_tool_call": "Skill" if activated else "Bash",
        "first_tool_skill_name": (
            "superpowers-beads:using-superpowers" if activated else None
        ),
        "input_tokens": 10,
        "output_tokens": 5,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
        "duration_ms": 1000,
        "rate_limit_status": None,
    }


class SummarizeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ab-test-report-"))
        self.path = self.tmp / "results.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_rows(self, rows):
        self.path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def test_summarize_groups_by_variant_and_model(self):
        rows = [
            make_row("current", "sonnet", activated=True),
            make_row("current", "sonnet", activated=False),
            make_row("current", "opus", activated=True),
            make_row("a", "sonnet", activated=True),
            make_row("a", "sonnet", activated=True),
        ]
        self.write_rows(rows)
        cells = summarize(self.path)

        by_key = {(c["variant_id"], c["model"]): c for c in cells}
        self.assertEqual(by_key[("current", "sonnet")]["n"], 2)
        self.assertEqual(by_key[("current", "sonnet")]["activations"], 1)
        self.assertEqual(by_key[("current", "sonnet")]["activation_rate"], 0.5)
        self.assertEqual(by_key[("current", "opus")]["n"], 1)
        self.assertEqual(by_key[("current", "opus")]["activation_rate"], 1.0)
        self.assertEqual(by_key[("a", "sonnet")]["n"], 2)
        self.assertEqual(by_key[("a", "sonnet")]["activation_rate"], 1.0)

    def test_summarize_skips_blank_lines(self):
        rows = [
            make_row("current", "sonnet", activated=True),
            make_row("current", "sonnet", activated=False),
        ]
        self.path.write_text(
            "\n" + json.dumps(rows[0]) + "\n\n" + json.dumps(rows[1]) + "\n\n"
        )
        cells = summarize(self.path)
        self.assertEqual(cells[0]["n"], 2)

    def test_format_summary_renders_table_with_rates(self):
        rows = [
            make_row("current", "sonnet", activated=False),
            make_row("current", "sonnet", activated=False),
            make_row("a", "sonnet", activated=True),
            make_row("a", "sonnet", activated=False),
        ]
        self.write_rows(rows)
        cells = summarize(self.path)
        text = format_summary(cells)

        self.assertIn("variant", text.lower())
        self.assertIn("model", text.lower())
        self.assertIn("current", text)
        self.assertIn("a", text)
        self.assertIn("0/2", text)
        self.assertIn("1/2", text)

    def test_summarize_excludes_unvalidated_runs(self):
        bad = make_row("current", "sonnet", activated=True)
        bad["harness_validated"] = False
        rows = [bad, make_row("current", "sonnet", activated=False)]
        self.write_rows(rows)
        cells = summarize(self.path)
        self.assertEqual(cells[0]["n"], 1)
        self.assertEqual(cells[0]["activations"], 0)
        self.assertEqual(cells[0]["excluded_unvalidated"], 1)

    def test_summarize_counts_rate_limited_runs(self):
        limited = make_row("current", "sonnet", activated=False)
        limited["rate_limit_status"] = "rejected"
        rows = [limited, make_row("current", "sonnet", activated=False)]
        self.write_rows(rows)
        cells = summarize(self.path)

        self.assertEqual(cells[0]["rate_limited"], 1)
        self.assertIn("rate_limited", format_summary(cells))

    def test_summarize_does_not_count_allowed_rate_limit_status(self):
        allowed = make_row("current", "sonnet", activated=False)
        allowed["rate_limit_status"] = "allowed"
        rows = [allowed, make_row("current", "sonnet", activated=False)]
        self.write_rows(rows)
        cells = summarize(self.path)

        self.assertEqual(cells[0]["rate_limited"], 0)

    def test_summarize_skips_rate_limit_casualty_rows(self):
        casualty = make_row("current", "sonnet", activated=False)
        casualty["rate_limited_failure"] = "rate_limit_event status=rejected"
        rows = [casualty, make_row("current", "sonnet", activated=True)]
        self.write_rows(rows)
        cells = summarize(self.path)

        self.assertEqual(cells[0]["n"], 1)
        self.assertEqual(cells[0]["activations"], 1)

    def test_summarize_merges_multiple_files(self):
        first = self.tmp / "run-1.jsonl"
        second = self.tmp / "run-2.jsonl"
        first.write_text(
            "\n".join(
                json.dumps(r)
                for r in [
                    make_row("current", "sonnet", activated=True, prompt="p1"),
                    make_row("current", "sonnet", activated=False, prompt="p2"),
                ]
            )
            + "\n"
        )
        second.write_text(
            json.dumps(make_row("current", "sonnet", activated=True, prompt="p3"))
            + "\n"
        )
        cells = summarize([first, second])

        by_key = {(c["variant_id"], c["model"]): c for c in cells}
        self.assertEqual(by_key[("current", "sonnet")]["n"], 3)
        self.assertEqual(by_key[("current", "sonnet")]["activations"], 2)


if __name__ == "__main__":
    unittest.main()
