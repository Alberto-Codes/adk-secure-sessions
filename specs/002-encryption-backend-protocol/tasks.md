# Tasks: EncryptionBackend Protocol

**Input**: Design documents from `/specs/002-encryption-backend-protocol/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md

**Tests**: Not explicitly requested in spec. Unit tests included as they
are integral to verifying protocol conformance (the primary deliverable).

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure test infrastructure is ready

- [ ] T001 Create tests/unit/ directory and verify pytest + pytest-asyncio are in dev dependencies

**Checkpoint**: Test runner works with `uv run pytest`

---

## Phase 2: User Story 1 — Define Encryption Contract (Priority: P1) 🎯 MVP

**Goal**: `EncryptionBackend` protocol with `encrypt` and `decrypt` async methods

**Independent Test**: Create a minimal class with matching methods and
confirm it satisfies the protocol via static type checking

### Implementation for User Story 1

- [ ] T002 [US1] Create `EncryptionBackend` protocol class in src/adk_secure_sessions/protocols.py — two `async def` methods (`encrypt(self, plaintext: bytes) -> bytes`, `decrypt(self, ciphertext: bytes) -> bytes`), `@runtime_checkable` decorator, module and class docstrings documenting contract + known limitations. This MUST be a Protocol, not an ABC (FR-007). No alternative base class.
- [ ] T003 [US1] Export `EncryptionBackend` from src/adk_secure_sessions/__init__.py

**Checkpoint**: Protocol importable via `from adk_secure_sessions.protocols import EncryptionBackend`

---

## Phase 3: User Story 2 — Runtime Validation (Priority: P1)

**Goal**: Verify `isinstance()` checks work for conforming and non-conforming objects

**Independent Test**: Pass conforming, partial, and non-conforming objects
to `isinstance(obj, EncryptionBackend)` and assert expected results

### Implementation for User Story 2

- [ ] T004 [US2] Write unit tests in tests/unit/test_protocols.py — test conforming class returns `True`, class missing `decrypt` returns `False`, class missing `encrypt` returns `False`, class with no methods returns `False`, sync methods return `True` (document known limitation)

**Checkpoint**: `uv run pytest tests/unit/test_protocols.py` passes

---

## Phase 4: User Story 3 — Third-Party Extensibility (Priority: P2)

**Goal**: Verify a backend defined without importing `adk_secure_sessions` passes protocol checks

**Independent Test**: Define a class in the test file without importing
the protocol, then verify it passes `isinstance()` after importing

### Implementation for User Story 3

- [ ] T005 [US3] Add extensibility test in tests/unit/test_protocols.py — define a standalone class (no imports from adk_secure_sessions for the class definition), then assert `isinstance(obj, EncryptionBackend)` returns `True`

**Checkpoint**: Third-party extensibility verified without inheritance

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validation and cleanup

- [ ] T006 Run `uv run ruff check src/adk_secure_sessions/protocols.py` and fix any issues
- [ ] T007 Run type checker against src/adk_secure_sessions/protocols.py
- [ ] T008 Validate quickstart.md examples match actual protocol API in specs/002-encryption-backend-protocol/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on Phase 1
- **US2 (Phase 3)**: Depends on Phase 2 (needs protocol to test against)
- **US3 (Phase 4)**: Depends on Phase 2 (needs protocol to test against)
- **Polish (Phase 5)**: Depends on Phases 2–4

### User Story Dependencies

- **US1 (P1)**: No dependencies — creates the protocol
- **US2 (P1)**: Depends on US1 — tests runtime validation of the protocol
- **US3 (P2)**: Depends on US1 — tests extensibility of the protocol; can run in parallel with US2

### Parallel Opportunities

- T004 and T005 can run in parallel (different test scenarios, same file but independent sections)
- T006 and T007 can run in parallel (different tools, same source file)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: US1 — protocol definition
3. **STOP and VALIDATE**: Protocol importable and type-checkable
4. Commit

### Incremental Delivery

1. Setup → US1 → protocol exists (MVP)
2. US2 → runtime validation confirmed
3. US3 → extensibility confirmed
4. Polish → linting, type checking, quickstart validation

---

## Notes

- This is a very small feature (~30 lines of production code, ~80 lines of tests)
- The protocol file has zero external dependencies (stdlib `typing` only)
- US2 and US3 are primarily test-driven — the protocol definition in US1 inherently enables both
- Commit after each phase
