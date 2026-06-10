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

import orjson

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
    pbzip2 is available, else `None` (stdlib `bz2.open` fallback). The caller
    owns `process.stderr` (a pipe): drain and close it after `stream` is
    consumed, and check `process.returncode`, as `iter_chunks` does.
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
            # Capture stderr so a decompression failure can be surfaced. pbzip2
            # emits only a few lines here (even on error), so it cannot fill the
            # pipe buffer and deadlock against the stdout read in iter_chunks.
            stderr=subprocess.PIPE,
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

    Each yielded chunk ends on a "\\n" boundary, so callers can split on "\\n"
    safely. Do NOT use ``str.splitlines()``: it also breaks on U+2028/U+2029/U+0085
    and other Unicode line separators that can occur raw inside record content,
    which would shatter those records. Handles UTF-8 multibyte characters split
    across read boundaries.
    """
    stream, proc = open_decompress(
        path,
        num_processors=num_processors,
        bufsize_mb=bufsize_mb,
    )
    read_size = stream_buffer_mb * 1024 * 1024
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    exhausted = False

    try:
        while True:
            data = stream.read(read_size)
            if not data:
                # EOF means the stream was fully drained -- mark it before the
                # final flush so a UnicodeDecodeError there (truncated multibyte
                # char) still triggers the exit-status check in finally, keeping
                # pbzip2's stderr in the raised error instead of losing it.
                exhausted = True
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
            stderr = proc.stderr.read() if proc.stderr is not None else b""
            if proc.stderr is not None:
                proc.stderr.close()
            proc.wait()
            # Only validate the exit status when we drained the whole stream. An
            # early break (e.g. CLI `head`) closes the pipe and makes pbzip2 die
            # with SIGPIPE, which is expected -- not a decompression failure.
            if exhausted and proc.returncode:
                msg = stderr.decode("utf-8", "replace").strip()
                raise RuntimeError(
                    f"pbzip2 failed (exit {proc.returncode}) decompressing "
                    f"{os.fspath(path)}" + (f": {msg}" if msg else "")
                )


def iter_lines(
    path: str | os.PathLike,
    **kwargs: Any,
) -> Iterator[str]:
    """Yield UTF-8 lines (without trailing newline) from a `.bz2` file."""
    # Split on "\n" only -- str.splitlines() also breaks on U+2028/U+2029/U+0085
    # and other Unicode line boundaries, which can appear raw inside record content
    # (notably inside embedded HTML/JavaScript) and would shatter those records.
    for chunk in iter_chunks(path, **kwargs):
        for line in chunk.split("\n"):
            line = line.rstrip("\r")
            if line:
                yield line


def iter_jsonl(
    path: str | os.PathLike,
    *,
    loads: Callable[[str | bytes], Any] | None = None,
    **kwargs: Any,
) -> Iterator[Any]:
    """Yield parsed JSON objects from a `.json.bz2` file (one object per line).

    Uses `orjson.loads` by default. Pass `loads=` to override.
    """
    if loads is None:
        loads = orjson.loads

    for line in iter_lines(path, **kwargs):
        yield loads(line)
