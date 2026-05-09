"""pbz2: stream and parallel-process `.bz2` files via pbzip2."""

from .parallel import process_parallel
from .reader import iter_chunks, iter_jsonl, iter_lines, open_decompress

__all__ = [
    "iter_chunks",
    "iter_jsonl",
    "iter_lines",
    "open_decompress",
    "process_parallel",
]
