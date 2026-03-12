# Story 4.4: Zero-Downtime Key Rotation

Status: review
Branch: feat/rotation-4-4-zero-downtime-key-rotation
GitHub Issue:

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **operator managing encryption keys in production**,
I want **to rotate encryption keys with zero downtime using a decrypt-with-old, encrypt-with-new strategy**,
So that **I can meet key rotation compliance requirements without disrupting active sessions**.

## Acceptance Criteria

1. **Given** the system supports multiple backends via the backend registry
   **When** key rotation is initiated
   **Then** the operator configures both old and new keys, specifying which is the active encryption key (FR48)
   **And** new sessions and updates are encrypted with the new key
   **And** existing sessions encrypted with the old key are decrypted successfully (using envelope header to identify the backend)

2. **Given** a production database containing sessions encrypted with the old key
   **When** `rotate_encryption_keys()` is called with `old_backend` and `new_backend`
   **Then** a migration utility re-encrypts all records across all 4 tables (`sessions`, `app_states`, `user_states`, `events`)
   **And** after rotation completes, all data is readable using only `new_backend`
   **And** the function returns the count of re-encrypted records

3. **Given** the rotation strategy choice between batch and lazy
   **When** the story is implemented
   **Then** the rotation strategy is clearly documented: whether rotation is batch (re-encrypt all at once), lazy (re-encrypt on next access via `additional_backends`), or both — with trade-offs explained
   **And** the lazy (zero-code-change) path via `additional_backends` is documented for cross-backend migrations

4. **Given** concurrent session updates may occur during batch rotation
   **When** `rotate_encryption_keys()` processes a session
   **Then** stale overwrites are prevented: if a session's `update_time` changed between read and write (concurrent update), the rotation skips that record and reports it as skipped rather than overwriting newer data (NFR27)

5. **Given** key rotation is a sensitive security operation
   **When** any error occurs during rotation
   **Then** key rotation never exposes old or new keys in logs or error messages (NFR6)
   **And** all existing error message safety assertions in `test_adk_encryption.py` continue to pass

6. **Given** a full rotation lifecycle scenario
   **When** an integration test exercises the complete flow
   **Then** the test verifies: create sessions with old key → call `rotate_encryption_keys()` → new reads succeed with new key → old key backend alone raises `DecryptionError` → confirm all tables (sessions, app_states, user_states, events) rotated

7. **Given** the public API contract
   **When** `rotate_encryption_keys` is exported
   **Then** it appears in `__all__` in `__init__.py` and is documented with a Google-style docstring including `Examples:` using fenced code blocks

## Tasks / Subtasks

- [x] Task 1: Evaluate and document the EncryptionCoordinator question (AC: #3)
  - [x] 1.1 Read the note at Story 3.3 party-mode consensus in `epics.md` line 834 regarding coordinator extraction
  - [x] 1.2 Determine if a coordinator class is needed (decision: `rotate_encryption_keys()` standalone function is sufficient; document rationale in Dev Notes)
  - [x] 1.3 Write `docs/adr/ADR-009-key-rotation-strategy.md` documenting the chosen strategy (batch + lazy paths, no coordinator, optimistic concurrency via `update_time`)

- [x] Task 2: Implement `rotate_encryption_keys()` in new module (AC: #1, #2, #4)
  - [x] 2.1 Create `src/adk_secure_sessions/rotation.py` with `rotate_encryption_keys()` async function
  - [x] 2.2 Function signature: `async def rotate_encryption_keys(db_url: str, old_backend: EncryptionBackend, new_backend: EncryptionBackend) -> RotationResult` where `RotationResult` is a dataclass with `rotated: int`, `skipped: int`
  - [x] 2.3 Implement raw SQLAlchemy `select` + `update` over all 4 tables for records matching `old_backend.backend_id` in their envelope header
  - [x] 2.4 Implement optimistic concurrency check: read `update_time`, re-encrypt, `UPDATE WHERE update_time = <read_value>` — increment skipped count if rows_affected == 0
  - [x] 2.5 Wrap all cryptography calls in `asyncio.to_thread()` (CPU-bound rule from conventions.md)
  - [x] 2.6 Ensure no key material appears in any exception message (NFR6)
  - [x] 2.7 Google-style docstring on module and function with `Examples:` fenced block

- [x] Task 3: Export `rotate_encryption_keys` from public API (AC: #7)
  - [x] 3.1 Add import to `src/adk_secure_sessions/__init__.py`
  - [x] 3.2 Add `"rotate_encryption_keys"` to `__all__` in alphabetical order
  - [x] 3.3 Add `"RotationResult"` to `__all__` if it is a public-facing dataclass

- [x] Task 4: Document lazy rotation path (AC: #3)
  - [x] 4.1 Create directory `docs/how-to/` (does not exist yet — must be created)
  - [x] 4.2 Create `docs/how-to/key-rotation.md` explaining both rotation paths with code examples
  - [x] 4.3 Document Path A (lazy cross-backend): configure `EncryptedSessionService(backend=new, additional_backends=[old])` — old sessions remain readable while new writes use new backend
  - [x] 4.4 Document Path B (batch same-backend): call `rotate_encryption_keys()` for same-backend passphrase rotation
  - [x] 4.5 Document trade-offs: Path A never migrates old data (storage grows mixed), Path B is a one-time migration but requires downtime window or retry logic
  - [x] 4.6 Update `mkdocs.yml` nav section — added `"How-To Guides:"` block, ADR-009 entry, and fixed missing ADR-008 entry

- [x] Task 5: Unit tests for `rotation.py` (AC: #2, #4, #5)
  - [x] 5.1 Create `tests/unit/test_rotation.py` with `pytestmark = pytest.mark.unit`
  - [x] 5.2 Test `rotate_encryption_keys` with mocked DB: returns `RotationResult(rotated=N, skipped=0)` for N records
  - [x] 5.3 Test optimistic concurrency skip: if `update_time` check fails (rows_affected=0), skipped count increments
  - [x] 5.4 Test that no key material appears in raised exceptions
  - [x] 5.5 Test that only records matching `old_backend.backend_id` in their envelope header are processed (skips records already on new backend)
  - [x] 5.6 Test empty database returns `RotationResult(rotated=0, skipped=0)` without error

- [x] Task 6: Integration test for full rotation lifecycle (AC: #6)
  - [x] 6.1 Create `tests/integration/test_key_rotation.py` with `pytestmark = pytest.mark.integration`
  - [x] 6.2 Fixture: create sessions + app_states + user_states + events using `old_backend` (real FernetBackend or AesGcmBackend)
  - [x] 6.3 Call `rotate_encryption_keys(db_url, old_backend, new_backend)` — assert rotated > 0, skipped == 0
  - [x] 6.4 Verify: reading sessions with `EncryptedSessionService(backend=new_backend)` succeeds for all sessions
  - [x] 6.5 Verify: `EncryptedSessionService(backend=old_backend_only)` raises `DecryptionError` on read (data now uses new key)
  - [x] 6.6 Verify all 4 tables are rotated (app_states, user_states, sessions, events)
  - [x] 6.7 Use async generator fixture with `yield; await svc.close()` teardown pattern

### Cross-Cutting Test Maturity (Standing Task)

<!-- Sourced from test-review.md recommendations. The create-story workflow
     picks the next unaddressed item and assigns it here. -->

**Test Review Item**: Monitor marginally-over-threshold files
**Severity**: P3 (Low)
**Location**: `tests/unit/test_serialization.py` (429), `tests/integration/test_adk_crud.py` (406), `tests/integration/test_conformance.py` (367), `tests/integration/test_adk_encryption.py` (356), `tests/integration/test_adk_runner.py` (356), `tests/unit/test_encrypted_session_service.py` (312), `tests/integration/test_encryption_boundary.py` (309), `tests/unit/test_fernet_backend.py` (301)

Eight files are over the 300-line threshold (301-429 lines). `test_serialization.py` at 429 lines is the largest (1.43x threshold) due to the new `TestAesGcmSerialization` class. `test_fernet_backend.py` newly crossed 300 at 301 lines after sync method tests were added. Each file is well-organized with clear test class boundaries. If any file exceeds 500 lines, split at the class boundary. This is informational, not actionable.

- [x] After adding new tests for this story, check if any of the monitored files have crossed or are approaching 500 lines
- [x] If `test_serialization.py` exceeds 500 lines after adding rotation tests, split at the `TestAesGcmSerialization` class boundary into a separate `test_serialization_aes_gcm.py` file — `test_serialization.py` is at 492 lines, no split performed (under 500 threshold)
- [x] Verify new/changed test(s) pass in CI — all 266 tests pass
- [ ] Mark item as done in `_bmad-output/test-artifacts/test-review.md` only if a split was performed; otherwise leave as Monitor — no split, left as Monitor

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `TestBackendIdFiltering::test_mixed_backends_only_processes_old_backend_records` (T008) — verifies envelope backend_id dispatch; `TestFullRotationLifecycle::test_new_backend_reads_succeed_after_rotation` (T011) | pass |
| 2    | `TestFullRotationLifecycle::test_rotate_returns_positive_rotated_count` (T010), `test_all_four_tables_covered_by_rotation` (T013), `test_new_backend_reads_succeed_after_rotation` (T011) | pass |
| 3    | `docs/how-to/key-rotation.md` + `docs/adr/ADR-009-key-rotation-strategy.md` + docvet | pass |
| 4    | `TestOptimisticConcurrency::test_zero_rowcount_increments_skipped` (T005), `test_partial_concurrent_writes_tracked` (T006) | pass |
| 5    | `TestErrorMessageSafety::test_unexpected_exception_wrapped_without_key_material` (T009) | pass |
| 6    | `TestFullRotationLifecycle` (T010–T015): full lifecycle, all 4 tables, new-key reads succeed, old-key raises `DecryptionError`, state preservation | pass |
| 7    | `tests/unit/test_public_api.py` (existing, exercises `rotate_encryption_keys` + `RotationResult` in `__all__`) + docvet | pass |

## Dev Notes

### EncryptionCoordinator Evaluation (from Story 3.3 Note)

The epics.md note (line 834) asks Story 4.4 to evaluate whether extracting an `EncryptionCoordinator` is needed for key rotation. **Decision: No coordinator class needed.**

Rationale:
- Multi-backend dispatch is already fully implemented via `EncryptedJSON.decrypt_dispatch` (mapping `backend_id → sync_decrypt`)
- The `additional_backends` mechanism in `EncryptedSessionService.__init__` handles the dispatch population
- Key rotation adds "re-encrypt all records" which is a migration task, not a dispatch task
- A standalone `rotate_encryption_keys()` async function in a dedicated `rotation.py` module is the right level of abstraction — minimal surface, single responsibility
- An `EncryptionCoordinator` class would be over-engineering: it would add a class with no protocol boundary that external code can depend on, and no clear benefit over the existing dispatch pattern

This decision should be documented in `docs/adr/ADR-009-key-rotation-strategy.md`.

### Key Rotation Paths

There are two distinct rotation scenarios with different implementation requirements:

**Path A: Lazy Cross-Backend Rotation (Zero Code Changes)**

Already works today via `additional_backends`. Example: rotating from Fernet to AES-GCM:

```python
old_fernet = FernetBackend("old-passphrase")
new_aes_gcm = AesGcmBackend(key=AESGCM.generate_key(bit_length=256))
service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=new_aes_gcm,         # new writes use AES-GCM
    additional_backends=[old_fernet],  # old sessions remain readable
)
```

This works because the two backends have different `backend_id` values (`0x01` vs `0x02`), enabling unambiguous dispatch. No migration utility needed — old data is read transparently, new data is written with the new backend. Trade-off: old encrypted records accumulate indefinitely; no forced migration.

**Path B: Batch Same-Backend Rotation (New `rotate_encryption_keys()` function)**

For same-backend key rotation (e.g., two `FernetBackend` instances with different passphrases), the `additional_backends` mechanism is blocked by the duplicate `backend_id` check in `EncryptedSessionService.__init__`. The rotation function bypasses this by operating directly on the SQLAlchemy engine.

Why `additional_backends` cannot handle same-backend rotation:
```python
# This RAISES ConfigurationError — both backends have backend_id == 0x01
service = EncryptedSessionService(
    backend=FernetBackend("new-passphrase"),
    additional_backends=[FernetBackend("old-passphrase")],  # CONFLICT: both are 0x01
)
```

The `rotate_encryption_keys()` function:
1. Opens the DB engine from `db_url`
2. Reads all encrypted columns across all 4 tables using raw `select` queries
3. For each row: parse envelope → check backend_id matches `old_backend.backend_id` → decrypt with `old_backend.sync_decrypt` → re-encrypt with `new_backend.sync_encrypt` → update row with optimistic concurrency check
4. Crypto calls go through `asyncio.to_thread()` (CPU-bound rule)

### Optimistic Concurrency (NFR27) — `update_time` approach

The `sessions` table has `update_time` (auto-updated by ADK on every write). The rotation function can use this as a natural optimistic concurrency guard:

```python
# Pseudocode:
result = await session.execute(select(EncryptedStorageSession.update_time).where(...))
read_update_time = result.scalar()
# ... re-encrypt state ...
rows_affected = await session.execute(
    update(EncryptedStorageSession)
    .where(id == session_id, update_time == read_update_time)
    .values(state=new_encrypted_state)
)
if rows_affected == 0:
    skipped += 1  # concurrent write happened, skip this record
```

**Why not a `version` column**: The `version` column was reserved in Story 1.2 but never added to `models.py` after the Epic 7 architecture migration to `DatabaseSessionService` wrapper. Adding a `version` column to our encrypted models would require overriding ADK's CRUD write methods (`create_session`, `append_event`) to increment it — going against the ADK-is-upstream principle (conventions.md). The `update_time` column is a functionally equivalent concurrency guard that requires no ADK method overrides.

This design decision (use `update_time` instead of `version`) should be noted in `ADR-009-key-rotation-strategy.md` and the story's change log.

### Critical Architecture Constraints

- **`EncryptedJSON` TypeDecorator sync/async boundary**: `process_bind_param`/`process_result_value` run synchronously within SQLAlchemy's execution context. The `rotate_encryption_keys()` function operates **outside** the TypeDecorator — it reads raw base64 TEXT from the DB, does its own base64 decode + `_parse_envelope` + decrypt/re-encrypt + `_build_envelope` + base64 encode. This is intentional: the rotation function needs to control which key is used for decryption, bypassing the TypeDecorator's configured dispatch.

- **All 4 tables have encrypted columns** (per `models.py`):
  - `sessions.state` (EncryptedJSON)
  - `app_states.state` (EncryptedJSON)
  - `user_states.state` (EncryptedJSON)
  - `events.event_data` (EncryptedJSON, nullable)

- **`events.event_data` is nullable** — skip NULL values without error

- **`asyncio.to_thread()` for crypto**: `old_backend.sync_decrypt` and `new_backend.sync_encrypt` are synchronous but CPU-bound. Wrap batch crypto calls in `asyncio.to_thread()` per conventions.md. For the rotation function operating at scale, consider wrapping per-record or in small batches.

- **Parametrized SQL only**: Even though the rotation function uses SQLAlchemy, use parametrized queries. Never f-string interpolation into SQL.

- **From `__future__ import annotations`**: Required as first import per conventions.md.

- **Absolute imports only**: `from adk_secure_sessions.serialization import _build_envelope, _parse_envelope` (these are "internal helpers" that the rotation module legitimately needs — they are already imported by `type_decorator.py`).

### Key Safety (NFR6)

Error messages from `rotate_encryption_keys()` must never contain:
- Key material, passphrases, or derived key bytes
- Plaintext session state
- Ciphertext (as raw bytes/hex that could be used for analysis)

All exceptions in the rotation path should use the same pattern as the rest of the codebase:
```python
msg = "Rotation failed: decryption error on record {record_id}"  # OK: record ID is metadata
raise DecryptionError(msg) from exc
```

### Sync/Async Boundary Warning (High-Risk Zone)

The rotation module is entirely async (`async def rotate_encryption_keys(...)`) but calls sync crypto functions. Per conventions.md "The Sync/Async Boundary Is a High-Risk Zone":
- All `sync_encrypt`/`sync_decrypt` calls in the rotation function MUST go through `asyncio.to_thread()`
- The rotation module does NOT use TypeDecorators (no SQLAlchemy ORM column encryption) — it operates on raw TEXT column values
- This surface area typically generates more code review findings — budget for review attention

### Blast Radius: Peripheral Config Files

- `mkdocs.yml`: Add `"How-To Guides:"` nav section with `key-rotation.md`; add ADR-009 to `Decisions:` block; add missing ADR-008 entry while in the area
- `src/adk_secure_sessions/__init__.py`: Add `rotate_encryption_keys` + `RotationResult` to imports and `__all__`
- No changes to `pyproject.toml`, `.github/workflows/*.yml`, `sonar-project.properties`, or `pre-commit-config.yaml`

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/adr/ADR-009-key-rotation-strategy.md` | New ADR documenting rotation strategy decision (batch + lazy paths, no coordinator, update_time optimistic concurrency) |
| `docs/how-to/key-rotation.md` | New how-to page: both rotation paths with code examples and trade-offs (requires creating `docs/how-to/` directory) |
| `mkdocs.yml` | Add `"How-To Guides:"` nav section; add ADR-009 to `Decisions:` block; fix missing ADR-008 entry |
| `src/adk_secure_sessions/__init__.py` | Export `rotate_encryption_keys` and `RotationResult` |

### Project Structure Notes

New files to create:
- `src/adk_secure_sessions/rotation.py` — `rotate_encryption_keys()` and `RotationResult` dataclass
- `tests/unit/test_rotation.py` — unit tests (mocked DB)
- `tests/integration/test_key_rotation.py` — integration test (real SQLite + real backends)
- `docs/adr/ADR-009-key-rotation-strategy.md` — architecture decision record
- `docs/how-to/key-rotation.md` — operator how-to guide

Modified files:
- `src/adk_secure_sessions/__init__.py` — add `rotate_encryption_keys`, `RotationResult` to imports + `__all__`
- `mkdocs.yml` — add `"How-To Guides:"` section; add ADR-009 + missing ADR-008 to Decisions nav block

**Do NOT modify**:
- `src/adk_secure_sessions/services/models.py` — no `version` column needed (use `update_time` instead)
- `src/adk_secure_sessions/services/encrypted_session.py` — no overrides needed
- `src/adk_secure_sessions/services/type_decorator.py` — rotation bypasses TypeDecorator
- Any existing test files (unless forced by cross-cutting task)

### Previous Story Intelligence

Story 7.6 (most recent completed) was a pure docs/planning story — no code patterns to inherit directly. The most recent code story was Story 3.4 (published performance benchmarks). Key patterns from git history:

- `feat(bench): add multi-backend benchmarks and docs page (#145)` — added `tests/benchmarks/test_encryption_overhead.py`, established benchmark patterns
- `feat(serialization): add multi-backend coexistence and dispatch (#144)` — Story 3.3 added `additional_backends` multi-backend dispatch to `EncryptedSessionService`; the `decrypt_dispatch` dict building pattern in `encrypted_session.py:193` is directly relevant
- `feat(backend): add per-key random salt key derivation to FernetBackend (#143)` — Story 3.2 established the `_make_runner` factory fixture pattern in `test_adk_runner.py`
- `feat(backend): add AES-256-GCM encryption backend (#141)` — Story 3.1 established magic-string constants pattern in integration tests

From Story 3.3 code review — ADR-related learnings that apply to this story:
- The `sync_encrypt`/`sync_decrypt` surface in TypeDecorators generated extra code review findings (conventions.md Sync/Async Boundary section) — this story creates a NEW sync/async boundary surface; expect findings
- Backend validation at init time (isinstance check + duplicate backend_id check) is a proven pattern — reuse in rotation function parameter validation

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 4.4`] — acceptance criteria and coordinator evaluation note
- [Source: `src/adk_secure_sessions/services/encrypted_session.py:129-204`] — `additional_backends` multi-dispatch implementation (Path A foundation)
- [Source: `src/adk_secure_sessions/services/type_decorator.py:85-174`] — `EncryptedJSON` TypeDecorator (rotation bypasses this)
- [Source: `src/adk_secure_sessions/serialization.py:64-107`] — `_build_envelope`, `_parse_envelope` helpers (used directly in rotation)
- [Source: `src/adk_secure_sessions/services/models.py:125-162`] — `EncryptedStorageSession` model (tables with encrypted columns)
- [Source: `docs/adr/ADR-007-architecture-migration.md`] — wrapper architecture, why `update_time` is available as a concurrency guard
- [Source: `.claude/rules/conventions.md#The Sync/Async Boundary Is a High-Risk Zone`] — rotation module is a high-risk zone for review findings
- [Source: `_bmad-output/project-context.md#Encryption Architecture`] — data flow contract (all paths through encrypt/decrypt)
- [Source: `_bmad-output/test-artifacts/test-review.md#Recommendation 6`] — cross-cutting test monitoring task

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors in new files (56 pre-existing diagnostics unchanged)
- [x] `uv run pytest` -- 266 passed, 17 deselected
- [ ] `pre-commit run --all-files` -- all hooks pass

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
| 2026-03-11 | Implemented `rotate_encryption_keys()` utility with `RotationResult` dataclass, ADR-009, how-to guide, unit tests (9), and integration tests (6). Exported from public API. All 266 tests pass. |

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `rotate_encryption_keys(db_url, old_backend, new_backend) -> RotationResult` as a standalone async function in `src/adk_secure_sessions/rotation.py`. Bypasses the `EncryptedJSON` TypeDecorator entirely — reads raw base64 TEXT, parses envelope, decrypts with `old_backend.sync_decrypt` via `asyncio.to_thread()`, re-encrypts with `new_backend.sync_encrypt`, writes back with `UPDATE WHERE update_time = :read_time` optimistic concurrency guard.
- `RotationResult(rotated, skipped)` dataclass tracks successfully re-encrypted records and concurrent-write skips. Events table (`has_update_time=False`) does not increment skipped on 0 rowcount (cascade-deleted rows vs. concurrent writes).
- Decision: No `EncryptionCoordinator` class needed — the standalone function has single responsibility and minimal surface area. Documented in ADR-009.
- Optimistic concurrency uses `update_time` column (already present in `sessions`, `app_states`, `user_states`) rather than a new `version` column — avoids overriding ADK CRUD methods.
- 9 unit tests (mocked engine) + 6 integration tests (real SQLite + real FernetBackend keys). All 266 tests in suite pass.
- Fixed import sort order in `__init__.py` (ruff I001: `rotation` must sort between `protocols` and `serialization`).
- Fixed line-length violations in integration test docstring (ruff E501) and reformatted 3 files (ruff format).

### File List

- `src/adk_secure_sessions/rotation.py` (new)
- `src/adk_secure_sessions/__init__.py` (modified — added `RotationResult`, `rotate_encryption_keys` imports and `__all__` entries)
- `tests/unit/test_rotation.py` (new)
- `tests/integration/test_key_rotation.py` (new)
- `docs/adr/ADR-009-key-rotation-strategy.md` (new)
- `docs/how-to/key-rotation.md` (new)
- `mkdocs.yml` (modified — added How-To Guides nav section, ADR-009 entry, fixed missing ADR-008 entry)
