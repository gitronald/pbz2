# pbz2

Stream and parallel-process `.bz2` files via [pbzip2](http://compression.great-site.net/pbzip2/) (parallel bzip2).

Reads compressed files through a `pbzip2 -dc` subprocess for multi-core decompression — no temp files, no full decompression to disk — and falls back to the stdlib `bz2` module when the `pbzip2` binary is unavailable. Iterate raw lines, newline-aligned text chunks, or parsed JSONL records, or fan chunks out across a process pool for parallel parsing. Includes a CLI for quick inspection and a Python API for custom pipelines. Corrupt or truncated input raises instead of silently yielding partial data.

## Project Structure

```
pbz2/
├── pbz2/                 # Python library
│   ├── reader.py         # Streaming readers (open_decompress, iter_*)
│   ├── parallel.py       # Process-pool chunk processing
│   └── cli.py            # Typer CLI commands
├── tests/                # Test suite
└── pyproject.toml        # Project configuration
```

## Installation

```bash
uv add pbz2
```

From source:

```bash
git clone https://github.com/gitronald/pbz2.git
cd pbz2
uv sync
```

From a specific branch:

```bash
uv add git+https://github.com/gitronald/pbz2.git@dev
```

Install the `pbzip2` binary for parallel decompression (optional — without it, reads fall back to single-threaded stdlib `bz2`):

```bash
sudo apt install pbzip2     # Debian/Ubuntu
brew install pbzip2         # macOS
```

## CLI Commands

Quick inspection of `.bz2` files from the shell:

```bash
# Count lines
pbz2 count data.json.bz2

# Print the first N lines
pbz2 head data.json.bz2 -n 5
```

## Python API

### Iterate

```python
import pbz2

# Parsed JSON objects from a .json.bz2 file
for obj in pbz2.iter_jsonl("data.json.bz2"):
    ...

# Raw UTF-8 lines
for line in pbz2.iter_lines("data.txt.bz2"):
    ...

# Newline-aligned text chunks (useful for batched processing)
for chunk in pbz2.iter_chunks("data.txt.bz2"):
    ...
```

### Parallel processing

`process_parallel` streams chunks of newline-terminated records through a worker pool. The worker function receives raw text chunks (so parsing happens in the worker, not the main process), and `on_result` runs in the main process to handle each result as it completes.

```python
import json
import pbz2

def parse_chunk(chunk: str) -> list[dict]:
    # split on "\n" only -- str.splitlines() also breaks on U+2028/U+2029 etc.,
    # which can appear raw inside records and would shatter them
    return [json.loads(line) for line in chunk.split("\n") if line]

def save(records: list[dict]) -> None:
    ...  # write to db, file, etc.

pbz2.process_parallel(
    "data.json.bz2",
    worker_fn=parse_chunk,
    on_result=save,
    num_processes=8,
)
```

### Reference

| Function | Description |
| --- | --- |
| `iter_chunks(path, **opts)` | Yield UTF-8 text chunks ending on a newline boundary. |
| `iter_lines(path, **opts)` | Yield non-empty UTF-8 lines (no trailing newline). |
| `iter_jsonl(path, *, loads=None, **opts)` | Yield parsed JSON objects (uses `orjson`; pass `loads=` to override). |
| `process_parallel(path, worker_fn, *, on_result=None, worker_args=(), num_processes=None, max_pending=None, ...)` | Run `worker_fn(chunk, *worker_args)` in a process pool, dispatching results to `on_result`. |
| `open_decompress(path, **opts)` | Low-level: open a binary stream of decompressed bytes. |

### Common options

- `num_processors` — pbzip2 worker count (default: cpu_count - 1)
- `bufsize_mb` — OS pipe buffer between pbzip2 and Python (default: 32 MB)
- `stream_buffer_mb` — Python-side read chunk size (default: 4 MB)
