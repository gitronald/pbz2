"""Tests for pbz2."""

from __future__ import annotations

import bz2
import json
from pathlib import Path

import pytest

import pbz2
from pbz2.reader import _has_pbzip2


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


def test_iter_lines_preserves_unicode_line_separators(tmp_path: Path) -> None:
    """Raw U+2028/U+2029/U+0085 inside a record must not split it.

    These code points are line boundaries to ``str.splitlines()`` but not to a
    plain ``split("\\n")``. They occur raw in real-world data (notably embedded
    JavaScript), so ``iter_lines`` must keep each record whole.
    """
    records = [
        {"i": 0, "html": "before\u2028after"},  # LINE SEPARATOR
        {"i": 1, "html": "x\u2029y"},  # PARAGRAPH SEPARATOR
        {"i": 2, "html": "a\u0085b"},  # NEL
        {"i": 3, "html": "plain"},
    ]
    path = tmp_path / "u2028.json.bz2"
    # ensure_ascii=False writes the separators raw (escaped \u2028 would not repro)
    with bz2.open(path, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    lines = list(pbz2.iter_lines(path))
    assert len(lines) == len(records)  # one line per record, not shattered

    objs = list(pbz2.iter_jsonl(path))
    assert len(objs) == len(records)
    assert objs[0]["html"] == "before\u2028after"
    assert objs[1]["html"] == "x\u2029y"
    assert objs[2]["html"] == "a\u0085b"


@pytest.mark.parametrize("backend", ["pbzip2", "stdlib"])
def test_corrupt_input_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    """A garbage `.bz2` must error rather than silently yield partial data.

    The pbzip2 path surfaces a non-zero exit as ``RuntimeError``; the stdlib
    fallback raises ``OSError`` on this garbage stream (a truncated but
    otherwise valid stream raises ``EOFError`` instead). Either way it must
    not return a short, silent result. The stdlib leg forces the fallback so
    both paths are covered even when pbzip2 is installed.
    """
    if backend == "pbzip2":
        if not _has_pbzip2():
            pytest.skip("pbzip2 not installed")
        expected: type[Exception] = RuntimeError
    else:
        monkeypatch.setattr("pbz2.reader._has_pbzip2", lambda: False)
        expected = OSError
    path = tmp_path / "bad.bz2"
    path.write_bytes(b"BZh9" + b"\x00not a valid bzip2 stream\xff" * 50)
    with pytest.raises(expected):
        list(pbz2.iter_lines(path))


def test_truncated_input_raises_runtime_error(tmp_path: Path) -> None:
    """A truncated `.bz2` must raise ``RuntimeError`` on the pbzip2 path.

    Truncated multibyte-dense output usually ends mid-character, so the final
    decoder flush raises ``UnicodeDecodeError`` -- the exit-status check must
    still fire and surface pbzip2's stderr instead of losing it.
    """
    if not _has_pbzip2():
        pytest.skip("pbzip2 not installed")
    src = tmp_path / "good.json.bz2"
    with bz2.open(src, "wt", encoding="utf-8") as f:
        for i in range(20_000):
            record = {"i": i, "msg": "日本語テキスト" * 5}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    bad = tmp_path / "trunc.json.bz2"
    bad.write_bytes(src.read_bytes()[: src.stat().st_size // 2])
    with pytest.raises(RuntimeError, match="pbzip2 failed"):
        list(pbz2.iter_lines(bad))


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
