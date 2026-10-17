# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- The README intro links to this changelog.

### Fixed

- Dependabot: dropped `semver-major-days` from the github-actions cooldown, which
  that ecosystem does not support; actions updates use the 5-day default.

## [0.2.2] - 2026-10-16

### Changed

- Type hints are fully parameterized for pyrefly's strict preset: path arguments
  are `str | os.PathLike[str]` and `open_decompress` returns
  `subprocess.Popen[bytes] | None`. Runtime behavior is unchanged.
- The sdist now ships only the package, `README.md`, `CHANGELOG.md`, and
  `LICENSE`; plan files, tests, and tooling config are no longer included.
- Tooling: ruff 0.15 -> 0.16 (pinned to the same minor as the pre-commit hook),
  pyrefly strict preset, and coverage configured in `pyproject.toml` with a 50%
  floor.
- CI: each test-matrix leg now runs on its own Python version (previously every
  leg fell back to the `.python-version` pin); workflow actions are pinned to
  commit SHAs; dependabot targets `dev` with cooldown windows.

## [0.2.1] - 2026-06-10

### Changed

- typer 0.25.1 -> 0.26.7 (typer no longer depends on `click`) and
  ruff 0.15.14 -> 0.15.16 (#16).
- CI: workflow actions reference specific version tags (e.g.
  `actions/checkout@v6.0.3`) instead of commit SHAs.

## [0.2.0] - 2026-06-10

### Changed

- `iter_jsonl` always uses `orjson` (now imported at module level); the dead
  stdlib-`json` ImportError fallback is removed. `orjson` was already a required
  dependency, so behavior is unchanged — pass `loads=` to override.
- `open_decompress` now opens pbzip2's stderr as a pipe owned by the caller
  (drain, close, and check `returncode` after consuming the stream), so
  decompression errors can be surfaced instead of discarded.
- CI: pbzip2 is installed in every test-matrix leg so the primary decompression
  path is exercised (the stdlib fallback is covered via a forced-fallback test);
  actions are pinned to commit SHAs; dependabot updates are grouped; publishing
  is gated behind the `PUBLISH_ENABLED` repository variable.

### Fixed

- `iter_chunks` (and everything built on it: `iter_lines`, `iter_jsonl`,
  `process_parallel`, the CLI) now raises `RuntimeError` with pbzip2's stderr
  when decompression exits non-zero, instead of silently yielding partial data
  from a corrupt or truncated `.bz2`. Stopping early (e.g. `pbz2 head`) is still
  treated as normal termination, not a failure.

## [0.1.3] - 2026-05-28

### Fixed

- `iter_lines` (and thus `iter_jsonl`) no longer drops records containing raw
  U+2028/U+2029/U+0085: it now splits on `\n` only, instead of `str.splitlines()`,
  which treats those Unicode separators as line boundaries and shattered such
  records into invalid fragments.

## [0.1.0] - 2026-05-10

Initial release.

### Added

- `open_decompress` — file-like reader that streams a `.bz2` file through `pbzip2 -dc`.
- `iter_chunks` — iterate over fixed-size byte chunks from a decompressed stream.
- `iter_lines` — iterate over decoded text lines from a decompressed stream.
- `iter_jsonl` — iterate over parsed JSON records from a decompressed JSONL stream, backed by `orjson`.
- `process_parallel` — fan out decompressed records across worker processes.
- `pbz2` CLI entry point (Typer-based) for streaming and processing `.bz2` files from the shell.
- Python 3.11–3.14 support.
