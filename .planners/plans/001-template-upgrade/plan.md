---
id: 1
slug: template-upgrade
status: active
branch: feature/template-upgrade
created: 2026-10-16T20:26:39-07:00
concluded:
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
