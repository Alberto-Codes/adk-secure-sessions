# Tasks: Encrypted Session Service

**Input**: Design documents from `/specs/006-encrypted-session-service/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests included as this is a library project requiring comprehensive testing.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and services directory structure

- [ ] T001 Create services package directory at src/adk_secure_sessions/services/
- [ ] T002 Create services/__init__.py with EncryptedSessionService export at src/adk_secure_sessions/services/__init__.py
- [ ] T003 [P] Add aiosqlite>=0.19.0 dependency to pyproject.toml
- [ ] T004 [P] Create integration tests directory at tests/integration/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create EncryptedSessionService class skeleton with constructor (db_path, backend, backend_id) in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T006 Implement database initialization method (_init_db) with schema from data-model.md in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T007 Add BaseSessionService inheritance and required imports from google.adk in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T008 Export EncryptedSessionService from package __init__.py at src/adk_secure_sessions/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 2 - Create and Retrieve Encrypted Sessions (Priority: P1) 🎯 MVP

**Goal**: Enable creating sessions with encrypted state and retrieving them with decrypted state

**Independent Test**: Create a session with `{"secret": "value"}`, verify database contains encrypted data, retrieve session and verify plaintext is returned correctly

### Tests for User Story 2

- [ ] T009 [P] [US2] Unit test for create_session encrypts state in tests/unit/test_encrypted_session_service.py
- [ ] T010 [P] [US2] Unit test for create_session generates UUID when session_id not provided in tests/unit/test_encrypted_session_service.py
- [ ] T011 [P] [US2] Unit test for create_session raises AlreadyExistsError for duplicate ID in tests/unit/test_encrypted_session_service.py
- [ ] T012 [P] [US2] Unit test for get_session returns decrypted state in tests/unit/test_encrypted_session_service.py
- [ ] T013 [P] [US2] Unit test for get_session returns None for non-existent session in tests/unit/test_encrypted_session_service.py
- [ ] T014 [P] [US2] Unit test for get_session with GetSessionConfig filters events in tests/unit/test_encrypted_session_service.py

### Implementation for User Story 2

- [ ] T015 [US2] Implement create_session method with state encryption in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T016 [US2] Implement get_session method with state decryption in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T017 [US2] Implement _get_app_state helper for app-level state merging in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T018 [US2] Implement _get_user_state helper for user-level state merging in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T019 [US2] Implement _get_events helper for event retrieval with filtering in src/adk_secure_sessions/services/encrypted_session.py

**Checkpoint**: User Story 2 should be fully functional - sessions can be created and retrieved with encryption/decryption

---

## Phase 4: User Story 3 - Append Events with Encrypted Data (Priority: P1)

**Goal**: Enable appending events to sessions with encrypted event data and state deltas

**Independent Test**: Append events to a session, inspect database to verify event_data is encrypted, retrieve session and verify events are decrypted

### Tests for User Story 3

- [ ] T020 [P] [US3] Unit test for append_event encrypts event data in tests/unit/test_encrypted_session_service.py
- [ ] T021 [P] [US3] Unit test for append_event extracts and persists app state delta in tests/unit/test_encrypted_session_service.py
- [ ] T022 [P] [US3] Unit test for append_event extracts and persists user state delta in tests/unit/test_encrypted_session_service.py
- [ ] T023 [P] [US3] Unit test for append_event updates session state in tests/unit/test_encrypted_session_service.py
- [ ] T024 [P] [US3] Unit test for append_event skips persistence for partial events in tests/unit/test_encrypted_session_service.py
- [ ] T025 [P] [US3] Unit test for append_event discards temp: prefixed keys in tests/unit/test_encrypted_session_service.py

### Implementation for User Story 3

- [ ] T026 [US3] Override append_event method with database persistence in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T027 [US3] Implement _extract_and_persist_state_delta helper in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T028 [US3] Implement _upsert_app_state helper for app state updates in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T029 [US3] Implement _upsert_user_state helper for user state updates in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T030 [US3] Implement _update_session_state_in_db helper in src/adk_secure_sessions/services/encrypted_session.py

**Checkpoint**: User Story 3 should be fully functional - events can be appended with encrypted storage

---

## Phase 5: User Story 4 - List and Delete Sessions (Priority: P2)

**Goal**: Enable listing sessions for an application and deleting sessions

**Independent Test**: Create multiple sessions, list them to verify all returned with decrypted state, delete one and confirm removal

### Tests for User Story 4

- [ ] T031 [P] [US4] Unit test for list_sessions returns all sessions for app in tests/unit/test_encrypted_session_service.py
- [ ] T032 [P] [US4] Unit test for list_sessions filters by user_id when provided in tests/unit/test_encrypted_session_service.py
- [ ] T033 [P] [US4] Unit test for list_sessions returns decrypted state in tests/unit/test_encrypted_session_service.py
- [ ] T034 [P] [US4] Unit test for delete_session removes session and events in tests/unit/test_encrypted_session_service.py
- [ ] T035 [P] [US4] Unit test for delete_session is idempotent (no error if not exists) in tests/unit/test_encrypted_session_service.py

### Implementation for User Story 4

- [ ] T036 [US4] Implement list_sessions method with state decryption in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T037 [US4] Implement delete_session method with cascade delete in src/adk_secure_sessions/services/encrypted_session.py

**Checkpoint**: User Story 4 should be fully functional - sessions can be listed and deleted

---

## Phase 6: User Story 5 - Async Context Manager for Connection Cleanup (Priority: P2)

**Goal**: Enable safe async context manager usage for database connection lifecycle

**Independent Test**: Use service with `async with` syntax, verify connections are properly acquired and released

### Tests for User Story 5

- [ ] T038 [P] [US5] Unit test for __aenter__ returns service instance in tests/unit/test_encrypted_session_service.py
- [ ] T039 [P] [US5] Unit test for __aexit__ calls close in tests/unit/test_encrypted_session_service.py
- [ ] T040 [P] [US5] Unit test for close properly closes database connection in tests/unit/test_encrypted_session_service.py
- [ ] T041 [P] [US5] Unit test for close is idempotent (no error if called twice) in tests/unit/test_encrypted_session_service.py

### Implementation for User Story 5

- [ ] T042 [US5] Implement close method in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T043 [US5] Implement __aenter__ method in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T044 [US5] Implement __aexit__ method in src/adk_secure_sessions/services/encrypted_session.py

**Checkpoint**: User Story 5 should be fully functional - service can be used as async context manager

---

## Phase 7: User Story 1 - Drop-in Replacement Integration (Priority: P1)

**Goal**: Verify the service works as a drop-in replacement for ADK's DatabaseSessionService

**Independent Test**: Replace DatabaseSessionService with EncryptedSessionService in an ADK agent and verify identical behavior

### Tests for User Story 1

- [ ] T045 [P] [US1] Integration test for BaseSessionService interface conformance in tests/integration/test_adk_integration.py
- [ ] T046 [P] [US1] Integration test for round-trip session workflow (create, append events, get, delete) in tests/integration/test_adk_integration.py
- [ ] T047 [P] [US1] Integration test verifying database contains only encrypted data in tests/integration/test_adk_integration.py
- [ ] T048 [P] [US1] Integration test with mock EncryptionBackend to verify protocol conformance (FR-014) in tests/integration/test_adk_integration.py

### Implementation for User Story 1

- [ ] T049 [US1] Add docstring with usage examples to EncryptedSessionService class in src/adk_secure_sessions/services/encrypted_session.py
- [ ] T050 [US1] Add type annotations for all public methods in src/adk_secure_sessions/services/encrypted_session.py

**Checkpoint**: User Story 1 should be complete - service is verified drop-in replacement

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Edge Case Tests

- [ ] T051 [P] Add edge case tests for wrong encryption key in tests/unit/test_encrypted_session_service.py
- [ ] T052 [P] Add edge case tests for corrupted encrypted data in tests/unit/test_encrypted_session_service.py
- [ ] T053 [P] Add edge case tests for empty state dictionary in tests/unit/test_encrypted_session_service.py
- [ ] T054 [P] Add edge case tests for database connection errors (verify aiosqlite exceptions propagate) in tests/unit/test_encrypted_session_service.py
- [ ] T055 [P] Add edge case tests for concurrent session access (SQLite locking behavior) in tests/unit/test_encrypted_session_service.py
- [ ] T056 [P] Add edge case tests for large state objects (verify handling near size limits) in tests/unit/test_encrypted_session_service.py

### Validation

- [ ] T057 Run code quality check (ruff check, ruff format, pytest)
- [ ] T058 Update CLAUDE.md with feature summary via update-agent-context.sh
- [ ] T059 Run quickstart.md examples as validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 2 (P1)**: Can start after Foundational - Creates foundation for session storage
- **User Story 3 (P1)**: Can start after US2 - Depends on session creation for appending events
- **User Story 4 (P2)**: Can start after US2 - Depends on session creation for listing/deleting
- **User Story 5 (P2)**: Can start after Foundational - Independent lifecycle management
- **User Story 1 (P1)**: Integration testing - Depends on all functionality being implemented

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Helper methods before main methods
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All tests for a user story marked [P] can run in parallel
- User Stories 4 and 5 can run in parallel after US2 completes
- All edge case tests in Polish phase can run in parallel

---

## Parallel Example: User Story 2 Tests

```bash
# Launch all tests for User Story 2 together:
Task: "Unit test for create_session encrypts state"
Task: "Unit test for create_session generates UUID"
Task: "Unit test for create_session raises AlreadyExistsError"
Task: "Unit test for get_session returns decrypted state"
Task: "Unit test for get_session returns None for non-existent"
Task: "Unit test for get_session with GetSessionConfig filters events"
```

---

## Implementation Strategy

### MVP First (User Stories 2 + 3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 2 (create/get sessions)
4. Complete Phase 4: User Story 3 (append events)
5. **STOP and VALIDATE**: Test basic session workflow
6. This delivers core encrypted session functionality

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 2 → Sessions can be created/retrieved → Core MVP
3. Add User Story 3 → Events can be appended → Full agent support
4. Add User Story 4 → List/delete sessions → Management features
5. Add User Story 5 → Context manager → Production-ready cleanup
6. Add User Story 1 → Integration tests → Verified drop-in replacement

### Task Count Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Phase 1: Setup | 4 | 2 parallel |
| Phase 2: Foundational | 4 | 0 parallel |
| Phase 3: US2 Create/Get | 11 | 6 parallel (tests) |
| Phase 4: US3 Events | 11 | 6 parallel (tests) |
| Phase 5: US4 List/Delete | 7 | 5 parallel (tests) |
| Phase 6: US5 Context Mgr | 7 | 4 parallel (tests) |
| Phase 7: US1 Integration | 6 | 4 parallel (tests) |
| Phase 8: Polish | 9 | 6 parallel |
| **Total** | **59** | **33 parallel opportunities** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
