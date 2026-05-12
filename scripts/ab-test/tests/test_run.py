import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run


class RunTest(unittest.TestCase):
    def test_parse_claude_version(self):
        self.assertEqual(
            run._parse_claude_version("2.1.132 (Claude Code)"),
            (2, 1, 132),
        )
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
        self.assertTrue(record["rate_limited_failure"])

    def test_completed_cell_keys_excludes_rate_limit_casualties(self):
        tmp = Path(tempfile.mkdtemp(prefix="ab-test-resume-"))
        try:
            path = tmp / "run.jsonl"
            done = {
                "variant_id": "current",
                "prompt_id": "feature",
                "model": "sonnet",
                "rep": 0,
                "rate_limited_failure": None,
            }
            casualty = {
                "variant_id": "a",
                "prompt_id": "feature",
                "model": "sonnet",
                "rep": 0,
                "rate_limited_failure": "rate_limit_event status=rejected",
            }
            path.write_text(json.dumps(done) + "\n" + json.dumps(casualty) + "\n")
            keys = run._completed_cell_keys([path])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        self.assertIn(("current", "feature", "sonnet", 0), keys)
        self.assertNotIn(("a", "feature", "sonnet", 0), keys)

    def test_cell_key_matches_for_cells_and_rows(self):
        cell = run._build_cells(
            [{"id": "current", "description": "x"}],
            [{"id": "feature", "text": "p"}],
            models=["sonnet"],
            n=1,
        )[0]
        self.assertEqual(run._cell_key(cell), ("current", "feature", "sonnet", 0))

    def test_resume_command_includes_resume_files_and_yes(self):
        args = argparse.Namespace(
            harness="claude",
            variants="current,a",
            prompts=None,
            models=["claude-sonnet-4-6"],
            n=10,
            concurrency=2,
            target_plugin="superpowers-beads",
            target_skill="using-superpowers",
            cell_timeout=180,
            claude="claude",
            codex="codex",
            resume=[Path("results/run-1.jsonl")],
        )
        cmd = run._resume_command(args, Path("results/run-2.jsonl"))
        self.assertIn("--resume results/run-1.jsonl", cmd)
        self.assertIn("--resume results/run-2.jsonl", cmd)
        self.assertIn("--variants current,a", cmd)
        self.assertIn("--n 10", cmd)
        self.assertIn("--concurrency 2", cmd)
        self.assertTrue(cmd.strip().endswith("--yes"))

    def test_print_preflight_shows_resume_info(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            run._print_preflight(
                cells=[{"variant_id": "a"}],
                variants=[{"id": "a", "description": "d"}],
                prompts=[{"id": "feature"}],
                models=["haiku"],
                n=1,
                output=Path("/tmp/out.jsonl"),
                concurrency=4,
                yes=True,
                resume_files=[Path("results/prev.jsonl")],
                resume_skipped=3,
            )
        out = buf.getvalue()
        self.assertIn("resume:", out)
        self.assertIn("skipping 3", out)
        self.assertIn("of 4 in the full plan", out)

    def test_record_for_codex_cell_uses_codex_analysis(self):
        cell = {
            "variant_id": "current",
            "prompt_id": "feature",
            "model": "default",
            "rep": 0,
            "prompt_text": "prompt",
        }
        workspace_dir = Path(tempfile.mkdtemp(prefix="ab-test-codex-"))
        skill_dir = workspace_dir / ".agents" / "skills" / "using-superpowers"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: using-superpowers\n---\n")
        with (
            mock.patch(
                "run.run_codex_cell",
                return_value={
                    "returncode": 0,
                    "stdout_lines": [
                        '{"type":"item.completed","item":{"type":"command_execution",'
                        '"command":"cat .agents/skills/using-superpowers/SKILL.md"}}'
                    ],
                    "stderr": "",
                },
            ),
        ):
            try:
                record = run._record_for_codex_cell(
                    cell=cell,
                    target_skill="using-superpowers",
                    workspace_dir=workspace_dir,
                    codex_path="codex",
                    timeout_seconds=180,
                )
            finally:
                shutil.rmtree(workspace_dir, ignore_errors=True)

        self.assertTrue(record["harness_validated"])
        self.assertTrue(record["activated"])
        self.assertEqual(record["first_tool_call"], "command_execution")
        self.assertEqual(record["first_tool_skill_name"], "using-superpowers")
        self.assertEqual(record["returncode"], 0)
        self.assertIsNone(record["input_tokens"])
        self.assertIsNone(record["rate_limited_failure"])

    def test_resolve_models_uses_codex_default_sentinel(self):
        self.assertEqual(run._resolve_models("codex", None), ["default"])

    def test_main_stops_on_rate_limit_and_writes_partial_results(self):
        tmp = Path(tempfile.mkdtemp(prefix="ab-test-stop-"))
        out = tmp / "out.jsonl"
        ok = {
            "returncode": 0,
            "stdout_lines": ['{"type":"result","subtype":"success","is_error":false}'],
            "stderr": "",
        }
        throttled = {
            "returncode": 1,
            "stdout_lines": [
                '{"type":"rate_limit_event","rate_limit_info":{"status":"rejected"}}'
            ],
            "stderr": "API Error: 429 rate_limit_error",
        }
        # 3 prompts x 1 variant x 1 model x 1 rep = 3 cells; the 2nd is throttled.
        # The 3rd cell must never reach run_cell (worker short-circuits), so only
        # two side-effect entries are supplied beyond the throttle.
        run_cell_results = [ok, throttled]
        analysis = {
            "harness_validated": True,
            "first_tool_call": None,
            "first_tool_skill_name": None,
            "first_tool_call_block_index": None,
            "activated": False,
        }
        usage = {
            "input_tokens": 1,
            "output_tokens": 1,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "duration_ms": 1,
            "total_cost_usd": 0.0,
        }
        argv = [
            "--variants", "current",
            "--prompts", "feature-request,bug-report,vague-greeting",
            "--models", "claude-haiku-4-5",
            "--n", "1",
            "--concurrency", "1",
            "--output", str(out),
            "--yes",
        ]
        buf = io.StringIO()
        try:
            with (
                mock.patch("run.run_cell", side_effect=run_cell_results) as run_cell_mock,
                mock.patch("run.analyze_stream", return_value=analysis),
                mock.patch("run.extract_usage", return_value=usage),
                mock.patch("run.extract_rate_limit_status", return_value=None),
                mock.patch("run._check_claude_version"),
                mock.patch("run.shutil.which", return_value="/usr/bin/claude"),
                mock.patch("run.build_variant_plugin", return_value=tmp / "plugin"),
                redirect_stdout(buf),
            ):
                rc = run.main(argv)
            output_text = buf.getvalue()
            rows = [
                json.loads(line)
                for line in out.read_text().splitlines()
                if line.strip()
            ]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        self.assertEqual(rc, 2)
        # run_cell called for cell 1 (ok) and cell 2 (throttled); cell 3 short-circuited.
        self.assertEqual(run_cell_mock.call_count, 2)
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[0]["rate_limited_failure"])
        self.assertTrue(rows[1]["rate_limited_failure"])
        self.assertIn("stopped early on a model rate limit", output_text)
        self.assertIn("--resume", output_text)

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
