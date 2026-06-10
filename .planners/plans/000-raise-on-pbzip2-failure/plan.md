---
id: 0
slug: raise-on-pbzip2-failure
status: active
branch: claude/full-max-code-review-lemyrj
created: 2026-06-10T09:52:14-07:00
concluded:
pr: https://github.com/gitronald/pbz2/pull/13
---

# Raise on pbzip2 decompression failure

## Plan

Backfilled — work already implemented; see the PR for full details.

`iter_chunks` read pbzip2's stdout to EOF and ignored the exit code, so a
corrupt or truncated `.bz2` silently yielded partial data. Fix: capture stderr,
check `proc.returncode` after the stream is fully drained, and raise
`RuntimeError` with pbzip2's message — gated on an `exhausted` flag so an early
break (e.g. CLI `head` → SIGPIPE) is not treated as a failure. Also: install
pbzip2 in CI so the primary path is tested, cover the stdlib fallback via
monkeypatch, and remove `iter_jsonl`'s dead stdlib-`json` fallback (orjson is a
required dependency).

## Log

- Initial implementation and code-review fixes (error surfacing on truncated
  multibyte input, fallback-path test coverage) are on the PR branch.