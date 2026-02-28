# Story 1.1: Test Infrastructure Foundation

Status: done
Branch: feat/test-1-1-infrastructure-foundation
GitHub Issue:

## Story

As a **library maintainer**,
I want **shared test fixtures, conftest files at each test level, and registered pytest markers**,
So that **subsequent test stories have proper infrastructure and the test suite is organized for unit, integration, and benchmark tests**.

## Acceptance Criteria

1. **Given** the test directory structure exists with `tests/unit/` and `tests/integration/`
   **When** I create `tests/conftest.py`, `tests/unit/conftest.py`, and `tests/integration/conftest.py`
   **Then** shared fixtures are available at the appropriate scope, including at minimum: `fernet_backend` fixture, `encryption_key` fixture, `db_path` fixture (temp file), and `encrypted_service` async generator fixture with cleanup
   **And** async generator fixtures use `yield svc; await svc.close()` pattern for database cleanup (NFR19)
   **And** existing inline fixtures (`temp_db_path`, `backend`, `service`) in test files are replaced by the new shared fixtures

2. **Given** `pyproject.toml` defines `[tool.pytest.ini_options]` markers
   **When** I register the `benchmark` marker
   **Then** the markers list includes `"benchmark: Performance benchmark tests"`
   **And** the `integration` marker already exists (no change needed)

3. **Given** conftest files are created and inline fixtures are deduplicated
   **When** I run `uv run pytest`
   **Then** all existing tests are discovered and pass without errors
   **And** code coverage remains >= 90% as enforced by `--cov-fail-under=90`
   **And** `uv run pytest --collect-only` confirms fixture resolution across all test files

## Tasks / Subtasks

- [x] Task 1: Create `tests/conftest.py` with root-level shared fixtures (AC: #1)
  - [x] 1.1 Add `fernet_backend` fixture — returns a fresh `FernetBackend` instance with a test passphrase
  - [x] 1.2 Add `encryption_key` fixture — returns a valid encryption key string for testing
  - [x] 1.3 Add `db_path` fixture — returns a temporary database file path using `tmp_path`
  - [x] 1.4 Add `encrypted_service` async generator fixture — `await svc._init_db()`, `yield svc`, `await svc.close()` (init is required before the service is usable)
  - [x] 1.5 Add module docstring (Google-style: overview, typical usage, See Also)
  - [x] 1.6 Add `from __future__ import annotations` as first import
- [x] Task 2: Create `tests/unit/conftest.py` — placeholder for unit-specific fixtures (AC: #1)
  - [x] 2.1 No unit-specific fixtures needed yet — file serves as a placeholder for future stories
  - [x] 2.2 Add module docstring explaining scope (unit-only fixtures go here)
  - [x] 2.3 Add `from __future__ import annotations` as first import
- [x] Task 3: Create `tests/integration/conftest.py` — placeholder for integration-specific fixtures (AC: #1)
  - [x] 3.1 No integration-specific fixtures needed yet — root conftest covers current needs. Future stories (1.6a, 1.6b) may add fixtures here.
  - [x] 3.2 Add module docstring explaining scope (integration-only fixtures go here)
  - [x] 3.3 Add `from __future__ import annotations` as first import
- [x] Task 4: Register `benchmark` marker in `pyproject.toml` (AC: #2)
  - [x] 4.1 Add `"benchmark: Performance benchmark tests"` to `[tool.pytest.ini_options] markers`
  - [x] 4.2 Verify `integration` marker already exists (it does — no change needed)
- [x] Task 5: Deduplicate fixtures from existing test files (AC: #1, #3)
  - [x] 5.1 In `test_encrypted_session_service.py`: remove inline `temp_db_path` fixture, rename usages to `db_path`; remove inline `backend` fixture, rename usages to `fernet_backend`; remove inline `service` fixture, rename usages to `encrypted_service`
  - [x] 5.2 In `test_adk_integration.py`: remove inline `temp_db_path` fixture, rename usages to `db_path`; remove inline `backend` fixture, rename usages to `fernet_backend`
  - [x] 5.3 Keep `_MockBackend` and `_BadDecryptBackend` local to `test_serialization.py` — these are test doubles, not shared fixtures
  - [x] 5.4 Run `uv run pytest` after each file migration to catch breakage early
- [x] Task 6: Verify test discovery, coverage, and cleanup (AC: #3)
  - [x] 6.1 Run `uv run pytest` and verify all existing tests discovered and pass without errors
  - [x] 6.2 Run `uv run pytest --collect-only` to verify fixture resolution across all test files
  - [x] 6.3 Verify code coverage remains >= 90% (no silently dropped tests)
  - [x] 6.4 Verify async generator fixtures properly close database connections
  - [x] 6.5 Run `bash scripts/code_quality_check.sh --all --verbose` to verify full pipeline passes

## AC-to-Test Mapping

| AC # | Test(s) | Status |
|------|---------|--------|
| 1 | `tests/conftest.py` (fixtures exist), `test_encrypted_session_service.py` (uses shared fixtures), `test_adk_integration.py` (uses shared fixtures) | pass |
| 2 | `pyproject.toml` markers list includes benchmark | pass |
| 3 | `uv run pytest` — 119 tests pass, 99.66% coverage >= 90%, `--collect-only` confirms fixture resolution | pass |

## Dev Notes

### What Already Exists

The project has extensive test infrastructure already in place:
- **6 test files** (~2,600 lines) covering protocols, exceptions, backends, serialization, service, and integration
- **pytest config** in `pyproject.toml` with markers (`unit`, `integration`, `slow`), `asyncio_mode = "auto"`, filterwarnings, and testpaths
- **CI pipeline** (`.github/workflows/tests.yml`) with Python 3.12 + google-adk version matrix, lint → format → type check → tests (90% coverage)
- **Quality script** (`scripts/code_quality_check.sh`) — 8-step pipeline
- **Async fixture patterns** already used in `test_encrypted_session_service.py` and `test_adk_integration.py`

### What This Story Creates

The **missing pieces** are conftest files and the `benchmark` marker:
- `tests/conftest.py` — does NOT exist yet
- `tests/unit/conftest.py` — does NOT exist yet
- `tests/integration/conftest.py` — does NOT exist yet
- `benchmark` marker — NOT registered in pyproject.toml yet

### Fixture Consolidation Strategy

Existing test files define their own fixtures inline. The main deduplication targets are:

**`test_encrypted_session_service.py`** (unit) defines:
- `temp_db_path` fixture — `str(tmp_path / "test.db")`
- `backend` fixture — `FernetBackend(key="test-passphrase")`
- `service` fixture — async generator with `yield svc; await svc.close()`

**`test_adk_integration.py`** (integration) defines:
- `temp_db_path` fixture — same pattern
- `backend` fixture — same pattern

**`test_fernet_backend.py`** (unit) uses inline `FernetBackend` construction (no fixtures)

**`test_serialization.py`** (unit) defines its own `_MockBackend` class (should remain local — it's a test double, not a shared fixture)

**Decision**: Move common `temp_db_path`, `backend` (as `fernet_backend`), and `encrypted_service` to the root `tests/conftest.py`. Keep test-file-specific fixtures and mock implementations local to their test files.

### Critical Patterns to Follow

1. **`from __future__ import annotations`** — required as first import in every new file
2. **Absolute imports only** — `from adk_secure_sessions.backends.fernet import FernetBackend`, never relative
3. **Function scope** (default) for all fixtures — fresh instance per test
4. **Async generator** pattern for service fixtures: `yield svc; await svc.close()`
5. **Google-style docstrings** on all fixtures with Examples sections using fenced code blocks
6. **No `@pytest.mark.asyncio`** — `asyncio_mode = "auto"` handles it; adding the decorator is redundant
7. **`pytest-mock` only** — never `unittest.mock`, `Mock()`, or `patch()` directly

### Imports Required for Conftest Files

```python
from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

from adk_secure_sessions.backends.fernet import FernetBackend
from adk_secure_sessions.serialization import BACKEND_FERNET
from adk_secure_sessions.services.encrypted_session import EncryptedSessionService
```

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| None | No user-facing changes — internal test infrastructure only |

### Project Structure Notes

- Source tree: `src/adk_secure_sessions/` (protocols, exceptions, serialization, backends/, services/)
- Test tree: `tests/unit/` and `tests/integration/`
- Conftest files go at `tests/`, `tests/unit/`, and `tests/integration/`
- No `__init__.py` in test directories (pytest handles discovery via `testpaths = ["tests"]`)

### Existing Marker Registration (pyproject.toml)

Current markers:
```toml
markers = [
    "unit: Unit tests - fast, isolated",
    "integration: Integration tests with real databases",
    "slow: Slow-running tests",
]
```

Add:
```toml
    "benchmark: Performance benchmark tests",
```

### Known Design Note: `encrypted_service` Scope

The `encrypted_service` fixture lives at root `tests/conftest.py` with a real `FernetBackend` + real SQLite. This means unit tests that use it are technically integration tests (real backend + real DB). The dev-quality-checklist states: "Unit tests — mock the EncryptionBackend to isolate persistence logic, OR mock the DB to isolate encryption logic. Never mock both or neither." The existing `test_encrypted_session_service.py` already uses this pattern (marked `unit` but uses real deps). This is a downstream cleanup opportunity — not a blocker for this story. Future stories may move `encrypted_service` to `tests/integration/conftest.py` and introduce mock-based service fixtures for true unit isolation.

### NFR19 Compliance

All async fixtures that create services with DB connections MUST:
1. Use async generator pattern with `yield`
2. Call `await svc.close()` after yield
3. Verify no leaked database connections after test teardown

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Phase 2 Structural Action Items]
- [Source: .claude/rules/pytest.md#Fixtures]
- [Source: .claude/rules/dev-quality-checklist.md#Async Test Hygiene]
- [Source: _bmad-output/project-context.md#Testing Rules]
- [Source: .claude/rules/conventions.md#Async-First by Design]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, 99.66% coverage
- [x] `bash scripts/code_quality_check.sh --all --verbose` -- full quality pipeline green

## Code Review

- **Reviewer:** Claude Opus 4.6 (adversarial code-review workflow)
- **Outcome:** Changes Requested → Fixed

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | MED | Missing pytestmark markers on test_encrypted_session_service.py | Added `pytestmark = pytest.mark.unit` |
| 2 | MED | Missing pytestmark markers on test_adk_integration.py | Added `pytestmark = pytest.mark.integration` |
| 3 | LOW | Integration-grade docstring note missing on encrypted_service fixture | Added note about real deps |
| 4 | LOW | RST backtick notation in placeholder conftest docstrings | Fixed to standard backticks |
| 5 | LOW | Sync example in encryption_key fixture docstring | Fixed to match async-first pattern |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

- 2026-02-28: Implemented test infrastructure foundation — created 3 conftest files, registered benchmark marker, deduplicated inline fixtures from 2 test files, verified 119 tests pass with 99.66% coverage
- 2026-02-28: Code review fixes — added pytestmark markers to test_encrypted_session_service.py (unit) and test_adk_integration.py (integration), added integration-grade docstring note to encrypted_service fixture, fixed RST backtick notation in placeholder conftest docstrings, fixed sync example in encryption_key fixture docstring
- 2026-02-28: Adopted docvet BMAD workflow customizations — updated create-story template with Branch, GitHub Issue, AC-to-Test Mapping, Documentation Impact, Quality Gates, Code Review sections; updated create-story instructions with branch population, doc impact assessment, GitHub issue automation; added Step 4b (branch creation) and enhanced Step 9 DoD in dev-story; added SonarQube integration to code-review; backfilled new sections on this story

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Ran `uv run pytest` after each deduplication step to catch breakage early
- Ran `uv run pytest --collect-only` confirming 119 tests collected with proper fixture resolution
- Ran `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` — 99.66% coverage (295 stmts, 1 miss)
- Ran `bash scripts/code_quality_check.sh --all --verbose` — all 8 steps passed, ruff auto-fixed 2 minor issues

### Completion Notes List

- Created `tests/conftest.py` with 4 shared fixtures: `encryption_key`, `fernet_backend`, `db_path`, `encrypted_service`
- `encrypted_service` uses async generator pattern with `yield svc; await svc.close()` (NFR19 compliant)
- `fernet_backend` depends on `encryption_key` fixture for test passphrase consistency
- Created `tests/unit/conftest.py` and `tests/integration/conftest.py` as placeholders with module docstrings
- Registered `benchmark` marker in `pyproject.toml` (verified `integration` marker already exists)
- Deduplicated `test_encrypted_session_service.py`: removed 3 inline fixtures (`temp_db_path` → `db_path`, `backend` → `fernet_backend`, `service` → `encrypted_service`), renamed all usages
- Deduplicated `test_adk_integration.py`: removed 2 inline fixtures (`temp_db_path` → `db_path`, `backend` → `fernet_backend`), renamed all usages
- Kept `_MockBackend` local to `test_serialization.py` (test double, not shared)
- All 119 tests pass, 99.66% coverage, full quality pipeline green
- Removed unused `TYPE_CHECKING` imports from both deduplicated test files (ruff auto-cleanup)

### File List

- tests/conftest.py (new)
- tests/unit/conftest.py (new)
- tests/integration/conftest.py (new)
- pyproject.toml (modified — added benchmark marker)
- tests/unit/test_encrypted_session_service.py (modified — removed inline fixtures, renamed usages)
- tests/integration/test_adk_integration.py (modified — removed inline fixtures, renamed usages)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — status tracking)
- _bmad-output/implementation-artifacts/1-1-test-infrastructure-foundation.md (modified — status tracking)
