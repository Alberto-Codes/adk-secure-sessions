# Tasks: Serialization Layer

**Input**: Design documents from `/specs/005-serialization-layer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/serialization.py

**Tests**: Included — the spec references pytest + pytest-asyncio + pytest-mock and the plan explicitly lists test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — new module scaffolding and exception additions

- [X] T001 Add `SerializationError` exception class to `src/adk_secure_sessions/exceptions.py`
- [X] T002 Export `SerializationError` from `src/adk_secure_sessions/__init__.py` and add to `__all__`
- [X] T003 Create empty `src/adk_secure_sessions/serialization.py` with module docstring, imports, and constant definitions (`ENVELOPE_VERSION_1`, `BACKEND_FERNET`, `BACKEND_REGISTRY`) per `contracts/serialization.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Envelope helper functions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `_build_envelope(version: int, backend_id: int, ciphertext: bytes) -> bytes` private helper in `src/adk_secure_sessions/serialization.py`
- [X] T005 Implement `_parse_envelope(envelope: bytes) -> tuple[int, int, bytes]` private helper in `src/adk_secure_sessions/serialization.py` that validates minimum length (3 bytes), recognized version byte, and recognized backend ID — raises `DecryptionError` on failure
- [X] T006 [P] Write tests for `SerializationError` hierarchy membership in `tests/unit/test_exceptions.py`
- [X] T007 [P] Write tests for `_build_envelope` and `_parse_envelope` helpers (valid round-trip, too-short input, unknown version, unknown backend ID) in `tests/unit/test_serialization.py`

**Checkpoint**: Envelope helpers ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Encrypt State on Write (Priority: P1) 🎯 MVP

**Goal**: Serialize a session state dictionary into a single encrypted envelope blob

**Independent Test**: Pass a Python dictionary through `encrypt_session`, verify output is opaque bytes with correct 2-byte header, and that it cannot be read without the correct key

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Write test for `encrypt_session` with simple dict `{"ssn": "123-45-6789"}` — assert output starts with `b'\x01\x01'` and ciphertext differs from plaintext JSON in `tests/unit/test_serialization.py`
- [X] T009 [P] [US1] Write test for `encrypt_session` with nested dict `{"user": {"name": "Alice", "age": 30}}` in `tests/unit/test_serialization.py`
- [X] T010 [P] [US1] Write test for `encrypt_session` with empty dict `{}` in `tests/unit/test_serialization.py`
- [X] T011 [P] [US1] Write test for `encrypt_session` with non-serializable input (e.g., `datetime`) — assert `SerializationError` is raised in `tests/unit/test_serialization.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `encrypt_session(data, backend, backend_id) -> bytes` in `src/adk_secure_sessions/serialization.py` per contract: `json.dumps()` → `encode()` → `backend.encrypt()` → `_build_envelope()`; catch `TypeError`/`ValueError` from `json.dumps` and wrap in `SerializationError`
- [X] T013 [US1] Verify all US1 tests pass by running `uv run pytest tests/unit/test_serialization.py -k "encrypt_session"`

**Checkpoint**: `encrypt_session` works — dictionaries can be encrypted into envelope format

---

## Phase 4: User Story 2 — Decrypt State on Read (Priority: P1)

**Goal**: Deserialize an encrypted envelope blob back into the original state dictionary

**Independent Test**: Encrypt a known dictionary with `encrypt_session`, then decrypt with `decrypt_session` and compare to original

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US2] Write round-trip test: `encrypt_session` → `decrypt_session` with type-diverse dict (strings, numbers, booleans, nulls, nested dicts, lists) in `tests/unit/test_serialization.py`
- [X] T015 [P] [US2] Write test for `decrypt_session` with tampered ciphertext bytes — assert `DecryptionError` raised in `tests/unit/test_serialization.py`
- [X] T016 [P] [US2] Write test for `decrypt_session` with truncated/empty envelope — assert `DecryptionError` raised in `tests/unit/test_serialization.py`
- [X] T017 [P] [US2] Write test for `decrypt_session` with wrong-key backend — assert `DecryptionError` raised in `tests/unit/test_serialization.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `decrypt_session(envelope, backend) -> dict` in `src/adk_secure_sessions/serialization.py` per contract: `_parse_envelope()` → `backend.decrypt()` → `json.loads()`; wrap `json.JSONDecodeError` in `SerializationError`
- [X] T019 [US2] Verify all US1 + US2 tests pass by running `uv run pytest tests/unit/test_serialization.py -k "session"`

**Checkpoint**: Full dict round-trip works — encrypt and decrypt session state end-to-end

---

## Phase 5: User Story 3 — Self-Describing Encrypted Format (Priority: P2)

**Goal**: Ensure encrypted output carries version and backend identifier prefix for future migration support

**Independent Test**: Inspect raw bytes of encrypted blob and verify first two bytes encode expected version and backend ID

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US3] Write test verifying envelope byte 0 == `ENVELOPE_VERSION_1` and byte 1 == `BACKEND_FERNET` for Fernet-encrypted output in `tests/unit/test_serialization.py`
- [X] T021 [P] [US3] Write test for decryption with unrecognized version byte `0xFF` — assert `DecryptionError` with message indicating unsupported format in `tests/unit/test_serialization.py`
- [X] T022 [P] [US3] Write test for decryption with unrecognized backend ID byte `0xFF` — assert `DecryptionError` with message indicating unsupported backend in `tests/unit/test_serialization.py`
- [X] T023 [P] [US3] Write test verifying two envelopes with different `backend_id` args produce different second bytes in `tests/unit/test_serialization.py`

### Implementation for User Story 3

- [X] T024 [US3] Verify all US3 tests pass (envelope format validation is already implemented in Phase 2 helpers and Phase 3–4 functions) — no new production code expected; if any test fails, fix the relevant helper or function in `src/adk_secure_sessions/serialization.py`

**Checkpoint**: Envelope self-description verified — version and backend bytes are correct and validated on read

---

## Phase 6: User Story 4 — Encrypt Event Data on Write (Priority: P2)

**Goal**: Encrypt pre-serialized JSON strings (e.g., ADK Event `model_dump_json()` output) into envelopes and decrypt back to strings

**Independent Test**: Pass a JSON string through `encrypt_json`, decrypt with `decrypt_json`, and compare to original

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T025 [P] [US4] Write round-trip test: `encrypt_json` → `decrypt_json` with a sample JSON string `'{"event": "click", "ts": 1234567890}'` in `tests/unit/test_serialization.py`
- [X] T026 [P] [US4] Write test verifying `encrypt_json` output starts with `b'\x01\x01'` envelope header in `tests/unit/test_serialization.py`
- [X] T027 [P] [US4] Write test for `decrypt_json` with tampered envelope — assert `DecryptionError` raised in `tests/unit/test_serialization.py`

### Implementation for User Story 4

- [X] T028 [US4] Implement `encrypt_json(json_str, backend, backend_id) -> bytes` in `src/adk_secure_sessions/serialization.py` per contract: `encode("utf-8")` → `backend.encrypt()` → `_build_envelope()`
- [X] T029 [US4] Implement `decrypt_json(envelope, backend) -> str` in `src/adk_secure_sessions/serialization.py` per contract: `_parse_envelope()` → `backend.decrypt()` → `decode("utf-8")`
- [X] T030 [US4] Verify all US4 tests pass by running `uv run pytest tests/unit/test_serialization.py -k "json"`

**Checkpoint**: JSON string round-trip works — events can be encrypted and decrypted

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Add serialization public API exports (`encrypt_session`, `decrypt_session`, `encrypt_json`, `decrypt_json`, `BACKEND_FERNET`, `ENVELOPE_VERSION_1`) to `src/adk_secure_sessions/__init__.py` and `__all__`
- [X] T032 [P] Write edge-case test for Unicode data round-trip (`{"name": "日本語"}`) in `tests/unit/test_serialization.py`
- [X] T033 [P] Write edge-case test verifying error messages from serialization functions do not contain plaintext data or key material in `tests/unit/test_serialization.py`
- [X] T034 Run full test suite with `uv run pytest` and verify all tests pass
- [X] T035 Run linting and formatting with `uv run ruff check . && uv run ruff format .`
- [X] T036 Run full quality pipeline with `bash scripts/code_quality_check.sh --all --verbose`
- [X] T037 Validate quickstart.md examples work against the implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on Phase 2 + US1 (needs `encrypt_session` to produce test fixtures)
- **US3 (Phase 5)**: Depends on Phase 2 + US1 (inspects envelope output from `encrypt_session`)
- **US4 (Phase 6)**: Depends on Phase 2 only (independent of US1/US2 — different function pair)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Requires US1's `encrypt_session` to generate test inputs
- **US3 (P2)**: Requires US1 to produce envelopes for byte inspection; no new production code
- **US4 (P2)**: Independent of US1/US2/US3 — can run in parallel with US2/US3 after Phase 2

### Parallel Opportunities

- **Phase 1**: T001, T002, T003 are sequential (T002 depends on T001, T003 is independent)
- **Phase 2**: T004 + T005 sequential (same file); T006 + T007 parallel (different files); T006/T007 parallel with T004/T005
- **Phase 3**: T008–T011 all parallel (test functions in same file, no interdependencies)
- **Phase 4**: T014–T017 all parallel
- **Phase 5**: T020–T023 all parallel
- **Phase 6**: T025–T027 all parallel; T028 + T029 sequential (same file); US4 parallel with US2/US3
- **Phase 7**: T031–T033 all parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (they target different test functions):
Task: "T008 - Test encrypt_session with simple dict"
Task: "T009 - Test encrypt_session with nested dict"
Task: "T010 - Test encrypt_session with empty dict"
Task: "T011 - Test encrypt_session with non-serializable input"

# Then implement (single file, sequential):
Task: "T012 - Implement encrypt_session"
Task: "T013 - Verify US1 tests pass"
```

## Parallel Example: US4 alongside US2/US3

```bash
# After Phase 2 completes, these can run in parallel:
Stream A: US1 → US2 → US3 (sequential dependency)
Stream B: US4 (independent)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T007)
3. Complete Phase 3: US1 — Encrypt State (T008–T013)
4. Complete Phase 4: US2 — Decrypt State (T014–T019)
5. **STOP and VALIDATE**: Full dict round-trip works independently
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 + US2 → Dict round-trip works (MVP!)
3. US3 → Envelope format verified (no new code expected)
4. US4 → JSON string encryption works
5. Polish → Exports, edge cases, quality gates

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 37 |
| **Phase 1 (Setup)** | 3 tasks |
| **Phase 2 (Foundational)** | 4 tasks |
| **US1 — Encrypt State (P1)** | 6 tasks |
| **US2 — Decrypt State (P1)** | 6 tasks |
| **US3 — Self-Describing Format (P2)** | 5 tasks |
| **US4 — Encrypt Events (P2)** | 6 tasks |
| **Polish** | 7 tasks |
| **Parallel opportunities** | Tests within each story; US4 parallel with US2/US3 |
| **Suggested MVP** | US1 + US2 (Phases 1–4, 19 tasks) |
