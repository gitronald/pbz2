# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

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
