# Story 3.3: Multi-Backend Coexistence & Dispatch

Status: review
Branch: feat/serialization-3-3-multi-backend-dispatch
GitHub Issue:

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **operator migrating from Fernet to AES-256-GCM**,
I want **the system to support multiple encryption backends simultaneously, dispatching decryption based on the envelope header**,
so that **I can migrate incrementally without re-encrypting all existing sessions at once**.

## Acceptance Criteria

1. **Given** the service is configured with multiple backends (e.g., Fernet + AES-256-GCM), **when** a new session is created, **then** it is encrypted with the configured primary backend.
2. **Given** the envelope protocol contains a backend ID byte at position 1, **when** a session encrypted with Fernet (`0x01`) is read while AES-256-GCM (`0x02`) is the primary backend, **then** decryption dispatches to Fernet based on the envelope header — not the primary backend.
3. **Given** the service is configured with Fernet as primary, **when** a session encrypted with AES-256-GCM is read, **then** decryption dispatches to AES-256-GCM based on the envelope header.
4. **Given** the envelope references an unregistered backend ID (e.g., `0xFF`), **when** decryption is attempted, **then** the system raises `DecryptionError` with a clear message — no silent corruption or fallback to wrong backend.
5. **Given** the backend registry, **when** a new backend is passed via the constructor API at construction time, **then** it is registered without modifying library internals — registration is final and backends cannot be added after construction (FR19).
6. **Given** a mixed-backend database (sessions encrypted with different backends), **when** `list_sessions` is called, **then** all sessions decrypt correctly regardless of which backend encrypted each one.
7. **Given** `EncryptedSessionService` accepts additional backends, **when** the service is constructed with only one backend and no `additional_backends`, **then** behavior is identical to the current single-backend API (backward compatibility).

## Tasks / Subtasks

- [x] Task 1: Extend `EncryptedJSON` TypeDecorator for multi-backend decrypt dispatch (AC: 2, 3, 4)
  - [x] 1.1 Add `_decrypt_dispatch: dict[int, Callable[[bytes], bytes]]` mapping backend_id to sync_decrypt
  - [x] 1.2 Modify `process_result_value` to read backend_id from parsed envelope and dispatch to the correct decrypt function
  - [x] 1.3 Raise `DecryptionError` with clear message when backend_id has no registered decrypt function
  - [x] 1.4 Keep `_encrypt_fn` + `_backend_id` for write path (primary backend unchanged)

- [x] Task 2: Extend `EncryptedSessionService` constructor for multi-backend (AC: 1, 5, 7)
  - [x] 2.1 Add `additional_backends: Sequence[EncryptionBackend] = ()` parameter to `__init__`
  - [x] 2.2 Validate all backends (primary + additional) conform to `EncryptionBackend` protocol
  - [x] 2.3 Validate no duplicate `backend_id` values across all backends
  - [x] 2.4 Build decrypt dispatch map: `{b.backend_id: b.sync_decrypt for b in all_backends}`
  - [x] 2.5 Pass dispatch map to `EncryptedJSON` constructor
  - [x] 2.6 Ensure single-backend usage (no `additional_backends`) works identically to current API
  - [x] 2.7 Update `EncryptedSessionService` docstring: multi-backend example + explicit note that backends are fixed after construction

- [x] Task 3: Unit tests for `EncryptedJSON` dispatch (AC: 2, 3, 4)
  - [x] 3.1 Test: decrypt routes to correct backend based on envelope backend_id byte
  - [x] 3.2 Test: unregistered backend_id raises `DecryptionError`
  - [x] 3.3 Test: primary backend used for all writes regardless of additional backends

- [x] Task 4: Unit tests for `EncryptedSessionService` multi-backend init (AC: 5, 7)
  - [x] 4.1 Test: service accepts `additional_backends` and constructs dispatch map
  - [x] 4.2 Test: duplicate `backend_id` raises `ConfigurationError`
  - [x] 4.3 Test: non-conforming additional backend raises `ConfigurationError`
  - [x] 4.4 Test: single backend (no additional) works identically to current behavior

- [x] Task 5: Integration test — mixed-backend session lifecycle in `tests/integration/test_multi_backend.py` (AC: 6)
  - [x] 5.1 Create sessions with Fernet backend (service configured with Fernet primary)
  - [x] 5.2 Create a new service with AES-GCM primary + Fernet additional
  - [x] 5.3 Verify `list_sessions` returns all sessions, Fernet-encrypted ones decrypt correctly
  - [x] 5.4 Create new sessions with AES-GCM primary, verify they use AES-GCM envelope
  - [x] 5.5 Create a third service with Fernet primary + AES-GCM additional, verify all sessions from both backends decrypt
  - [x] 5.6 Verify raw DB rows are encrypted (not plaintext JSON) for both backends — encryption boundary assertion

- [x] Task 6: Update public API exports (AC: all)
  - [x] 6.1 No new public symbols needed (additional_backends is a constructor param, not a new class)
  - [x] 6.2 Update `EncryptedSessionService` docstring with multi-backend example
  - [x] 6.3 Verify `test_public_api.py` still passes

### Cross-Cutting Test Maturity (Standing Task)

<!-- Sourced from test-review.md recommendations. The create-story workflow
     picks the next unaddressed item and assigns it here. -->

**Test Review Item**: Add rationale comments to magic constants
**Severity**: P3 (Low)
**Location**: `tests/benchmarks/test_encryption_overhead.py:35`

`N_ITERATIONS = 20`, `_OVERHEAD_THRESHOLD = 1.20`, `_TARGET_SIZE_BYTES = 10240` lack rationale comments. `test_concurrent_writes.py` correctly documents `NUM_COROUTINES` with NFR traceability -- apply same pattern.

- [x] Add rationale comments to `N_ITERATIONS`, `_OVERHEAD_THRESHOLD`, `_TARGET_SIZE_BYTES` in `test_encryption_overhead.py` following the `test_concurrent_writes.py` pattern (NFR traceability + justification)
- [x] Verify new/changed test(s) pass in CI
- [x] Mark item as done in `_bmad-output/test-artifacts/test-review.md`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_multi_backend.py::TestMixedBackendLifecycle::test_new_sessions_use_primary_backend` | pass |
| 2    | `test_type_decorator.py::TestDecryptDispatch::test_dispatch_routes_to_correct_backend_by_envelope_id`, `test_multi_backend.py::TestMixedBackendLifecycle::test_fernet_sessions_readable_after_primary_switch_to_aes_gcm` | pass |
| 3    | `test_type_decorator.py::TestDecryptDispatch::test_dispatch_routes_to_correct_backend_by_envelope_id`, `test_multi_backend.py::TestMixedBackendLifecycle::test_reverse_primary_reads_both_backends` | pass |
| 4    | `test_type_decorator.py::TestDecryptDispatch::test_unregistered_backend_in_dispatch_raises_decryption_error` | pass |
| 5    | `test_encrypted_session_service.py::TestMultiBackendInit::test_accepts_additional_backends`, `test_encrypted_session_service.py::TestMultiBackendInit::test_duplicate_backend_id_raises_configuration_error`, `test_encrypted_session_service.py::TestMultiBackendInit::test_non_conforming_additional_backend_raises_configuration_error` | pass |
| 6    | `test_multi_backend.py::TestMixedBackendLifecycle::test_list_sessions_decrypts_mixed_backend_sessions` | pass |
| 7    | `test_encrypted_session_service.py::TestMultiBackendInit::test_single_backend_no_additional_works_identically`, `test_encrypted_session_service.py::TestSessionCRUD` (all existing tests pass unchanged) | pass |

## Dev Notes

### Architecture: Where Dispatch Happens

The dispatch mechanism lives in `EncryptedJSON` (TypeDecorator), NOT in `serialization.py`. The TypeDecorator is the encryption boundary for SQLAlchemy — it intercepts reads/writes at the column level.

**Current flow (single backend):**
```
process_result_value(text) → base64_decode → _parse_envelope → _decrypt_fn(ciphertext) → json.loads
```

**New flow (multi-backend):**
```
process_result_value(text) → base64_decode → _parse_envelope → dispatch[backend_id](ciphertext) → json.loads
```

The `_parse_envelope` already validates backend_id and returns it. Currently `process_result_value` discards `_backend_id` — this story makes it use it for dispatch.

### Key Design Decisions

1. **Primary backend = first positional arg** — `EncryptedSessionService(db_url, backend, additional_backends=[...])`. The `backend` param is the primary (used for new writes). `additional_backends` provides legacy decrypt capability.

2. **Dispatch map lives in EncryptedJSON (party-mode consensus)** — A `dict[int, Callable]` inside `EncryptedJSON`, NOT a separate `EncryptionCoordinator` class. The architecture doc describes a coordinator as a Phase 3 concept, but party-mode consensus confirmed: a dict is the right abstraction until key rotation (Story 4.4) demands more. The dict is set at construction and never mutated (`cache_ok = True` requires this). No `MappingProxyType` — convention is sufficient.

3. **Construction-time registration only (party-mode consensus)** — FR19 "dynamic registration" means constructor-injected, not post-init mutable. Backends are fixed after construction. The docstring must state this explicitly. `EncryptedJSON`'s `cache_ok = True` means SQLAlchemy may cache the type instance — post-init mutation would be a correctness bug.

4. **No changes to `serialization.py`** — The module-level functions (`encrypt_session`, `decrypt_session`) are used by the standalone serialization API, not by the service. The service uses `EncryptedJSON`. The `BACKEND_REGISTRY` in `serialization.py` remains a validation registry (name lookup), not a dispatch registry. The dispatch map is instance-level in `EncryptedJSON`.

5. **No changes to `protocols.py`** — The `EncryptionBackend` protocol already has `backend_id`, `sync_encrypt`, `sync_decrypt`. No new protocol members needed.

6. **Backward compatibility** — When `additional_backends` is empty (default), the dispatch map has exactly one entry: `{primary.backend_id: primary.sync_decrypt}`. Behavior is identical to current single-backend usage.

### Files to Modify

| File | Change | Reason |
|------|--------|--------|
| `src/adk_secure_sessions/services/type_decorator.py` | Add `_decrypt_dispatch` dict, modify `process_result_value` to dispatch by backend_id | Core dispatch mechanism |
| `src/adk_secure_sessions/services/encrypted_session.py` | Add `additional_backends` param, build dispatch map, pass to `EncryptedJSON` | Service API extension |
| `tests/unit/test_type_decorator.py` | Add dispatch tests (correct routing, unregistered ID, primary-only write) | Task 3 |
| `tests/unit/test_encrypted_session_service.py` | Add multi-backend init tests (dispatch map, duplicates, non-conforming, backward compat) | Task 4 |
| `tests/integration/test_multi_backend.py` (new file) | Mixed-backend lifecycle integration test (party-mode consensus: separate file due to distinct fixture tree, 500-line threshold, 1:1 story traceability) | Task 5 |
| `tests/benchmarks/test_encryption_overhead.py` | Add rationale comments to magic constants | Cross-cutting |

### Peripheral Config Impact

No peripheral config impact. This story modifies internal service/TypeDecorator code and tests only. No changes to CI, pyproject.toml, mkdocs.yml, sonar-project.properties, or pre-commit config.

### Architecture Compliance

- **Protocols over inheritance** (ADR-001): No protocol changes. Backends still conform via structural subtyping.
- **Async-first** (ADR-002): TypeDecorator operates in sync context (SQLAlchemy requirement). `sync_decrypt` is the correct method to use in the dispatch map.
- **Envelope is wire protocol** (ADR-000): Envelope format unchanged. Dispatch reads the existing backend_id byte — no header modifications.
- **Encryption is a contract** (ADR-003): Every data path still goes through encrypt/decrypt. Adding dispatch doesn't bypass encryption — it routes to the correct decryptor.
- **ADK is upstream** (ADR-004): No changes to overridden methods. `_get_schema_classes` and `_prepare_tables` unchanged. Only `__init__` gains a new parameter.

### Library/Framework Requirements

- **No new dependencies**. All dispatch logic uses stdlib `dict` lookup.
- `cryptography >= 44.0.0` (already present) for both Fernet and AES-GCM backends.
- `google-adk >= 1.22.0` (already present) for `DatabaseSessionService`.

### Testing Requirements

- **Unit tests** mock backends (mock `sync_encrypt`/`sync_decrypt`/`backend_id`) to isolate dispatch logic.
- **Integration tests** use real `FernetBackend` + real `AesGcmBackend` + real SQLite.
- **Encryption boundary invariant**: Integration test must verify raw DB rows are encrypted (not plaintext) for both backends.
- **Wrong-key raises `DecryptionError`**: Verify for both backends in multi-backend scenario.
- Mark all new test files/classes with `@pytest.mark.unit` or `@pytest.mark.integration`.
- Async generator fixtures with `await svc.close()` teardown for any service fixtures.

### Previous Story Intelligence (Story 3.2)

**Patterns established:**
- Constants at module top: `_SALT_MARKER`, `_SALT_LENGTH`, etc. Follow this for any new constants.
- Error message extraction: `_DECRYPT_FAILED_MSG` constant for reused error strings. Apply if dispatch error messages are reused.
- Test file split at 500 lines: If `test_type_decorator.py` (currently 153 lines) or `test_encrypted_session_service.py` (currently 312 lines) would exceed 500 lines after adding tests, split proactively.
- Factory pattern for test fixtures: `_make_runner` factory in `test_adk_runner.py`. Consider similar pattern if multiple backend combinations need testing.

**Problems to avoid:**
- Per-operation PBKDF2 performance regression (not applicable here — dispatch is a dict lookup, O(1))
- Bare `Exception` catch — always catch specific exception types

### Git Intelligence

Recent commits (last 2 merged PRs):
- `64f2a76` feat(backend): add per-key random salt key derivation to FernetBackend (#143) — modified `fernet.py`, added `test_fernet_salt.py`, updated `ADR-008`, `docs/algorithms.md`
- `9ea7881` feat(backend): add AES-256-GCM encryption backend (#141) — added `aes_gcm.py`, `test_aes_gcm_backend.py`, updated `serialization.py` (BACKEND_AES_GCM, BACKEND_REGISTRY), updated `protocols.py` (sync_encrypt, sync_decrypt, backend_id)

Both backends are fully implemented with salt support. The dispatch story builds on their completed work.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `src/adk_secure_sessions/services/encrypted_session.py` docstring | Add multi-backend usage example |
| `docs/reference/` (auto-generated by griffe) | Will auto-update from docstring changes |
| README.md | Consider adding multi-backend migration example (optional, can defer to 3.4) |

### Project Structure Notes

- All source changes in `src/adk_secure_sessions/services/` — aligned with existing structure
- New integration test in `tests/integration/test_multi_backend.py` (party-mode consensus)
- No new modules or packages created

### References

- [Source: src/adk_secure_sessions/services/type_decorator.py] — `EncryptedJSON` TypeDecorator, lines 49-163
- [Source: src/adk_secure_sessions/services/encrypted_session.py] — `EncryptedSessionService.__init__`, lines 81-122
- [Source: src/adk_secure_sessions/serialization.py] — `BACKEND_REGISTRY`, `_parse_envelope`, lines 50-107
- [Source: src/adk_secure_sessions/protocols.py] — `EncryptionBackend` protocol, lines 46-187
- [Source: src/adk_secure_sessions/backends/aes_gcm.py] — `AesGcmBackend`, lines 48-210
- [Source: _bmad-output/planning-artifacts/epics.md] — Epic 3, Story 3.3 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — Envelope protocol, backend registry, multi-backend strategy
- [Source: docs/adr/ADR-000-strategy-decorator-architecture.md] — Envelope wire protocol
- [Source: docs/adr/ADR-001-protocol-based-interfaces.md] — Protocols over inheritance

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 246 passed, 98.78% coverage
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
| 2026-03-07 | Story created by SM agent -- comprehensive context engine |
| 2026-03-07 | Party mode consensus: (1) dispatch dict in EncryptedJSON, no EncryptionCoordinator — deferred to Story 4.4; (2) construction-time registration only, FR19 = constructor-injected; (3) new test_multi_backend.py file; AC #5 clarified, Task 2 docstring requirement added, Task 5 file target + encryption boundary assertion added |
| 2026-03-07 | Implementation complete — all 6 tasks + cross-cutting done. 246 tests pass, 98.78% coverage. Multi-backend dispatch via EncryptedJSON._decrypt_dispatch dict, EncryptedSessionService.additional_backends param, 5 integration tests in test_multi_backend.py |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered.

### Completion Notes List

- Task 1: Replaced `decrypt_fn` with `decrypt_dispatch: dict[int, Callable]` in `EncryptedJSON.__init__`. `process_result_value` now reads `backend_id` from parsed envelope and dispatches to the correct decrypt function. Unregistered backend_id raises `DecryptionError` with hex-formatted message. Write path unchanged (uses `_encrypt_fn` + `_backend_id`).
- Task 2: Added `additional_backends: Sequence[EncryptionBackend] = ()` to `EncryptedSessionService.__init__`. Validates all backends conform to protocol, rejects duplicate backend_ids with `ConfigurationError`. Builds dispatch map from all backends. Updated class and module docstrings with multi-backend migration examples and construction-time finality note.
- Task 3: 4 unit tests in `TestDecryptDispatch` — dispatch routing by envelope header, primary backend read, unregistered backend error, write-path primary-only.
- Task 4: 4 unit tests in `TestMultiBackendInit` — additional_backends acceptance, duplicate backend_id rejection, non-conforming backend rejection, single-backend backward compat.
- Task 5: 5 integration tests in `test_multi_backend.py` — Fernet-to-AES migration, mixed-backend list_sessions, primary backend envelope verification, reverse-primary reads, raw DB encryption boundary for both backends.
- Task 6: No new public symbols. Docstrings updated. `test_public_api.py` passes.
- Cross-cutting: Added rationale docstrings to `N_ITERATIONS`, `_OVERHEAD_THRESHOLD`, `_TARGET_SIZE_BYTES`. Updated test-review.md.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `src/adk_secure_sessions/services/encrypted_session.py` docstring | Multi-backend migration example added to module and class docstrings |
| `src/adk_secure_sessions/services/type_decorator.py` docstring | Updated constructor examples to use `decrypt_dispatch` |
| `docs/reference/` (auto-generated by griffe) | Will auto-update from docstring changes |

### File List

- `src/adk_secure_sessions/services/type_decorator.py` — modified (decrypt_dispatch, process_result_value dispatch)
- `src/adk_secure_sessions/services/encrypted_session.py` — modified (additional_backends param, dispatch map, docstrings)
- `tests/unit/test_type_decorator.py` — modified (updated fixtures + 4 dispatch tests)
- `tests/unit/test_encrypted_session_service.py` — modified (4 multi-backend init tests)
- `tests/integration/test_multi_backend.py` — new (5 mixed-backend lifecycle tests)
- `tests/benchmarks/test_encryption_overhead.py` — modified (rationale docstrings)
- `tests/benchmarks/conftest.py` — modified (rationale docstring for _TARGET_SIZE_BYTES)
- `_bmad-output/test-artifacts/test-review.md` — modified (marked recommendation #5 done)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — modified (status update)
- `_bmad-output/implementation-artifacts/3-3-multi-backend-coexistence-dispatch.md` — modified (story tracking)
