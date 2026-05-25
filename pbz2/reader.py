"""Streaming readers for `.bz2` files using pbzip2 for parallel decompression.

Falls back to the stdlib `bz2` module when the `pbzip2` binary is unavailable.
"""

from __future__ import annotations

import bz2
import codecs
import logging
import os
import shutil
import subprocess
from collections.abc import Callable, Iterator
from typing import IO, Any, cast

logger = logging.getLogger(__name__)

DEFAULT_BUFSIZE_MB = 32  # OS pipe buffer between pbzip2 and Python
DEFAULT_STREAM_BUFFER_MB = 4  # Python-side read chunk size


def _has_pbzip2() -> bool:
    return shutil.which("pbzip2") is not None


def open_decompress(
    path: str | os.PathLike,
    *,
    num_processors: int | None = None,
    bufsize_mb: int = DEFAULT_BUFSIZE_MB,
) -> tuple[IO[bytes], subprocess.Popen | None]:
    """Open a binary stream that yields decompressed bytes from `path`.

    Returns `(stream, process)`. `process` is the pbzip2 subprocess when
    pbzip2 is available, else `None` (stdlib `bz2.open` fallback).
    """
    if _has_pbzip2():
        nproc = num_processors or max(1, (os.cpu_count() or 2) - 1)
        cmd = [
            "pbzip2",
            "-dc",
            f"-p{nproc}",
            os.fspath(path),
        ]
        logger.info("decompress cmd: %s", " ".join(cmd))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=bufsize_mb * 1024 * 1024,
        )
        assert proc.stdout is not None
        return proc.stdout, proc

    logger.info("pbzip2 not found; falling back to stdlib bz2 for %s", path)
    return cast(IO[bytes], bz2.open(os.fspath(path), "rb")), None


def iter_chunks(
    path: str | os.PathLike,
    *,
    num_processors: int | None = None,
    bufsize_mb: int = DEFAULT_BUFSIZE_MB,
    stream_buffer_mb: int = DEFAULT_STREAM_BUFFER_MB,
) -> Iterator[str]:
    """Yield UTF-8 text chunks of complete newline-terminated records.

    Each yielded chunk ends on a newline boundary, so callers can `splitlines()`
    safely. Handles UTF-8 multibyte characters split across read boundaries.
    """
    stream, proc = open_decompress(
        path,
        num_processors=num_processors,
        bufsize_mb=bufsize_mb,
    )
    read_size = stream_buffer_mb * 1024 * 1024
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""

    try:
        while True:
            data = stream.read(read_size)
            if not data:
                # Flush any final bytes through the incremental decoder
                buffer += decoder.decode(b"", final=True)
                if buffer:
                    yield buffer
                return

            buffer += decoder.decode(data)
            last_nl = buffer.rfind("\n")
            if last_nl == -1:
                continue
            yield buffer[: last_nl + 1]
            buffer = buffer[last_nl + 1 :]
    finally:
        stream.close()
        if proc is not None:
            proc.wait()


def iter_lines(
    path: str | os.PathLike,
    **kwargs: Any,
) -> Iterator[str]:
    """Yield UTF-8 lines (without trailing newline) from a `.bz2` file."""
    for chunk in iter_chunks(path, **kwargs):
        for line in chunk.splitlines():
            if line:
                yield line


def iter_jsonl(
    path: str | os.PathLike,
    *,
    loads: Callable[[str | bytes], Any] | None = None,
    **kwargs: Any,
) -> Iterator[Any]:
    """Yield parsed JSON objects from a `.json.bz2` file (one object per line).

    Uses `orjson.loads` when available, else stdlib `json.loads`. Pass `loads=`
    to override.
    """
    if loads is None:
        try:
            import orjson

            loads = orjson.loads
        except ImportError:
            import json

            loads = json.loads

    for line in iter_lines(path, **kwargs):
        yield loads(line)
