"""Concurrent cell execution wrapper.

Hermetic per-cell sessions are independent (different temp plugin trees can
share a name; different processes have separate stdout), so cells parallelize
cleanly across threads. Each thread blocks on `subprocess.run`, so a
ThreadPoolExecutor is the right primitive — the GIL is released during the
subprocess call."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterator, List, Tuple


CellRecord = dict


def execute_cells(
    cells: List[dict],
    worker: Callable[[dict], CellRecord],
    concurrency: int = 1,
) -> Iterator[Tuple[int, dict, CellRecord]]:
    """Run worker(cell) for each cell, yielding (done_count, cell, record).

    With concurrency<=1, cells run sequentially in submission order.
    With concurrency>1, cells run in parallel via ThreadPoolExecutor; yield
    order is completion order, not submission order. done_count is monotonic
    1..len(cells) regardless of mode.

    Worker exceptions propagate via future.result() — the caller is responsible
    for catching expected failures (e.g. subprocess.TimeoutExpired) inside the
    worker if it wants to materialize them as records instead of crashing the
    run."""
    if not cells:
        return

    if concurrency <= 1:
        for index, cell in enumerate(cells, start=1):
            yield index, cell, worker(cell)
        return

    workers = min(concurrency, len(cells))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(worker, cell): cell for cell in cells}
        for done_count, future in enumerate(as_completed(futures), start=1):
            cell = futures[future]
            yield done_count, cell, future.result()
