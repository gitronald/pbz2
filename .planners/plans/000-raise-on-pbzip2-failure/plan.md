---
id: 0
slug: raise-on-pbzip2-failure
status: done
branch: claude/full-max-code-review-lemyrj
created: 2026-06-10T09:52:14-07:00
concluded: 2026-06-10T09:48:27-07:00
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
- 2026-06-10 — max-effort review of the PR run and posted as a PR comment.
  Review follow-up (all in the second branch commit): `exhausted` moved before
  the final decoder flush so truncation mid-multibyte-character raises
  `RuntimeError` with pbzip2's stderr instead of a bare `UnicodeDecodeError`
  (regression test added); corrupt-input test parametrized over both backends
  so the stdlib fallback stays covered in CI; `open_decompress` docstring
  documents caller ownership of `process.stderr`; test docstring corrected
  (`EOFError` vs `OSError`). Conscious no-op: oversized branch commit subject
  handled via the merge-commit subject rather than rewriting pushed history.
  Checks green locally (ruff, pyrefly, 11 tests) and in CI (3.11-3.14).

## Retrospective

- The empirical review probes were the high-value step: running truncated
  multibyte input against the branch exposed that the headline error path
  rarely fired (`UnicodeDecodeError` masked the `RuntimeError` in 5 of 6
  truncation points) — a static read of the diff looked correct.
- Installing pbzip2 in CI silently killed coverage of the stdlib fallback;
  forcing the fallback with a monkeypatch keeps both paths tested on one CI
  config. Worth remembering whenever a binary dependency gates a code path.
- Setting the "stream fully drained" flag at EOF detection (not after the
  decoder flush) was a one-line fix with outsized diagnostic value; ordering of
  state flags around failable cleanup steps deserves review attention.
- This plan was backfilled after the work; scaffolding it at review time would
  have captured the findings with less reconstruction.