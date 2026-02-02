# adk-secure-sessions Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-01

## Active Technologies

- Python 3.12 (per pyproject.toml `requires-python`)
- stdlib `typing` only for protocol definitions
- Dev tooling: ruff (lint/format), ty (type checking), pytest + pytest-asyncio + pytest-mock
- Docs tooling: griffe, mkdocs-gen-files (future MkDocs site)

## Project Structure

```text
src/adk_secure_sessions/
  __init__.py          # Public API — exports EncryptionBackend
  protocols.py         # EncryptionBackend protocol (PEP 544, @runtime_checkable)
tests/unit/
  test_protocols.py    # Protocol conformance + runtime validation tests
scripts/
  code_quality_check.sh  # 8-step quality pipeline
  docstring_*.py         # Docstring quality scripts
  gen_ref_pages.py       # MkDocs reference generation
specs/
  002-encryption-backend-protocol/  # Feature spec, plan, tasks, research
.claude/rules/
  python.md            # Python style rules (scoped to *.py)
  pytest.md            # Test rules (scoped to tests/**/*.py)
```

## Commands

```bash
uv run pytest                                    # Run tests
uv run ruff check .                              # Lint
uv run ruff format .                             # Format
bash scripts/code_quality_check.sh --all --verbose  # Full quality pipeline
```

## Code Style

- Google Python Style Guide (see `.claude/rules/python.md`)
- Google-style docstrings with Examples sections using fenced code blocks
- pytest-mock (`mocker` fixture) over `unittest.mock` (see `.claude/rules/pytest.md`)
- Async-first: all public APIs are `async def`

## Recent Changes

- 002-encryption-backend-protocol: `EncryptionBackend` protocol with `encrypt`/`decrypt` async methods, `@runtime_checkable`, full test suite
- Added `scripts/` directory with 8-step code quality pipeline
- Added `.claude/rules/` for contextual Python and pytest rules
- Added dev dependencies: griffe, mkdocs-gen-files, pytest-mock

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
