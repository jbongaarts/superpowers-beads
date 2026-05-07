import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from executor import execute_cells


class ExecuteCellsTest(unittest.TestCase):
    def test_concurrency_one_preserves_submission_order(self):
        cells = [{"id": i} for i in range(5)]
        seen = list(
            execute_cells(cells, worker=lambda c: {"out": c["id"]}, concurrency=1)
        )
        ids = [cell["id"] for _, cell, _ in seen]
        self.assertEqual(ids, [0, 1, 2, 3, 4])
        outs = [r["out"] for _, _, r in seen]
        self.assertEqual(outs, [0, 1, 2, 3, 4])
        counts = [c for c, _, _ in seen]
        self.assertEqual(counts, [1, 2, 3, 4, 5])

    def test_concurrency_zero_or_negative_falls_back_to_sequential(self):
        cells = [{"id": i} for i in range(3)]
        for concurrency in (0, -1):
            with self.subTest(concurrency=concurrency):
                seen = list(
                    execute_cells(
                        cells,
                        worker=lambda c: {"out": c["id"]},
                        concurrency=concurrency,
                    )
                )
                self.assertEqual([c["id"] for _, c, _ in seen], [0, 1, 2])

    def test_concurrency_above_one_yields_every_cell(self):
        cells = [{"id": i} for i in range(8)]
        seen = list(
            execute_cells(cells, worker=lambda c: {"out": c["id"]}, concurrency=4)
        )
        out_ids = sorted(r["out"] for _, _, r in seen)
        self.assertEqual(out_ids, list(range(8)))
        done_counts = [c for c, _, _ in seen]
        self.assertEqual(done_counts, list(range(1, 9)))

    def test_concurrency_actually_parallelizes(self):
        cells = [{"id": i} for i in range(4)]
        sleep_s = 0.1

        def worker(_cell):
            time.sleep(sleep_s)
            return {"thread": threading.get_ident()}

        start = time.time()
        seen = list(execute_cells(cells, worker, concurrency=4))
        elapsed = time.time() - start

        self.assertLess(
            elapsed,
            sleep_s * len(cells) * 0.6,
            f"concurrency=4 took {elapsed:.2f}s; sequential would be {sleep_s*len(cells):.2f}s",
        )
        thread_ids = {r["thread"] for _, _, r in seen}
        self.assertGreater(len(thread_ids), 1, "expected work across multiple threads")

    def test_concurrency_caps_at_cell_count(self):
        cells = [{"id": 0}]
        seen = list(
            execute_cells(cells, worker=lambda c: {"ok": True}, concurrency=10)
        )
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], 1)

    def test_empty_cells_is_a_noop(self):
        seen = list(execute_cells([], worker=lambda c: {}, concurrency=4))
        self.assertEqual(seen, [])

    def test_worker_exceptions_propagate(self):
        cells = [{"id": 0}, {"id": 1}]

        def worker(_cell):
            raise ValueError("boom")

        for concurrency in (1, 2):
            with self.subTest(concurrency=concurrency):
                with self.assertRaises(ValueError):
                    list(execute_cells(cells, worker, concurrency=concurrency))


if __name__ == "__main__":
    unittest.main()
