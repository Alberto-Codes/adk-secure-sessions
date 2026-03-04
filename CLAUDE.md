# adk-secure-sessions Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-02

## Active Technologies
- Python 3.12 (per `requires-python`) + `cryptography>=44.0.0` (already in `pyproject.toml`)
- stdlib `json`, `asyncio`, `typing` — no additional runtime dependencies beyond `cryptography`
- Dev tooling: ruff (lint/format), ty (type checking), pytest + pytest-asyncio + pytest-mock
- Docs tooling: griffe, mkdocs-gen-files (future MkDocs site)
- Python 3.12 (per `requires-python` in pyproject.toml) + google-adk (BaseSessionService, Session, Event), aiosqlite, cryptography (006-encrypted-session-service)
- SQLite via aiosqlite (async), schema derived from ADK's data model with encrypted columns (006-encrypted-session-service)

## Project Structure

```text
src/adk_secure_sessions/
  __init__.py          # Public API — exports all public symbols
  protocols.py         # EncryptionBackend protocol (PEP 544, @runtime_checkable)
  exceptions.py        # SecureSessionError, EncryptionError, DecryptionError, SerializationError
  serialization.py     # encrypt_session, decrypt_session, encrypt_json, decrypt_json
  backends/
    fernet.py          # FernetBackend — Fernet symmetric encryption
tests/unit/
  test_protocols.py    # Protocol conformance + runtime validation tests
  test_exceptions.py   # Exception hierarchy tests
  test_fernet_backend.py # FernetBackend tests
  test_serialization.py  # Serialization layer tests (envelope, round-trip, edge cases)
scripts/
  gen_ref_pages.py       # MkDocs reference generation
.claude/rules/
  python.md            # Python style rules (scoped to *.py)
  pytest.md            # Test rules (scoped to tests/**/*.py)
```

## Commands

```bash
uv run pytest                                    # Run tests
uv run ruff check .                              # Lint
uv run ruff format .                             # Format
pre-commit run --all-files                       # Full quality pipeline (lint, format, ty, tests, docvet)
```

## Code Style

- Google Python Style Guide (see `.claude/rules/python.md`)
- Google-style docstrings with Examples sections using fenced code blocks
- pytest-mock (`mocker` fixture) over `unittest.mock` (see `.claude/rules/pytest.md`)
- Async-first: all public APIs are `async def`

## Recent Changes
- 006-encrypted-session-service: Added Python 3.12 (per `requires-python` in pyproject.toml) + google-adk (BaseSessionService, Session, Event), aiosqlite, cryptography
- 005-serialization-layer: Implemented serialization module — `encrypt_session`, `decrypt_session`, `encrypt_json`, `decrypt_json` with self-describing envelope format; added `SerializationError` exception
- 004-exception-hierarchy: Exception hierarchy — `SecureSessionError`, `EncryptionError`, `DecryptionError`, `SerializationError`


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
