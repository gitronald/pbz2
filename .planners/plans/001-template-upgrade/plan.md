---
id: 1
slug: template-upgrade
status: active
branch: feature/template-upgrade
created: 2026-10-16T20:26:39-07:00
concluded:
pr:
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
