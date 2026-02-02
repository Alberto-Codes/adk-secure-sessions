# Tasks: Implement FernetBackend

**Input**: Design documents from `/specs/003-fernet-backend/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are included as this project uses TDD per existing test infrastructure (`tests/unit/`).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create exception hierarchy and backends package structure

- [ ] T001 Create exception module with `SecureSessionError` and `DecryptionError` in `src/adk_secure_sessions/exceptions.py`
- [ ] T002 Create backends package with `__init__.py` in `src/adk_secure_sessions/backends/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Skeleton FernetBackend class with key derivation logic — MUST be complete before user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Implement `FernetBackend.__init__` with PBKDF2 key derivation and direct Fernet key detection in `src/adk_secure_sessions/backends/fernet.py`
- [ ] T004 Update public API exports to include `FernetBackend`, `SecureSessionError`, `DecryptionError` in `src/adk_secure_sessions/__init__.py`

**Checkpoint**: FernetBackend can be imported and initialized with string or bytes keys

---

## Phase 3: User Story 1 - Encrypt and Decrypt Round-Trip (Priority: P1) 🎯 MVP

**Goal**: A developer can encrypt plaintext bytes and decrypt the ciphertext back to the original plaintext

**Independent Test**: Encrypt a known byte string, decrypt it, verify output matches input

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Write unit test for encrypt/decrypt round-trip in `tests/unit/test_fernet_backend.py`
- [ ] T006 [P] [US1] Write unit test for non-deterministic ciphertext (same plaintext produces different ciphertext) in `tests/unit/test_fernet_backend.py`
- [ ] T007 [P] [US1] Write unit test for empty bytes round-trip in `tests/unit/test_fernet_backend.py`

### Implementation for User Story 1

- [ ] T008 [US1] Implement `FernetBackend.encrypt` async method using `asyncio.to_thread` in `src/adk_secure_sessions/backends/fernet.py`
- [ ] T009 [US1] Implement `FernetBackend.decrypt` async method using `asyncio.to_thread` in `src/adk_secure_sessions/backends/fernet.py`

**Checkpoint**: Encrypt/decrypt round-trip works for all valid inputs. All US1 tests pass.

---

## Phase 4: User Story 2 - Wrong Key Fails Decryption (Priority: P1)

**Goal**: Decryption with a wrong key raises `DecryptionError`, never silently returns wrong data

**Independent Test**: Encrypt with key A, decrypt with key B, verify `DecryptionError` is raised

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US2] Write unit test for wrong key raises `DecryptionError` in `tests/unit/test_fernet_backend.py`
- [ ] T011 [P] [US2] Write unit test for tampered ciphertext raises `DecryptionError` in `tests/unit/test_fernet_backend.py`
- [ ] T012 [P] [US2] Write unit test for malformed/truncated ciphertext raises `DecryptionError` in `tests/unit/test_fernet_backend.py`
- [ ] T013 [P] [US2] Write unit test that error message does not contain key material in `tests/unit/test_fernet_backend.py`

### Implementation for User Story 2

- [ ] T014 [US2] Add `DecryptionError` wrapping of `cryptography.fernet.InvalidToken` in `FernetBackend.decrypt` in `src/adk_secure_sessions/backends/fernet.py`

**Checkpoint**: All decryption failure modes raise `DecryptionError` with safe messages. All US2 tests pass.

---

## Phase 5: User Story 3 - Flexible Key Input (Priority: P2)

**Goal**: Developers can provide keys as `str`, `bytes`, or valid Fernet keys without extra conversion

**Independent Test**: Initialize with a string passphrase, perform encrypt/decrypt round-trip

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US3] Write unit test for string key initialization and round-trip in `tests/unit/test_fernet_backend.py`
- [ ] T016 [P] [US3] Write unit test for bytes key initialization and round-trip in `tests/unit/test_fernet_backend.py`
- [ ] T017 [P] [US3] Write unit test for valid Fernet key passthrough (no derivation) in `tests/unit/test_fernet_backend.py`
- [ ] T018 [P] [US3] Write unit test for empty key raises `ValueError` in `tests/unit/test_fernet_backend.py`

### Implementation for User Story 3

- [ ] T019 [US3] Validate key input and add `TypeError` for non-bytes plaintext in `FernetBackend.encrypt` in `src/adk_secure_sessions/backends/fernet.py`

**Checkpoint**: All key input types work correctly. All US3 tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Protocol conformance, final validation, documentation

- [ ] T020 [P] Write unit test for `isinstance(FernetBackend(...), EncryptionBackend)` protocol check in `tests/unit/test_fernet_backend.py`
- [ ] T021 [P] Write unit test for non-bytes plaintext raises `TypeError` in `tests/unit/test_fernet_backend.py`
- [ ] T022 Run full test suite and verify all tests pass via `uv run pytest tests/unit/test_fernet_backend.py -v`
- [ ] T023 Run code quality pipeline via `bash scripts/code_quality_check.sh --all --verbose`
- [ ] T024 Validate quickstart.md examples work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion
  - US1 and US2 are both P1 but US2 depends on US1 (needs encrypt to test wrong-key decrypt)
  - US3 can proceed in parallel with US2 after US1 completes
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 `encrypt` being implemented (needs ciphertext to test decryption failures)
- **User Story 3 (P2)**: Can start after Phase 2 — No dependencies on other stories (key handling is in `__init__`)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation completes when all story tests pass
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- All test tasks within a story marked [P] can run in parallel
- US3 tests (T015-T018) can run in parallel with US2 implementation (T014)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write unit test for encrypt/decrypt round-trip in tests/unit/test_fernet_backend.py"
Task: "Write unit test for non-deterministic ciphertext in tests/unit/test_fernet_backend.py"
Task: "Write unit test for empty bytes round-trip in tests/unit/test_fernet_backend.py"

# Then implement sequentially:
Task: "Implement FernetBackend.encrypt"
Task: "Implement FernetBackend.decrypt"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (exceptions + backends package)
2. Complete Phase 2: Foundational (FernetBackend init + exports)
3. Complete Phase 3: User Story 1 (encrypt/decrypt round-trip)
4. **STOP and VALIDATE**: Run `uv run pytest tests/unit/test_fernet_backend.py -v`
5. MVP is functional — basic encryption works

### Incremental Delivery

1. Setup + Foundational → Backend can be initialized
2. Add US1 → Encrypt/decrypt works → MVP!
3. Add US2 → Error handling hardened → Security-ready
4. Add US3 → Flexible key input → Developer-friendly
5. Polish → Protocol conformance verified, quality checks pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tests go in single file `tests/unit/test_fernet_backend.py` (organized by test class per story)
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
