# Story 7.4: Test Migration & Conformance Verification

Status: done
Branch: feat/test-7-4-conformance-verification
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/135

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **library maintainer**,
I want **a test suite that verifies the wrapped EncryptedSessionService is behaviorally equivalent to the previous implementation and to an unencrypted DatabaseSessionService**,
So that **I have confidence the architecture migration introduced no regressions**.

## Acceptance Criteria

1. **Conformance Testing — Core Operations**
   - Given the rewritten `EncryptedSessionService` wraps `DatabaseSessionService`
   - When conformance tests are run
   - Then for identical inputs, the wrapped service produces the same `Session` and `Event` objects (same fields, types, values) as a raw `DatabaseSessionService` — except that persisted data is encrypted at rest
   - And conformance tests cover: create, get, list, delete, and append_event operations

2. **Round-Trip Encryption Testing**
   - Given the `TypeDecorator` encrypts on write and decrypts on read
   - When round-trip encryption tests are run
   - Then data verified at each boundary: plaintext -> TypeDecorator encrypts -> DB stores ciphertext -> TypeDecorator decrypts -> plaintext matches original
   - And wrong-key decryption raises `DecryptionError`, never returns garbage data (NFR7)
   - And empty state (`{}`) and empty event lists (`[]`) round-trip without error (NFR15)

3. **ADK Runner Integration Verification**
   - Given Story 1.6a verified ADK Runner accepts `EncryptedSessionService`
   - When the runner integration test is re-run against the rewritten service
   - Then the test passes — an ADK Runner can execute a complete agent turn using the wrapped service (NFR20)

4. **Unencrypted Data Detection**
   - Given a database containing unencrypted `DatabaseSessionService` data (no encryption)
   - When the wrapped `EncryptedSessionService` attempts to read that data
   - Then it detects the unencrypted data and raises a clear error (not silent corruption or garbage data)
   - And the error message indicates the data was not encrypted, not that decryption failed with wrong key

5. **Concurrency & Connection Management**
   - And concurrent async session operations on the same database do not corrupt data (NFR25)
   - And all async fixtures properly close database connections on teardown (NFR19)

6. **Quality Standards**
   - And code coverage remains >= 90% (NFR18)
   - And the test suite passes with zero warnings (NFR16)

## Tasks / Subtasks

- [x] Task 1: Conformance test suite — wrapped vs unwrapped DatabaseSessionService (AC: 1)
  - [x] 1.1 Create `tests/integration/test_conformance.py` with `pytestmark = pytest.mark.integration`
  - [x] 1.2 Fixture: `unencrypted_service` — raw `DatabaseSessionService` with separate DB file
  - [x] 1.3 Test `test_create_session_conformance`
  - [x] 1.4 Test `test_get_session_conformance`
  - [x] 1.5 Test `test_list_sessions_conformance`
  - [x] 1.6 Test `test_delete_session_conformance`
  - [x] 1.7 Test `test_append_event_conformance`
  - [x] 1.8 Test `test_state_merge_conformance`

- [x] Task 2: Encryption boundary verification — ciphertext-at-rest (AC: 2)
  - [x] 2.1 Create `tests/integration/test_encryption_boundary.py` with `pytestmark = pytest.mark.integration`
  - [x] 2.2 Test `test_state_stored_as_ciphertext` — uses `sqlite3.connect()` for raw DB reads
  - [x] 2.3 Test `test_event_data_stored_as_ciphertext`
  - [x] 2.4 Test `test_app_state_stored_as_ciphertext` — with `pytest.skip()` guard if table empty
  - [x] 2.5 Test `test_user_state_stored_as_ciphertext` — with `pytest.skip()` guard if table empty
  - [x] 2.6 Test `test_metadata_stored_plaintext`
  - [x] 2.7 Test `test_empty_state_round_trip_with_boundary_check`
  - [x] 2.8 Test `test_complex_nested_state_round_trip`

- [x] Task 3: Unencrypted data detection (AC: 4)
  - [x] 3.0 **Investigation**: Traced error path — plaintext JSON fails at `base64.b64decode()` with `binascii.Error` (inherits `ValueError`). Added broader `except (ValueError, Exception)` catch in `process_result_value` to produce clear `DecryptionError("data does not appear to be encrypted")`. Some JSON strings partially decode as valid base64, hitting `_parse_envelope` which raises `DecryptionError("Unsupported envelope version: N")` — both paths now produce `DecryptionError`.
  - [x] 3.1 Fixture: `shared_db_encrypted_service` — shared DB for both services
  - [x] 3.2 Test `test_unencrypted_data_raises_clear_error`
  - [x] 3.3 Assert `DecryptionError` raised (not silent corruption)
  - [x] 3.4 Error message does not expose key material or plaintext
  - [x] 3.5 Test `test_unencrypted_event_data_detected`

- [x] Task 4: ADK Runner integration re-verification (AC: 3)
  - [x] 4.1 Verified `test_adk_runner.py` passes — all 6 tests pass
  - [x] 4.2 No runner failures — all passing from Story 7.3
  - [x] 4.3 Already covered by `test_full_lifecycle_through_runner` (raw DB encryption check at lines 182-203) and `test_state_delta_is_encrypted_in_database` (lines 255-284)

- [x] Task 5: Concurrency & fixture cleanup audit (AC: 5)
  - [x] 5.1 Audited all fixtures — all use async generator pattern with proper cleanup: `tests/conftest.py::encrypted_service`, `tests/benchmarks/conftest.py::baseline_conn`, `test_conformance.py` (3 fixtures), `test_adk_runner.py` (3 runner fixtures)
  - [x] 5.2 Verified `test_concurrent_writes.py` passes — all 4 tests pass
  - [x] 5.3 Added `test_concurrent_event_appends_all_encrypted` to `test_concurrent_writes.py`

- [x] Task 6: Quality gate verification (AC: 6)
  - [x] 6.1 Coverage: 98.88% (>= 90% threshold) — 171 passed, 1 deselected
  - [x] 6.2 Zero warnings: `pytest -W error` — 171 passed
  - [x] 6.3 Pre-commit: all hooks pass (verified earlier in session)
  - [x] 6.4 Ruff check: zero lint violations
  - [x] 6.5 Ruff format: zero format issues (32 files already formatted)

### Cross-Cutting Test Maturity (Standing Task)

- [x] Identified gap: No integration test for **tampered ciphertext at rest** — if raw DB data is modified, service must raise `DecryptionError` (not silent corruption). Unit tests cover tampered data but no integration test verified it through the full SQLAlchemy ORM path.
- [x] Added `TestTamperedCiphertextAtRest::test_tampered_state_raises_decryption_error` to `test_encryption_boundary.py`
- [x] Test passes in full suite (171 passed)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_conformance.py::TestCreateSessionConformance`, `TestGetSessionConformance`, `TestListSessionsConformance`, `TestDeleteSessionConformance`, `TestAppendEventConformance`, `TestStateMergeConformance` | ✅ pass |
| 2    | `test_encryption_boundary.py::TestStateCiphertextAtRest`, `TestEventCiphertextAtRest`, `TestAppStateCiphertextAtRest`, `TestUserStateCiphertextAtRest`, `TestMetadataStoredPlaintext`, `TestEmptyStateRoundTrip`, `TestComplexNestedStateRoundTrip` | ✅ pass |
| 3    | `test_adk_runner.py` (existing 6 tests re-verified — includes `test_full_lifecycle_through_runner` with raw DB encryption check) | ✅ pass |
| 4    | `test_conformance.py::TestUnencryptedDataDetection` (2 tests) + source fix in `type_decorator.py` | ✅ pass |
| 5    | `test_concurrent_writes.py` (4 existing + 1 new `test_concurrent_event_appends_all_encrypted`), fixture audit (all pass) | ✅ pass |
| 6    | Coverage 98.88%, zero warnings, ruff clean, format clean, pre-commit pass | ✅ pass |

## Dev Notes

### Architecture Context

Story 7.3 rewrote `EncryptedSessionService` from ~800-line raw aiosqlite to ~130-line `DatabaseSessionService` wrapper. Encryption now happens at the SQLAlchemy TypeDecorator boundary (`EncryptedJSON`), not in CRUD method overrides.

**Key implementation details from Story 7.3 that affect testing:**
- `EncryptedSessionService` subclasses `DatabaseSessionService` with zero CRUD overrides
- All encryption/decryption happens in `EncryptedJSON.process_bind_param()` and `process_result_value()` (synchronous — greenlet context)
- `DontWrapMixin` on exception classes ensures `DecryptionError` propagates directly through SQLAlchemy (not wrapped in `StatementError`)
- Constructor API changed: `db_url="sqlite+aiosqlite:///path"` replaces `db_path="path"`
- `aiosqlite` removed from direct deps — still available transitively via google-adk

**What already exists from Story 7.3 (do NOT duplicate):**
- `test_encrypted_session_service.py` — CRUD round-trips, wrong-key tests, empty state, sentinel tests, zero-CRUD-override verification
- `test_type_decorator.py` — TypeDecorator unit tests
- `test_adk_integration.py` — BaseSessionService interface conformance
- `test_adk_runner.py` — Runner drop-in verification (NFR20)
- `test_concurrent_writes.py` — Concurrent write safety (NFR25)

**What this story adds (the gap):**
1. **Conformance comparison** — side-by-side tests comparing wrapped vs unwrapped `DatabaseSessionService` output for identical inputs
2. **Boundary verification** — raw DB reads proving ciphertext at rest (the "gold standard" from architecture doc, section on encryption boundary verification)
3. **Unencrypted data detection** — creating plaintext data with raw `DatabaseSessionService`, reading with encrypted service, verifying clear error
4. **Quality consolidation** — full suite verification with coverage + zero warnings

### Party Mode Consensus (Architect + Dev + Test Architect)

**Agreed decisions:**
1. **Conformance comparison strategy**: Behavioral equivalence + field-level assertions. Compare behavior (create returns Session, get retrieves what was created, state merges work) AND assert specific fields (`app_name`, `user_id`, `state` values). Exclude auto-generated fields (`session_id`, timestamps).
2. **Fixture architecture**: Separate databases for conformance tests (each service gets its own DB), shared database for unencrypted detection tests (raw service writes, encrypted service reads same file).
3. **Boundary verification**: Use synchronous `create_engine("sqlite:///...")` to read raw rows after async operations commit. Ensure async engine has flushed before sync engine reads.
4. **`append_event` conformance**: Must verify `event.content` dict equality explicitly, not just field presence.

**Investigation items for dev agent:**
1. **AC-4 error path (HIGH PRIORITY)**: Trace what happens when `process_result_value` receives plaintext JSON (not an envelope). The data won't have `[version_byte][backend_id_byte]` header. Does base64 decode + `_parse_envelope` produce a clear `DecryptionError`? Or a confusing `ValueError`? If unclear, a small source change to `process_result_value` is authorized to improve the error message (document as scoped change).
2. **`app_states`/`user_states` table population**: Verify which ADK operations populate these tables. A simple `create_session` may not write to them. If they're empty, boundary tests are meaningless — use `pytest.skip()` or find the right operation.
3. **Benchmark test stale import**: `tests/benchmarks/test_encryption_overhead.py` line 26 imports `aiosqlite` directly. Not in scope for this story but track for future cleanup.

**Relaxed constraint**: The "Do NOT modify source code" constraint is relaxed specifically for AC-4 if the unencrypted data error path produces unclear errors. Any source change must be minimal (error handling only) and documented as a subtask.

### Critical Patterns for Dev Agent

**Conformance test pattern:**
```python
# Use TWO separate databases — never share a DB file between services
encrypted_svc = EncryptedSessionService(db_url="sqlite+aiosqlite:///enc.db", backend=backend)
unencrypted_svc = DatabaseSessionService(db_url="sqlite+aiosqlite:///plain.db")

# Identical inputs
enc_session = await encrypted_svc.create_session(app_name="app", user_id="u1", state={"k": "v"})
plain_session = await unencrypted_svc.create_session(app_name="app", user_id="u1", state={"k": "v"})

# Compare — session_id will differ (UUIDs), but structure must match
assert enc_session.app_name == plain_session.app_name
assert enc_session.user_id == plain_session.user_id
assert enc_session.state == plain_session.state  # decrypted state matches
```

**Boundary verification pattern (gold standard):**
```python
# Create via service (normal API)
session = await encrypted_svc.create_session(app_name="app", user_id="u1", state={"secret": "data"})

# Read raw DB row directly (bypass service)
from sqlalchemy import create_engine, text
engine = create_engine("sqlite:///enc.db")
with engine.connect() as conn:
    row = conn.execute(text("SELECT state FROM sessions WHERE ...")).fetchone()
    raw_value = row[0]

# Assert: raw value is NOT plaintext JSON
import json
with pytest.raises((json.JSONDecodeError, UnicodeDecodeError, Exception)):
    json.loads(raw_value)  # Must fail — it's ciphertext (base64-encoded envelope)
```

**Unencrypted data detection pattern:**
```python
# Create unencrypted data with raw DatabaseSessionService
plain_svc = DatabaseSessionService(db_url="sqlite+aiosqlite:///shared.db")
plain_session = await plain_svc.create_session(app_name="app", user_id="u1", state={"key": "val"})

# Try to read with encrypted service — SAME database
enc_svc = EncryptedSessionService(db_url="sqlite+aiosqlite:///shared.db", backend=backend)
with pytest.raises(DecryptionError):
    await enc_svc.get_session(app_name="app", user_id="u1", session_id=plain_session.id)
```

**Fixture cleanup pattern:**
```python
@pytest.fixture
async def service(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    svc = EncryptedSessionService(db_url=db_url, backend=backend)
    yield svc
    await svc.close()
```

### Important Constraints

- **Source code changes scoped to AC-4 only** — this story is primarily test-only. However, if the unencrypted data error path in `process_result_value` produces unclear errors (see Task 3.0 investigation), a minimal source change is authorized to improve the error message. Document any source change as a subtask with rationale.
- **Do NOT duplicate existing tests** — Story 7.3 already covers CRUD round-trips, wrong-key decryption, empty state, sentinels. This story adds NEW test dimensions (conformance comparison, boundary verification, unencrypted detection).
- **Use `pytest.mark.integration`** — new test files are integration tests (real DB, real encryption).
- **All tests async** — `async def test_...`, no `@pytest.mark.asyncio` (auto mode).
- **`tmp_path` for databases** — every test gets its own temp directory. Never use fixed paths.

### Peripheral Config Impact

No peripheral config impact — this story adds test files only. No changes to `pyproject.toml`, `mkdocs.yml`, CI workflows, or any config files.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| None | No user-facing changes — test-only story |

### Project Structure Notes

New files follow existing test organization:
- `tests/integration/test_conformance.py` — new conformance comparison tests
- `tests/integration/test_encryption_boundary.py` — new boundary verification tests
- Unencrypted data detection tests can live in `test_conformance.py` (same theme) or `test_encryption_boundary.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 7, Story 7.4]
- [Source: _bmad-output/planning-artifacts/architecture.md — Encryption Boundary Verification Pattern]
- [Source: _bmad-output/implementation-artifacts/7-3-rewrite-encryptedsessionservice-as-databasesessionservice-wrapper.md — Dev Notes, Files Modified, Code Patterns]
- [Source: docs/adr/ADR-007-architecture-migration.md — Wrapper architecture decision]
- [Source: .claude/rules/dev-quality-checklist.md — AC-to-Test Traceability, Encryption Path Verification]
- [Source: .claude/rules/conventions.md — Encryption Is a Contract]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 171 passed, 98.88% coverage
- [x] `pre-commit run --all-files` -- all hooks pass

## Code Review

- **Reviewer:** Alberto-Codes (BMAD adversarial review + party mode consensus)
- **Outcome:** Changes Requested → Fixed → Approved

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | HIGH | AC-4 error message not verified — tests only assert `DecryptionError` raised, not message content | Fixed: added `assert "wrong key" not in str(exc_info.value)` to both unencrypted detection tests |
| 2 | MEDIUM | Redundant `except (ValueError, Exception)` in type_decorator.py (SonarQube S5713) | Fixed: refactored to ordered `except DecryptionError: raise` then `except Exception:` |
| 3 | LOW | `pytest.raises` + `json.loads` anti-pattern in boundary test | Fixed: simplified to `assert "classified" not in raw_value` matching other boundary tests |
| 4 | MEDIUM | `TestAppendEventConformance` missing `actions` equality check (party mode consensus gap) | Fixed: added `assert enc_event.actions == plain_event.actions` |
| 5 | MEDIUM | `TestEmptyStateRoundTrip` weak assertion (`isinstance` not `== {}`) | Fixed: changed to `assert retrieved.state == {}` + `assert len(retrieved.events) == 0` |
| 6 | LOW | `sqlite3.connect()` without context manager | Skipped: `with sqlite3.connect()` manages transactions not connections; explicit `.close()` is correct |
| 7 | LOW | Test names say "fifty" but NUM_COROUTINES=10 | Skipped: pre-existing from Story 1.6b, out of scope |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes (171 passed, 98.88% coverage)
- [x] Quality gates re-verified (ruff clean, zero warnings, SonarQube zero issues on modified source)

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-05 | Story created by SM agent — comprehensive context for test migration |
| 2026-03-05 | Party mode review (Architect + Dev + Test Architect) — added conformance strategy consensus, fixture architecture decisions, AC-4 error path investigation task, `app_states`/`user_states` population caveat, relaxed source constraint for AC-4 |
| 2026-03-05 | Implementation complete — all 6 tasks done, 171 tests pass, 98.88% coverage |
| 2026-03-05 | Code review: 5 findings fixed (1 HIGH, 2 MEDIUM, 2 LOW), 2 skipped (out of scope). SonarQube S5713 resolved. All quality gates pass. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — no unexpected failures during implementation.

### Completion Notes List

- AC-4 required a scoped source change to `type_decorator.py:process_result_value` — added broader exception handling for non-envelope data (plaintext JSON). The error path varies: some JSON fails at `base64.b64decode()` (`binascii.Error`), some partially decodes and fails at `_parse_envelope` (`DecryptionError("Unsupported envelope version")`). Both paths now produce `DecryptionError`.
- Task 4.3 was already covered by existing `test_full_lifecycle_through_runner` and `test_state_delta_is_encrypted_in_database` — no new test needed.
- Cross-cutting: Added `TestTamperedCiphertextAtRest` — integration test for tampered raw DB data detection through full SQLAlchemy ORM path.

### File List

| File | Action | Description |
|------|--------|-------------|
| `tests/integration/test_conformance.py` | Created | 8 tests: 6 conformance (AC-1) + 2 unencrypted detection (AC-4) |
| `tests/integration/test_encryption_boundary.py` | Created | 8 tests: 7 boundary verification (AC-2) + 1 cross-cutting tampered data |
| `tests/integration/test_concurrent_writes.py` | Modified | Added `test_concurrent_event_appends_all_encrypted` (AC-5) |
| `src/adk_secure_sessions/services/type_decorator.py` | Modified | Broadened `process_result_value` exception handling for AC-4 |
| `_bmad-output/implementation-artifacts/7-4-test-migration-conformance-verification.md` | Modified | Task checkboxes, AC-to-Test mapping, dev record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified | Story status: backlog → done |
