# Story 1.2: Schema Reservation for Optimistic Concurrency

Status: review
Branch: feat/session-1-2-schema-version-reservation
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/42

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **library maintainer**,
I want **a `version INTEGER DEFAULT 1` column on `sessions`, `app_states`, and `user_states` tables**,
So that **early adopters won't face a breaking schema migration when Phase 3 optimistic concurrency ships**.

## Acceptance Criteria

1. **Given** the `_init_db` method in `EncryptedSessionService` creates the database schema
   **When** the schema is initialized on a fresh database
   **Then** the `sessions` table has a `version` column with `INTEGER DEFAULT 1`
   **And** the `app_states` table has a `version` column with `INTEGER DEFAULT 1`
   **And** the `user_states` table has a `version` column with `INTEGER DEFAULT 1`
   **And** the `events` table does NOT have a `version` column (append-only, excluded per Architecture Decision 1)

2. **Given** a test verifies column metadata
   **When** `PRAGMA table_info(<table>)` is executed for each table
   **Then** the `version` column exists with type `INTEGER` and default value `1`
   **And** the `events` table has no `version` column

3. **Given** the schema now includes `version` columns
   **When** existing CRUD operations are executed (create, get, list, delete session; append event; upsert app/user state)
   **Then** no INSERT, UPDATE, or SELECT statement references the `version` column (column is purely reserved and inert)
   **And** all existing tests pass unchanged
   **And** code coverage remains >= 90%

## Tasks / Subtasks

- [x] Task 1: Add `version INTEGER DEFAULT 1` to `sessions` CREATE TABLE in `_SCHEMA` (AC: #1)
  - [x] 1.1 In `src/adk_secure_sessions/services/encrypted_session.py`, locate the `_SCHEMA` constant
  - [x] 1.2 Add `version INTEGER DEFAULT 1` column to the `sessions` table DDL (after `update_time`)
- [x] Task 2: Add `version INTEGER DEFAULT 1` to `app_states` CREATE TABLE in `_SCHEMA` (AC: #1)
  - [x] 2.1 Add `version INTEGER DEFAULT 1` column to the `app_states` table DDL (after `update_time`)
- [x] Task 3: Add `version INTEGER DEFAULT 1` to `user_states` CREATE TABLE in `_SCHEMA` (AC: #1)
  - [x] 3.1 Add `version INTEGER DEFAULT 1` column to the `user_states` table DDL (after `update_time`)
- [x] Task 4: Verify `events` table has NO `version` column (AC: #1)
  - [x] 4.1 Confirm `events` CREATE TABLE has no `version` column (append-only, per Architecture Decision 1)
- [x] Task 5: Verify zero query changes (AC: #3)
  - [x] 5.1 Audit all INSERT, UPDATE, SELECT, DELETE statements — none reference `version`
  - [x] 5.2 Run `uv run pytest` to confirm all existing tests pass unchanged
- [x] Task 6: Write schema verification tests (AC: #2)
  - [x] 6.1 Add `TestSchemaVersionColumn` class in `tests/unit/test_encrypted_session_service.py`
  - [x] 6.2 Parametrized test: for each of `sessions`, `app_states`, `user_states` — assert `version` column exists with type `INTEGER` and default `1` via `PRAGMA table_info`
  - [x] 6.3 Negative test: assert `events` table does NOT have a `version` column
  - [x] 6.4 Run `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` — all tests pass, coverage >= 90%
- [x] Task 7: Run full quality pipeline (AC: #3)
  - [x] 7.1 Run `bash scripts/code_quality_check.sh --all --verbose` — all steps pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_encrypted_session_service.py::TestSchemaVersionColumn::test_version_column_exists_with_correct_default[sessions/app_states/user_states]` + `test_events_table_has_no_version_column` | pass |
| 2    | `test_encrypted_session_service.py::TestSchemaVersionColumn::test_version_column_exists_with_correct_default` (PRAGMA table_info: type=INTEGER, dflt_value=1) | pass |
| 3    | 119 existing tests pass unchanged + 4 new tests = 123 total, 99.66% coverage | pass |

## Dev Notes

### What This Story Changes

**One file, one constant.** The `_SCHEMA` string constant in `src/adk_secure_sessions/services/encrypted_session.py` (lines ~36-82) contains all CREATE TABLE DDL. Add `version INTEGER DEFAULT 1` to three of the four tables. Zero query changes. Zero behavior changes.

### Exact Change Location

**File:** `src/adk_secure_sessions/services/encrypted_session.py`
**Constant:** `_SCHEMA` (module-level, triple-quoted string)

Current tables in `_SCHEMA`:
- `app_states` — PRIMARY KEY `(app_name)` — ADD `version INTEGER DEFAULT 1`
- `user_states` — PRIMARY KEY `(app_name, user_id)` — ADD `version INTEGER DEFAULT 1`
- `sessions` — PRIMARY KEY `(app_name, user_id, id)` — ADD `version INTEGER DEFAULT 1`
- `events` — PRIMARY KEY `(app_name, user_id, session_id, id)` — DO NOT ADD `version`

### SQL Statements That Must NOT Change

These 8 SQL operations exist in the file and must remain untouched (no `version` references):

1. `INSERT INTO sessions (app_name, user_id, id, state, create_time, update_time)` — create_session
2. `SELECT 1 FROM sessions WHERE app_name = ? AND user_id = ? AND id = ?` — duplicate check
3. `SELECT state, update_time FROM sessions WHERE ...` — get_session
4. `SELECT id, user_id, state, update_time FROM sessions WHERE ...` — list_sessions
5. `DELETE FROM sessions WHERE ...` — delete_session
6. `INSERT INTO app_states ... ON CONFLICT ... DO UPDATE` — _upsert_app_state
7. `INSERT INTO user_states ... ON CONFLICT ... DO UPDATE` — _upsert_user_state
8. `INSERT INTO events ...` — append_event

### Why the Column Is Inert

Phase 2 uses SQLite with aiosqlite's single-writer connection model — concurrent writes are serialized automatically. The `version` column enables Phase 3 optimistic concurrency when PostgreSQL introduces true multi-writer scenarios. Reserving it now avoids a breaking migration for early adopters.

[Source: _bmad-output/planning-artifacts/architecture.md#Decision 1]

### Testing Strategy

**PRAGMA table_info** returns rows: `(cid, name, type, notnull, dflt_value, pk)`.
- For `sessions`, `app_states`, `user_states`: assert a row exists where `name == "version"`, `type == "INTEGER"`, `dflt_value == "1"`
- For `events`: assert NO row has `name == "version"`
- Use the `encrypted_service` fixture from `tests/conftest.py` — it initializes the DB via `_init_db()`
- Access the connection via `service._connection` (already initialized by the fixture's `await svc._init_db()`)

### Previous Story Intelligence (1.1)

**Patterns established:**
- `from __future__ import annotations` as first import in every new file
- Absolute imports only: `from adk_secure_sessions.backends.fernet import FernetBackend`
- Google-style docstrings with `Examples:` sections using fenced code blocks
- `pytestmark = pytest.mark.unit` at module level in unit test files
- Shared fixtures: `encrypted_service`, `fernet_backend`, `db_path`, `encryption_key` in `tests/conftest.py`
- Async generator fixture pattern: `yield svc; await svc.close()`
- No `@pytest.mark.asyncio` — `asyncio_mode = "auto"` handles it
- 119 tests passing at 99.66% coverage before this story

**Review findings from 1.1 to avoid repeating:**
- Always add `pytestmark` to test files (MED finding)
- Use standard backticks, not RST notation (LOW finding)

### Critical Guardrails

- **DO NOT** add `version` to any INSERT, UPDATE, SELECT, or DELETE statement
- **DO NOT** add `version` to the `events` table
- **DO NOT** modify any existing SQL query strings
- **DO NOT** change any method signatures or public API
- **DO** place the column after the last existing column in each CREATE TABLE (before closing parenthesis)
- **DO** use exact syntax: `version INTEGER DEFAULT 1` (not `DEFAULT '1'`, not `NOT NULL`)

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| None | No user-facing changes — internal schema reservation only |

### Project Structure Notes

- Source: `src/adk_secure_sessions/services/encrypted_session.py` (only production file touched)
- Tests: `tests/unit/test_encrypted_session_service.py` (new test class added)
- No new files created, no modules added, no `__init__.py` changes
- Aligned with existing project structure — no variances

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1: Schema Reservation for Optimistic Concurrency]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- [Source: .claude/rules/conventions.md#Own Our Schema]
- [Source: docs/adr/ADR-004-adk-schema-compatibility.md]
- [Source: _bmad-output/project-context.md#Database Layer]
- [Source: _bmad-output/implementation-artifacts/1-1-test-infrastructure-foundation.md#Dev Notes]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 123 tests pass, 99.66% coverage
- [x] `bash scripts/code_quality_check.sh --all --verbose` -- full quality pipeline green

## Code Review

- **Reviewer:**
- **Outcome:**

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
|   |          |         |            |

### Verification

- [ ] All HIGH findings resolved
- [ ] All MEDIUM findings resolved or accepted
- [ ] Tests pass after review fixes
- [ ] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-02-28 | Implemented schema reservation — added `version INTEGER DEFAULT 1` to sessions, app_states, user_states tables; verified events table excluded; added 4 schema verification tests; 123 tests pass at 99.66% coverage |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Ran `uv run pytest` after schema changes (Tasks 1-3) — 119 existing tests pass unchanged
- Ran `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90 -v` — 123 tests pass, 99.66% coverage
- Ran `bash scripts/code_quality_check.sh --all --verbose` — all 8 steps passed, ruff reformatted 1 file (trailing comma)

### Completion Notes List

- Added `version INTEGER DEFAULT 1` to `app_states` table (after `update_time`, before closing `)`)
- Added `version INTEGER DEFAULT 1` to `user_states` table (after `update_time`, before `PRIMARY KEY`)
- Added `version INTEGER DEFAULT 1` to `sessions` table (after `update_time`, before `PRIMARY KEY`)
- Confirmed `events` table has NO `version` column (append-only, Architecture Decision 1)
- Audited all 8 SQL operations — none reference `version` (column is purely inert)
- Added `TestSchemaVersionColumn` class with parametrized positive test (3 tables) and negative test (events)
- Tests use `PRAGMA table_info` to verify column name, type, notnull, and default value
- 119 existing tests pass unchanged (zero regressions), 4 new tests added = 123 total
- Coverage unchanged at 99.66%

### File List

- src/adk_secure_sessions/services/encrypted_session.py (modified — `_SCHEMA` constant: added version column to 3 tables)
- tests/unit/test_encrypted_session_service.py (modified — added `TestSchemaVersionColumn` class with 4 tests)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — status tracking)
- _bmad-output/implementation-artifacts/1-2-schema-reservation-for-optimistic-concurrency.md (modified — story tracking)
