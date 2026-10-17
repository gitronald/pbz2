---
id: 1
slug: template-upgrade
status: done
branch: feature/template-upgrade
created: 2026-10-16T20:26:39-07:00
concluded: 2026-10-16T20:28:18-07:00
pr: https://github.com/gitronald/pbz2/pull/26
---

# Upgrade to proj-template v0.11.2

## Plan

Bring pbz2 to the proj-template v0.11.2 standard with the template's
`install-template` skill (upgrade mode), read from the `v0.11.2` tag. pbz2 has
no `[tool.proj-template]` stamp, so it is treated as never stamped.

### Classification

**package**: it has a hatchling `[build-system]`, a `project.scripts` entry
(`pbz2`), and a `publish.yml`.

### Sync decisions

| Template path | Action |
|---|---|
| `pyproject.toml` ruff / pyrefly | merge: `extend-exclude = ["*.md"]`, pyrefly `preset = "strict"`, `project-excludes`, tests sub-config |
| `pyproject.toml` dev group | merge pins: `pyrefly>=1.0.0`, `pytest>=9.0.3`, `ruff>=0.16,<0.17` |
| `pyproject.toml` pytest / coverage | merge: `addopts = "--cov --cov-report=term-missing"`, `[tool.coverage.*]` with `source = ["pbz2"]`; `fail_under` set to the current total if below 50 |
| `pyproject.toml` sdist `only-include` | add, with `/pbz2` |
| `pyproject.toml` `[tool.proj-template]` | stamp `0.11.2`, last |
| `.pre-commit-config.yaml` | sync: `default_stages`, ruff rev, `ruff-check` id, planners hooks |
| `.gitattributes` | add (`.planners/README.md merge=union`) |
| `.gitignore`, `.python-version` | already match |
| `.github/workflows/test.yml` | sync (SHA pins, job-level `UV_PYTHON`, `--python` on sync, coverage via `addopts`); keep the repo's `pbzip2` apt install step |
| `.github/workflows/publish.yml` | sync SHA pins |
| `.github/dependabot.yml` | merge: header comment, `target-branch: dev`; keep the repo's `semver-major-days: 14` on the github-actions ecosystem |
| `.claude/` | gitignored here: written in the main checkout, on disk only |
| `pbz2/`, `tests/`, `README.md`, `CHANGELOG.md` | never |

### Order

1. Tooling config (`pyproject.toml`, pre-commit, `.gitattributes`)
2. CI and dependabot
3. Code fixes for the strict pyrefly preset and ruff 0.16
4. Verify: ruff, pyrefly, pre-commit, pytest all green
5. Stamp, PR into `dev`

## Log

- **2026-10-16T20:26:51-07:00** — Activated.
  - Branch: `feature/template-upgrade`
  - Base: `dev` at `e907604`
  - Worktree: `.worktrees/template-upgrade`
  - PR: pending
- **2026-10-16T20:28:29-07:00** — Applied the v0.11.2 sync matrix; all checks green (ruff, pyrefly strict 0 errors, pre-commit, pytest 11 passed at 83% coverage).
  - Tooling: pyproject ruff/pyrefly/pytest/coverage sections and dev pins merged; sdist only-include added; pre-commit synced; ruff-pre-commit rev moved to v0.16.10 to match the locked ruff; .gitattributes added.
  - Strict pyrefly: 9 implicit-any-type-argument errors fixed at the source (os.PathLike[str], subprocess.Popen[bytes], list[Future[Any]]); no excludes needed.
  - Coverage: fail_under kept at the template's 50 (current total 83%).
  - CI: test.yml and publish.yml synced to SHA pins; kept the repo's pbzip2 apt install step, which the tests need.
  - Dependabot: added header and target-branch dev (origin/dev exists); kept the repo's semver-major-days 14 on github-actions, which the template drops. Merged rather than asked, since both keep repo content and add the template's.
  - .claude/ is gitignored: CLAUDE.md, settings.json, and the Stop hook were written in the main checkout, on disk only. settings.local.json was not copied: the shared permission baseline lives in the user-level settings, so a per-repo copy would only duplicate it.
  - Stamped [tool.proj-template] version 0.11.2 last.
- **2026-10-16T20:28:59-07:00** — PR opened: https://github.com/gitronald/pbz2/pull/26
- **2026-10-16T20:36:27-07:00** — Review gate (medium, /code-review on sonnet finders): no findings; local gate and CI 3.11-3.14 green.
  - Review follow-up: five low-confidence candidates raised, none actioned. Conscious no-ops: three template-intended config choices (separate local pre-commit blocks, explicit uv python install, pyrefly project-excludes); the coverage floor applying to partial pytest runs, accepted by the template; the dependabot semver-major-days key, which predates this PR.
  - sdist checked with uv build: only pbz2/, README, CHANGELOG, LICENSE, plus hatchling's forced files.

## Retrospective

- The sync matrix held as planned. The one deviation was the ruff-pre-commit rev: it moved to v0.16.10 to match the locked ruff rather than the template's listed rev, so the commit hook and `uv run ruff` apply one rule set.
- Strict pyrefly cost nine annotation fixes, all implicit `Any` type arguments, and no excludes. A small typed package absorbs the strict preset cheaply.
- Merging repo-specific content (the pbzip2 apt step, dependabot's 14-day major cooldown) into the template files, rather than overwriting them, was the main judgment call. Recording each keep in the sync table up front made the review quick.
- `.claude/` is gitignored here, so the template's Claude files exist only on disk in the main checkout. A fresh clone will not have them until it is re-synced.
