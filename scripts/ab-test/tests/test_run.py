import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run


class RunTest(unittest.TestCase):
    def test_parse_claude_version(self):
        self.assertEqual(run._parse_claude_version("2.1.132 (Claude Code)"), (2, 1, 132))
        self.assertIsNone(run._parse_claude_version("Claude Code dev build"))

    def test_check_claude_version_rejects_old_cli(self):
        completed = subprocess.CompletedProcess(
            args=["claude", "--version"],
            returncode=0,
            stdout="2.1.131 (Claude Code)\n",
            stderr="",
        )
        with mock.patch("run.subprocess.run", return_value=completed):
            with self.assertRaises(SystemExit) as cm:
                run._check_claude_version("claude")

        self.assertIn("2.1.132", str(cm.exception))

    def test_check_claude_version_accepts_minimum_cli(self):
        completed = subprocess.CompletedProcess(
            args=["claude", "--version"],
            returncode=0,
            stdout="2.1.132 (Claude Code)\n",
            stderr="",
        )
        with mock.patch("run.subprocess.run", return_value=completed):
            run._check_claude_version("claude")

    def test_filter_reports_actual_flag_name_for_missing_ids(self):
        with self.assertRaises(SystemExit) as cm:
            run._filter(
                [{"id": "current"}],
                ids=["missing"],
                key="id",
                flag_name="variants",
            )

        self.assertIn("--variants", str(cm.exception))
        self.assertNotIn("--ids", str(cm.exception))

    def test_build_cells_interleaves_variants_within_each_prompt_model_rep(self):
        variants = [
            {"id": "current", "description": "baseline"},
            {"id": "a", "description": "candidate"},
        ]
        prompts = [
            {"id": "feature", "text": "feature prompt"},
            {"id": "bug", "text": "bug prompt"},
        ]

        cells = run._build_cells(variants, prompts, models=["haiku"], n=1)

        self.assertEqual(
            [(c["prompt_id"], c["variant_id"]) for c in cells],
            [
                ("feature", "current"),
                ("feature", "a"),
                ("bug", "current"),
                ("bug", "a"),
            ],
        )

    def test_stderr_excerpt_uses_tail(self):
        stderr = "head-" + ("x" * 600) + "-tail"
        self.assertEqual(run._stderr_excerpt(stderr), stderr[-500:])
        self.assertTrue(run._stderr_excerpt(stderr).endswith("-tail"))

    def test_record_for_cell_includes_rate_limit_status(self):
        cell = {
            "variant_id": "current",
            "prompt_id": "feature",
            "model": "haiku",
            "rep": 0,
            "prompt_text": "prompt",
        }
        with (
            mock.patch(
                "run.run_cell",
                return_value={
                    "returncode": 1,
                    "stdout_lines": [
                        '{"type":"rate_limit_event","rate_limit_info":{"status":"rejected"}}'
                    ],
                    "stderr": "",
                },
            ),
            mock.patch(
                "run.analyze_stream",
                return_value={
                    "harness_validated": True,
                    "first_tool_call": None,
                    "first_tool_skill_name": None,
                    "first_tool_call_block_index": None,
                    "activated": False,
                },
            ),
            mock.patch(
                "run.extract_usage",
                return_value={
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                    "duration_ms": 12,
                    "total_cost_usd": 0,
                },
            ),
        ):
            record = run._record_for_cell(
                cell=cell,
                target_plugin="superpowers-beads",
                target_skill="using-superpowers",
                plugin_dir=Path("/tmp/plugin"),
                claude_path="claude",
                timeout_seconds=180,
            )

        self.assertEqual(record["rate_limit_status"], "rejected")

    def test_print_preflight_shows_variant_descriptions_and_token_estimate(self):
        cells = [{"variant_id": "current"}, {"variant_id": "a"}]
        variants = [
            {
                "id": "current",
                "description": "The current baseline description",
            },
            {
                "id": "a",
                "description": "A candidate description that is deliberately long enough to truncate in preflight output",
            },
        ]
        prompts = [{"id": "feature"}]
        buf = io.StringIO()

        with redirect_stdout(buf):
            run._print_preflight(
                cells=cells,
                variants=variants,
                prompts=prompts,
                models=["haiku"],
                n=1,
                output=Path("/tmp/out.jsonl"),
                concurrency=4,
                yes=False,
            )

        output = buf.getvalue()
        self.assertIn("current: The current baseline description", output)
        self.assertIn("a: A candidate description", output)
        self.assertIn("estimated input tokens", output)
        self.assertIn("20,000", output)


if __name__ == "__main__":
    unittest.main()
