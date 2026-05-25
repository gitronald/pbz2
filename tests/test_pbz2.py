"""Tests for pbz2."""

from __future__ import annotations

import bz2
import json
from pathlib import Path

import pytest

import pbz2


@pytest.fixture
def jsonl_bz2(tmp_path: Path) -> Path:
    records = [{"i": i, "msg": f"hello {i} éñ"} for i in range(1000)]
    path = tmp_path / "data.json.bz2"
    with bz2.open(path, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


def test_iter_lines(jsonl_bz2: Path) -> None:
    lines = list(pbz2.iter_lines(jsonl_bz2))
    assert len(lines) == 1000
    assert json.loads(lines[0])["i"] == 0
    assert json.loads(lines[-1])["i"] == 999


def test_iter_jsonl(jsonl_bz2: Path) -> None:
    objs = list(pbz2.iter_jsonl(jsonl_bz2))
    assert len(objs) == 1000
    assert objs[42]["i"] == 42
    assert "éñ" in objs[0]["msg"]


def test_iter_jsonl_with_stdlib_loads(jsonl_bz2: Path) -> None:
    objs = list(pbz2.iter_jsonl(jsonl_bz2, loads=json.loads))
    assert len(objs) == 1000


def test_iter_chunks_newline_aligned(jsonl_bz2: Path) -> None:
    for chunk in pbz2.iter_chunks(jsonl_bz2, stream_buffer_mb=1):
        assert chunk.endswith("\n")


def _count_lines(chunk: str) -> int:
    return sum(1 for line in chunk.splitlines() if line)


def test_process_parallel(jsonl_bz2: Path) -> None:
    counts: list[int] = []
    pbz2.process_parallel(
        jsonl_bz2,
        worker_fn=_count_lines,
        on_result=counts.append,
        num_processes=2,
    )
    assert sum(counts) == 1000


def test_process_parallel_decoupled_decompress(jsonl_bz2: Path) -> None:
    """A pbzip2 thread count below the worker count yields identical results."""
    counts: list[int] = []
    pbz2.process_parallel(
        jsonl_bz2,
        worker_fn=_count_lines,
        on_result=counts.append,
        num_processes=4,
        decompress_procs=1,
    )
    assert sum(counts) == 1000


def _sum_field(chunk: str, field: str) -> int:
    return sum(json.loads(line)[field] for line in chunk.splitlines() if line)


def test_process_parallel_with_worker_args(jsonl_bz2: Path) -> None:
    totals: list[int] = []
    pbz2.process_parallel(
        jsonl_bz2,
        worker_fn=_sum_field,
        worker_args=("i",),
        on_result=totals.append,
        num_processes=2,
    )
    assert sum(totals) == sum(range(1000))
