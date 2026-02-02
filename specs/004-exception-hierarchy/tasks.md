# Tasks: Exception Hierarchy

**Input**: Design documents from `/specs/004-exception-hierarchy/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Included — the spec requires verifying hierarchy relationships, sibling independence, and message safety.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No setup needed — project structure and dependencies already exist.

*Phase skipped: existing project, no new dependencies.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add `EncryptionError` to the exception module and export it — required before any user story testing.

**⚠️ CRITICAL**: US1 and US2 both depend on `EncryptionError` existing.

- [ ] T001 Add `EncryptionError(SecureSessionError)` class with Google-style docstring to `src/adk_secure_sessions/exceptions.py`
- [ ] T002 Add `EncryptionError` import and `__all__` entry to `src/adk_secure_sessions/__init__.py`

**Checkpoint**: `EncryptionError` importable from `adk_secure_sessions` — foundational code complete.

---

## Phase 3: User Story 1 — Catch All Library Errors (Priority: P1) 🎯 MVP

**Goal**: Verify that `SecureSessionError` catches all library exceptions including the new `EncryptionError`.

**Independent Test**: Raise each exception type and confirm `except SecureSessionError` catches all of them.

### Tests for User Story 1

- [ ] T003 [P] [US1] Test `SecureSessionError` inherits from `Exception` in `tests/unit/test_exceptions.py`
- [ ] T004 [P] [US1] Test `EncryptionError` is caught by `except SecureSessionError` in `tests/unit/test_exceptions.py`
- [ ] T005 [P] [US1] Test `DecryptionError` is caught by `except SecureSessionError` in `tests/unit/test_exceptions.py`
- [ ] T006 [P] [US1] Test `SecureSessionError` is not caught by unrelated handlers (e.g., `except ValueError`) in `tests/unit/test_exceptions.py`

**Checkpoint**: All catch-all behavior verified — US1 complete.

---

## Phase 4: User Story 2 — Distinguish Encryption from Decryption Errors (Priority: P1)

**Goal**: Verify that `EncryptionError` and `DecryptionError` are independent siblings — catching one does not catch the other.

**Independent Test**: Raise `DecryptionError`, confirm `except EncryptionError` does not catch it, and vice versa.

### Tests for User Story 2

- [ ] T007 [P] [US2] Test `EncryptionError` and `DecryptionError` are both subclasses of `SecureSessionError` (`issubclass`) in `tests/unit/test_exceptions.py`
- [ ] T008 [P] [US2] Test `EncryptionError` is NOT a subclass of `DecryptionError` and vice versa in `tests/unit/test_exceptions.py`
- [ ] T009 [P] [US2] Test raising `DecryptionError` is not caught by `except EncryptionError` in `tests/unit/test_exceptions.py`
- [ ] T010 [P] [US2] Test raising `EncryptionError` is not caught by `except DecryptionError` in `tests/unit/test_exceptions.py`

**Checkpoint**: Sibling independence verified — US2 complete.

---

## Phase 5: User Story 3 — Safe Error Messages (Priority: P2)

**Goal**: Verify exception messages do not leak sensitive data and that exception chaining preserves cause.

**Independent Test**: Construct exceptions with messages and verify no sensitive patterns; verify `raise ... from ...` preserves `__cause__`.

### Tests for User Story 3

- [ ] T011 [P] [US3] Test all exception classes accept and store a message string in `tests/unit/test_exceptions.py`
- [ ] T012 [P] [US3] Test exception chaining (`raise EncryptionError(...) from original`) preserves `__cause__` in `tests/unit/test_exceptions.py`
- [ ] T013 [P] [US3] Test exception chaining (`raise DecryptionError(...) from original`) preserves `__cause__` in `tests/unit/test_exceptions.py`

**Checkpoint**: Message handling and chaining verified — US3 complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories.

- [ ] T014 Run `uv run ruff check .` and `uv run ruff format .` to verify code quality
- [ ] T015 Run `uv run pytest` to verify all tests pass (existing + new)
- [ ] T016 Run quickstart.md validation — verify all import examples work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — can start immediately
- **US1 (Phase 3)**: Depends on Phase 2 (T001, T002)
- **US2 (Phase 4)**: Depends on Phase 2 (T001, T002)
- **US3 (Phase 5)**: Depends on Phase 2 (T001, T002)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US3 (P2)**: Can start after Phase 2 — no dependencies on other stories

### Parallel Opportunities

- T001 and T002 are sequential (T002 imports what T001 creates)
- All test tasks within a phase (T003–T006, T007–T010, T011–T013) can run in parallel (same file, different test functions)
- US1, US2, US3 test phases can run in parallel after Phase 2

---

## Parallel Example: All User Stories

```bash
# After Phase 2 completes, all test tasks can be written in parallel:
Task: "T003-T006 — US1 catch-all tests"
Task: "T007-T010 — US2 sibling tests"
Task: "T011-T013 — US3 message safety tests"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 2: Add `EncryptionError` (T001–T002)
2. Complete Phase 3: US1 catch-all tests (T003–T006)
3. Complete Phase 4: US2 sibling tests (T007–T010)
4. **STOP and VALIDATE**: Run `uv run pytest`
5. This covers both P1 stories — MVP complete

### Full Delivery

1. Complete MVP above
2. Add Phase 5: US3 message safety tests (T011–T013)
3. Complete Phase 6: Polish (T014–T016)
4. All acceptance criteria verified

---

## Notes

- All tests go in a single new file: `tests/unit/test_exceptions.py`
- Only 2 source files are modified (T001, T002) — the rest is tests
- No changes to `FernetBackend` or other existing code
- Commit after Phase 2 + all tests for a clean history
