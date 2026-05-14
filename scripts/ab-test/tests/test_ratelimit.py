import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ratelimit import detect_rate_limit


class DetectRateLimitTest(unittest.TestCase):
    def test_rejected_rate_limit_event_is_a_failure(self):
        lines = ['{"type":"rate_limit_event","rate_limit_info":{"status":"rejected"}}']
        reason = detect_rate_limit(lines, stderr="", returncode=1)
        self.assertIsNotNone(reason)
        self.assertIn("rejected", reason)

    def test_rejected_rate_limit_event_even_with_zero_returncode(self):
        lines = ['{"type":"rate_limit_event","rate_limit_info":{"status":"rejected"}}']
        self.assertIsNotNone(detect_rate_limit(lines, stderr="", returncode=0))

    def test_allowed_warning_rate_limit_event_is_not_a_failure(self):
        lines = [
            '{"type":"rate_limit_event","rate_limit_info":{"status":"allowed_warning"}}',
            '{"type":"result","subtype":"success","is_error":false}',
        ]
        self.assertIsNone(detect_rate_limit(lines, stderr="", returncode=0))

    def test_allowed_rate_limit_event_is_not_a_failure(self):
        lines = ['{"type":"rate_limit_event","rate_limit_info":{"status":"allowed"}}']
        self.assertIsNone(detect_rate_limit(lines, stderr="", returncode=0))

    def test_error_result_event_with_rate_limit_text(self):
        lines = [
            '{"type":"result","subtype":"error_during_execution","is_error":true,'
            '"result":"API Error: 429 rate_limit_error: usage limit reached"}'
        ]
        reason = detect_rate_limit(lines, stderr="", returncode=1)
        self.assertIsNotNone(reason)
        self.assertIn("usage limit", reason)

    def test_error_result_event_without_throttle_text_is_not_a_failure(self):
        lines = [
            '{"type":"result","subtype":"error_during_execution","is_error":true,'
            '"result":"model produced invalid tool call"}'
        ]
        self.assertIsNone(detect_rate_limit(lines, stderr="", returncode=1))

    def test_nonzero_exit_with_429_in_stderr(self):
        reason = detect_rate_limit(
            stdout_lines=[],
            stderr="Error: request failed: 429 Too Many Requests",
            returncode=1,
        )
        self.assertIsNotNone(reason)
        self.assertIn("stderr", reason)

    def test_nonzero_exit_with_usage_limit_in_stderr(self):
        reason = detect_rate_limit(
            stdout_lines=[],
            stderr="You've reached your usage limit. Resets at 3:20am.",
            returncode=2,
        )
        self.assertIsNotNone(reason)

    def test_nonzero_exit_with_ordinary_error_is_not_a_failure(self):
        self.assertIsNone(
            detect_rate_limit(
                stdout_lines=[],
                stderr="fatal: not a git repository",
                returncode=128,
            )
        )

    def test_clean_success_with_rate_limit_text_in_model_reply_is_not_a_failure(self):
        # The model talking *about* rate limits in a successful turn must not trip it.
        lines = [
            '{"type":"assistant","message":{"content":[{"type":"text",'
            '"text":"Here is how you handle a 429 rate limit error..."}]}}',
            '{"type":"result","subtype":"success","is_error":false}',
        ]
        self.assertIsNone(detect_rate_limit(lines, stderr="", returncode=0))

    def test_nonzero_exit_with_only_benign_rate_limit_event_is_not_a_failure(self):
        # A non-zero exit plus a benign rate_limit_event line must not self-trip
        # via the literal "rate_limit" substring inside the event type name.
        lines = [
            '{"type":"system","subtype":"init"}',
            '{"type":"rate_limit_event","rate_limit_info":{"status":"allowed"}}',
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash"}]}}',
        ]
        self.assertIsNone(detect_rate_limit(lines, stderr="", returncode=143))

    def test_clean_success_with_no_events(self):
        self.assertIsNone(detect_rate_limit([], stderr="", returncode=0))

    def test_garbled_lines_are_ignored(self):
        self.assertIsNone(
            detect_rate_limit(["not json", "", "{partial"], stderr="", returncode=0)
        )


if __name__ == "__main__":
    unittest.main()
