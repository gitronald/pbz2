# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

- `block_size` parameter from `open_decompress`, `iter_chunks`, and `process_parallel`. The underlying `pbzip2 -b#` flag is documented as "not valid for decompression" and was silently ignored, so the parameter was a no-op. Callers passing `block_size=...` will now get a `TypeError`.

### Fixed

### Security
