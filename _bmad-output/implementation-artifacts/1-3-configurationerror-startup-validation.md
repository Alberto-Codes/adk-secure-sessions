# Story 1.3: ConfigurationError & Startup Validation

Status: review
Branch: feat/session-1-3-configurationerror-startup-validation
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/44

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer using the library**,
I want **clear error messages when I misconfigure EncryptedSessionService**,
so that **I catch bad encryption keys or invalid backends at startup, not as cryptic runtime failures**.

## Acceptance Criteria

1. **Given** `ConfigurationError` does not exist in the exception hierarchy
   **When** I add `ConfigurationError` as a subclass of `SecureSessionError` to `exceptions.py`
   **Then** `ConfigurationError` is exported from `__init__.py` and appears in `__all__`
   **And** `ConfigurationError` has a Google-style docstring with an Examples section

2. **Given** an `EncryptedSessionService` is instantiated with an empty encryption key
   **When** the constructor validates the configuration
   **Then** a `ConfigurationError` is raised with a message specifying the expected key format

3. **Given** an `EncryptedSessionService` is instantiated with a backend that does not satisfy `EncryptionBackend` protocol
   **When** the constructor validates the backend
   **Then** a `ConfigurationError` is raised indicating the backend does not conform to the protocol

4. **Given** a valid encryption key and backend are provided
   **When** the constructor validates the configuration
   **Then** no error is raised and the service initializes normally

5. **And** ADR-006 is created documenting the ConfigurationError decision, following ADR-005's format, citing the "add when code demands" principle, and including: context, decision, rationale, consequences, and alternatives considered

6. **And** the error message never includes the encryption key value (FR25/NFR6)

7. **And** database connection failures raise exceptions that include the database file path, OS error code, and suggested remediation (NFR14)

8. **And** all existing tests pass

## Tasks / Subtasks

- [x] Task 1: Add `ConfigurationError` to exception hierarchy (AC: #1)
  - [x] 1.1 Add `class ConfigurationError(SecureSessionError)` to `src/adk_secure_sessions/exceptions.py` with Google-style docstring and Examples section using fenced code blocks
  - [x] 1.2 Add `ConfigurationError` to imports in `src/adk_secure_sessions/__init__.py`
  - [x] 1.3 Add `ConfigurationError` to `__all__` in alphabetical position (between `BACKEND_FERNET` and `DecryptionError`)
  - [x] 1.4 Update module docstring `Attributes:` section in `__init__.py` to include `ConfigurationError`
- [x] Task 2: Update `FernetBackend` to raise `ConfigurationError` (AC: #2, #6)
  - [x] 2.1 Add `from adk_secure_sessions.exceptions import ConfigurationError` to `backends/fernet.py`
  - [x] 2.2 Replace `TypeError` raise for non-str/bytes key with `ConfigurationError`
  - [x] 2.3 Replace `ValueError` raise for empty key with `ConfigurationError`
  - [x] 2.4 Verify error messages do NOT include the key value (FR25/NFR6) — current messages are already safe
  - [x] 2.5 Update existing `FernetBackend` tests to expect `ConfigurationError` instead of `TypeError`/`ValueError`
- [x] Task 3: Add constructor validation to `EncryptedSessionService` (AC: #2, #3, #4)
  - [x] 3.1 Add `isinstance(backend, EncryptionBackend)` check in `__init__`, raise `ConfigurationError` if fails
  - [x] 3.2 Validate `backend_id` is an `int`, raise `ConfigurationError` if not
  - [x] 3.3 Validate `db_path` is a non-empty string, raise `ConfigurationError` if not
  - [x] 3.4 Update `__init__` docstring `Raises:` section to document `ConfigurationError`
- [x] Task 4: Enrich database connection error messages (AC: #7)
  - [x] 4.1 Wrap `aiosqlite.connect()` call in `_init_db` with try/except for `sqlite3.OperationalError` and `OSError`
  - [x] 4.2 Re-raise as `ConfigurationError` with message including: db_path, original error type, OS error code (if present), and remediation hint ("check path exists and is writable")
  - [x] 4.3 Use `raise ConfigurationError(msg) from exc` for proper exception chaining
- [x] Task 5: Write tests (AC: #1-#4, #6, #7, #8)
  - [x] 5.1 Unit tests for `ConfigurationError` class: inheritance from `SecureSessionError`, docstring exists, can be caught by parent
  - [x] 5.2 Unit tests for `FernetBackend` key validation: empty str key, empty bytes key, non-str-bytes key → all raise `ConfigurationError`
  - [x] 5.3 Unit tests for `EncryptedSessionService.__init__` validation: invalid backend (not EncryptionBackend), invalid backend_id (non-int), empty db_path
  - [x] 5.4 Unit test: valid construction does not raise (happy path)
  - [x] 5.5 Unit test: error messages do not contain key material
  - [x] 5.6 Integration test: database connection failure with bad path produces enriched error message
  - [x] 5.7 Run full suite: `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90`
- [x] Task 6: Create ADR-006 (AC: #5)
  - [x] 6.1 Create `docs/adr/ADR-006-configuration-error.md` following ADR-005's format
  - [x] 6.2 Include: Context (FR15, ADR-005's "add when code demands" principle), Decision, Rationale, Consequences, Alternatives Considered
  - [x] 6.3 Add ADR-006 entry to `docs/adr/index.md`
- [x] Task 7: Run full quality pipeline (AC: #8)
  - [x] 7.1 Run `uv run ruff check .` — zero violations
  - [x] 7.2 Run `uv run ruff format --check .` — zero format issues
  - [x] 7.3 Run `uv run ty check` — zero type errors (src/ only)
  - [x] 7.4 Run `bash scripts/code_quality_check.sh --all --verbose` — all 8 steps pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_exceptions.py::TestConfigurationErrorHierarchy` (10 tests: inheritance, caught-by-base, sibling independence, chaining, docstring, message) | pass |
| 2    | `test_fernet_backend.py::TestFlexibleKeyInput::test_empty_string_key_raises_configuration_error`, `test_empty_bytes_key_raises_configuration_error`; `test_encrypted_session_service.py::TestConstructorValidation::test_invalid_backend_raises_configuration_error` | pass |
| 3    | `test_encrypted_session_service.py::TestConstructorValidation::test_invalid_backend_raises_configuration_error`, `test_error_message_includes_backend_type_name` | pass |
| 4    | `test_encrypted_session_service.py::TestConstructorValidation::test_valid_construction_does_not_raise` | pass |
| 5    | Manual verification: `docs/adr/ADR-006-configuration-error.md` created following ADR-005 format, `docs/adr/index.md` updated | pass |
| 6    | `test_fernet_backend.py::TestPolish::test_key_validation_errors_do_not_contain_key_material`; `test_encrypted_session_service.py::TestConstructorValidation::test_error_message_does_not_contain_key_material` | pass |
| 7    | `test_encrypted_session_service.py::TestEdgeCases::test_database_connection_errors_raise_configuration_error` | pass |
| 8    | Full suite: 154 tests pass, 99.68% coverage (>=90% threshold) | pass |

## Dev Notes

### What This Story Changes

**Four production files + one ADR.** This story adds a new exception class, startup validation to the service constructor and backend, and enriched DB connection error messages. It changes behavior for misconfigured services — errors that previously raised generic `ValueError`/`TypeError` (from FernetBackend) or `sqlite3.OperationalError` (from aiosqlite) now raise `ConfigurationError` with actionable messages.

### Exact Change Locations

**File 1:** `src/adk_secure_sessions/exceptions.py`
- Add `class ConfigurationError(SecureSessionError)` after `SerializationError` (line ~103)
- Follow the exact pattern of existing exceptions: Google-style docstring with Examples section using fenced code blocks
- Current hierarchy: `SecureSessionError` → `EncryptionError`, `DecryptionError`, `SerializationError`
- After change: `SecureSessionError` → `EncryptionError`, `DecryptionError`, `SerializationError`, `ConfigurationError`

**File 2:** `src/adk_secure_sessions/__init__.py`
- Add `ConfigurationError` to the import from `exceptions` (line 45-50)
- Add `"ConfigurationError"` to `__all__` in alphabetical position (between `"BACKEND_FERNET"` and `"DecryptionError"` on line ~63)
- Update the module docstring `Attributes:` block to include `ConfigurationError`

**File 3:** `src/adk_secure_sessions/backends/fernet.py`
- Add import: `from adk_secure_sessions.exceptions import ConfigurationError` (alongside existing `DecryptionError` import, line 35)
- Change `TypeError` raise on line 79 to `ConfigurationError`
- Change `ValueError` raise on line 86 to `ConfigurationError`
- Error messages are already safe (no key material) — verify, don't change

**File 4:** `src/adk_secure_sessions/services/encrypted_session.py`
- Add `from adk_secure_sessions.exceptions import ConfigurationError` to imports (after line 40)
- Add validation block in `__init__` (after line 152, before `self._db_path = db_path`):
  ```python
  if not isinstance(db_path, str) or not db_path:
      msg = "db_path must be a non-empty string"
      raise ConfigurationError(msg)
  if not isinstance(backend, EncryptionBackend):
      msg = (
          f"backend must conform to EncryptionBackend protocol, "
          f"got {type(backend).__name__}"
      )
      raise ConfigurationError(msg)
  if not isinstance(backend_id, int):
      msg = f"backend_id must be an int, got {type(backend_id).__name__}"
      raise ConfigurationError(msg)
  ```
- Wrap `aiosqlite.connect()` in `_init_db` (line 161) with try/except:
  ```python
  try:
      self._connection = await aiosqlite.connect(self._db_path)
  except (OSError, sqlite3.OperationalError) as exc:
      error_code = getattr(exc, "errno", None) or ""
      msg = (
          f"Failed to connect to database at '{self._db_path}': {exc}. "
          f"Check that the path exists and is writable."
      )
      raise ConfigurationError(msg) from exc
  ```
- Add `import sqlite3` to imports (stdlib)
- Update `__init__` docstring `Raises:` section

**File 5:** `docs/adr/ADR-006-configuration-error.md` (NEW)
- Follow ADR-005 format exactly: Status, Date, Deciders, Context, Decision, Consequences, Alternatives Considered
- Reference ADR-005's "add when code demands" principle as the trigger
- Document: covers bad key format, empty key, invalid backend_id, missing backend, bad db_path
- Note: `DatabaseConnectionError` deferred to Phase 3 (Architecture Decision 2)

**File 6:** `docs/adr/index.md`
- Add ADR-006 entry in sequence

### Existing Test Updates Required

FernetBackend tests in `tests/unit/test_fernet_backend.py` currently assert `ValueError` and `TypeError` for bad keys. These must be updated to expect `ConfigurationError`:

- `test_empty_string_key_raises_value_error` → rename to `test_empty_string_key_raises_configuration_error`, change `pytest.raises(ValueError)` to `pytest.raises(ConfigurationError)`
- `test_empty_bytes_key_raises_value_error` → rename to `test_empty_bytes_key_raises_configuration_error`
- `test_non_str_bytes_key_raises_type_error` → rename to `test_non_str_bytes_key_raises_configuration_error`

The test class `TestFlexibleKeyInput` and `TestPolish` in that file have these tests.

### Architecture Decision 2 Compliance

Per architecture Decision 2:
- **DO** add `ConfigurationError` as `SecureSessionError` subclass
- **DO NOT** add `DatabaseConnectionError` — defer to Phase 3
- **DO** wrap database connection errors in `ConfigurationError` with enriched messages (NFR14)
- **DO** follow ADR-005's principle: "Add a subclass when a caller has a concrete need to handle a failure mode differently in a `try/except` block"

### Security Guardrails (FR25/NFR6)

Error messages must NEVER include:
- The encryption key value
- Plaintext or ciphertext
- Backend internal state

Current FernetBackend error messages are already safe:
- `"key must be str or bytes, got {type}"` — includes type name only, not key value
- `"key must not be empty"` — no key value

Service constructor messages should follow the same pattern:
- Include the type/class name of invalid arguments
- Include the db_path for connection errors (it's a file path, not sensitive)
- Never include the key or backend state

### Previous Story Intelligence (1.2)

**Patterns established:**
- `from __future__ import annotations` as first import in every new file
- Absolute imports only: `from adk_secure_sessions.backends.fernet import FernetBackend`
- Google-style docstrings with `Examples:` sections using fenced code blocks (NOT `::` directive in function/class docstrings)
- `pytestmark = pytest.mark.unit` at module level in unit test files
- Shared fixtures: `encrypted_service`, `fernet_backend`, `db_path`, `encryption_key` in `tests/conftest.py`
- Async generator fixture pattern: `yield svc; await svc.close()`
- No `@pytest.mark.asyncio` — `asyncio_mode = "auto"` handles it
- 135 tests passing at 99.66% coverage before this story
- Exception message pattern: `msg = "..."; raise SomeError(msg)` (ruff TRY003)
- Exception chaining: always `raise X(msg) from exc` or `raise X(msg) from None`

**Review findings from 1.1/1.2 to avoid repeating:**
- Always add `pytestmark` to test files (MED finding from 1.1)
- Use standard backticks, not RST notation in function/class docstrings (LOW finding from 1.1)
- Add pk assertion when testing PRAGMA columns (L1 from 1.2 review)

### Critical Guardrails

- **DO NOT** add `DatabaseConnectionError` — deferred to Phase 3 per Architecture Decision 2
- **DO NOT** include key values in any error message
- **DO NOT** change the `EncryptionBackend` Protocol definition
- **DO NOT** change any public method signatures on `EncryptedSessionService`
- **DO** validate in `__init__` (synchronous, before any async work)
- **DO** use `isinstance(backend, EncryptionBackend)` for protocol check (it's `@runtime_checkable`)
- **DO** use `raise ConfigurationError(msg) from exc` for exception chaining
- **DO** update existing FernetBackend tests to expect `ConfigurationError` instead of `ValueError`/`TypeError`
- **DO** use the `msg = "..."; raise X(msg)` pattern (ruff TRY003)
- **DO** follow ADR-005 format for ADR-006

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/adr/ADR-006-configuration-error.md` | New ADR documenting ConfigurationError decision |
| `docs/adr/index.md` | Add ADR-006 entry |
| `docs/reference/` | Auto-generated by griffe — no manual update needed |

### Project Structure Notes

- Source: `src/adk_secure_sessions/exceptions.py` (add class), `__init__.py` (export), `backends/fernet.py` (change raises), `services/encrypted_session.py` (add validation)
- Tests: `tests/unit/test_fernet_backend.py` (update existing), `tests/unit/test_encrypted_session_service.py` (new tests), possibly `tests/unit/test_exceptions.py` (new tests)
- New file: `docs/adr/ADR-006-configuration-error.md`
- Updated file: `docs/adr/index.md`
- No new modules or `__init__.py` changes beyond exports
- Aligned with existing project structure — no variances

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2: Exception Hierarchy Evolution]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- [Source: docs/adr/ADR-005-exception-hierarchy.md#When to Add Subclasses]
- [Source: .claude/rules/conventions.md#Protocols Over Inheritance]
- [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- [Source: _bmad-output/implementation-artifacts/1-2-schema-reservation-for-optimistic-concurrency.md#Dev Notes]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 154 passed, 99.68% coverage
- [x] `bash scripts/code_quality_check.sh --all --verbose` -- all 8 steps pass (pre-existing docstring enrichment opportunities and 1 pre-existing type diagnostic in tests unrelated to this story)

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
| 2026-02-28 | Implemented ConfigurationError exception, FernetBackend key validation migration, EncryptedSessionService constructor validation, enriched DB connection errors, ADR-006, and 19 new tests |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No blocking issues encountered during implementation.

### Completion Notes List

- Added `ConfigurationError(SecureSessionError)` to `exceptions.py` with Google-style docstring and fenced code block Examples section
- Migrated `FernetBackend.__init__` from `TypeError`/`ValueError` to `ConfigurationError` for key validation errors
- Added synchronous constructor validation to `EncryptedSessionService.__init__`: validates `db_path` (non-empty string), `backend` (EncryptionBackend protocol), `backend_id` (int)
- Wrapped `aiosqlite.connect()` in `_init_db` with `try/except (OSError, sqlite3.OperationalError)`, re-raising as `ConfigurationError` with enriched message (db path, error code, remediation hint) and proper exception chaining
- Updated `__init__.py` exports: import, `__all__`, module docstring Attributes
- Created `docs/adr/ADR-006-configuration-error.md` following ADR-005 format with context, decision, consequences, and alternatives
- Updated `docs/adr/index.md` with ADR-006 entry
- All error messages verified to exclude key material (FR25/NFR6)
- 154 tests pass with 99.68% coverage

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/adr/ADR-006-configuration-error.md` | New ADR documenting ConfigurationError decision |
| `docs/adr/index.md` | Added ADR-006 entry |
| `docs/reference/` | Auto-generated by griffe — no manual update needed |

### File List

- `src/adk_secure_sessions/exceptions.py` (modified — added ConfigurationError class)
- `src/adk_secure_sessions/__init__.py` (modified — added ConfigurationError to imports, __all__, docstring)
- `src/adk_secure_sessions/backends/fernet.py` (modified — import ConfigurationError, changed raises from TypeError/ValueError)
- `src/adk_secure_sessions/services/encrypted_session.py` (modified — added import sqlite3, ConfigurationError; added constructor validation; wrapped _init_db connection)
- `tests/unit/test_exceptions.py` (modified — added TestConfigurationErrorHierarchy, updated parametrize)
- `tests/unit/test_fernet_backend.py` (modified — updated 3 tests to expect ConfigurationError, added key material safety test)
- `tests/unit/test_encrypted_session_service.py` (modified — added TestConstructorValidation class, updated DB connection error test)
- `docs/adr/ADR-006-configuration-error.md` (new)
- `docs/adr/index.md` (modified — added ADR-006 row)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status updated)
- `_bmad-output/implementation-artifacts/1-3-configurationerror-startup-validation.md` (modified — task checkboxes, AC mapping, dev record)
