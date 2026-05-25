"""Parallel processing of `.bz2` streams via a process pool.

Streams chunks of newline-terminated records from a `.bz2` file through a
worker function in a `ProcessPoolExecutor`, dispatching each result to an
optional handler in the main process.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from typing import Any

from .reader import (
    DEFAULT_BUFSIZE_MB,
    DEFAULT_STREAM_BUFFER_MB,
    iter_chunks,
)

logger = logging.getLogger(__name__)


def process_parallel(
    path: str | os.PathLike,
    worker_fn: Callable[..., Any],
    *,
    on_result: Callable[[Any], None] | None = None,
    worker_args: Sequence[Any] = (),
    num_processes: int | None = None,
    decompress_procs: int | None = None,
    max_pending: int | None = None,
    bufsize_mb: int = DEFAULT_BUFSIZE_MB,
    stream_buffer_mb: int = DEFAULT_STREAM_BUFFER_MB,
) -> None:
    """Process chunks of `path` in parallel.

    `worker_fn(chunk, *worker_args)` runs in worker processes; each chunk is a
    `str` of complete newline-terminated records. Results are dispatched to
    `on_result` in the main process as they complete.

    `decompress_procs` sets the pbzip2 `-p` thread count independently of the
    worker pool; it defaults to `num_processes` (decompressor and workers coupled,
    as before). Sizing it below the worker count frees CPU for the workers when
    parsing -- not decompression -- is the bottleneck.

    When `max_pending` is set, the producer pauses while that many futures are
    in-flight to bound memory.
    """
    nproc = num_processes or max(1, (os.cpu_count() or 2) // 2)
    dproc = decompress_procs or nproc
    cap = max_pending if max_pending is not None else nproc * 2

    def drain_done(pending: list, *, block: bool = False) -> list:
        if block and pending:
            wait(pending, return_when=FIRST_COMPLETED)
        still_pending = []
        for fut in pending:
            if fut.done():
                result = fut.result()
                if on_result is not None:
                    on_result(result)
            else:
                still_pending.append(fut)
        return still_pending

    with ProcessPoolExecutor(max_workers=nproc) as executor:
        pending: list = []
        for chunk in iter_chunks(
            path,
            num_processors=dproc,
            bufsize_mb=bufsize_mb,
            stream_buffer_mb=stream_buffer_mb,
        ):
            if not chunk.strip():
                continue
            pending.append(executor.submit(worker_fn, chunk, *worker_args))
            pending = drain_done(pending)
            while len(pending) >= cap:
                pending = drain_done(pending, block=True)

        while pending:
            pending = drain_done(pending, block=True)
