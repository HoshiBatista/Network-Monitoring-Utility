<div align="center">

# Contributing to Network Monitoring Utility

Thank you for taking the time to contribute!  
Please read this guide before opening an issue or pull request.

</div>

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Report a Bug](#how-to-report-a-bug)
- [How to Request a Feature](#how-to-request-a-feature)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Style](#commit-style)
- [Pull Request Checklist](#pull-request-checklist)
- [Code Style](#code-style)

---

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).  
By contributing you agree to uphold its standards.

---

## How to Report a Bug

1. Search [existing issues](../../issues) to avoid duplicates.
2. Open a **Bug Report** issue and include:
   - A clear title and description
   - Steps to reproduce
   - Expected vs actual behaviour
   - Python version, OS, and relevant logs

---

## How to Request a Feature

1. Search [existing issues](../../issues) to avoid duplicates.
2. Open a **Feature Request** issue and describe:
   - The problem you want to solve
   - Your proposed solution (optional)
   - Why this would benefit other users

---

## Development Setup

```bash
# 1. Fork & clone
git clone https://github.com/<your-username>/network-monitoring-utility.git
cd network-monitoring-utility

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install all dependencies (including dev tools)
pip install -r requirements.txt

# 4. Verify everything works
pytest
ruff check .
ruff format --check .
```

---

## Making Changes

```bash
# Create a branch from main
git checkout -b feat/your-feature-name   # new feature
git checkout -b fix/short-description    # bug fix
git checkout -b docs/update-readme       # documentation
```

Keep branches focused — one logical change per PR makes review faster.

---

## Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short imperative summary>

[optional body]
```

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `refactor` | Code change with no behaviour change |
| `chore` | Build, CI, or tooling changes |

**Examples**

```
feat: add TCP port check to checker service
fix: handle ConnectionRefusedError in _tcp_check
docs: update README quick-start section
test: add validation tests for node port range
```

---

## Pull Request Checklist

Before opening a PR make sure:

- [ ] All existing tests pass: `pytest`
- [ ] New functionality is covered by tests
- [ ] Code is formatted: `ruff format .`
- [ ] No lint errors: `ruff check .`
- [ ] The PR description explains **what** changed and **why**
- [ ] Branch is up to date with `main`

---

## Code Style

This project uses **Ruff** for both linting and formatting (configured in `pyproject.toml`).

```bash
# Auto-fix lint issues
ruff check . --fix

# Format all files
ruff format .
```

Key conventions:
- Type hints on all function signatures
- `async def` for all I/O-bound functions
- Loguru (`from loguru import logger`) — no `print()` statements
- Pydantic schemas for all API inputs and outputs
- No bare `except:` — always catch a specific exception type
