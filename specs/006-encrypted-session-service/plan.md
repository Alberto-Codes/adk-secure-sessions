# Implementation Plan: Encrypted Session Service

**Branch**: `006-encrypted-session-service` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-encrypted-session-service/spec.md`

## Summary

Implement `EncryptedSessionService` as a drop-in replacement for ADK's `DatabaseSessionService`. The service implements `BaseSessionService` directly (per Constitution Principle IV) with transparent field-level encryption for session state and event data at the JSON serialization boundary. Uses the existing serialization layer (`encrypt_session`/`decrypt_session`) and exception hierarchy.

## Technical Context

**Language/Version**: Python 3.12 (per `requires-python` in pyproject.toml)
**Primary Dependencies**: google-adk (BaseSessionService, Session, Event), aiosqlite, cryptography
**Storage**: SQLite via aiosqlite (async), own schema independent of ADK
**Testing**: pytest + pytest-asyncio + pytest-mock
**Target Platform**: Linux/macOS/Windows (cross-platform Python)
**Project Type**: Single project (Python library)
**Performance Goals**: Standard web app expectations (sub-second session operations)
**Constraints**: Must maintain ADK interface compatibility, async-only API
**Scale/Scope**: Single-user to multi-tenant (SQLite file per deployment)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Protocol-Based Interfaces | ✅ PASS | Uses existing `EncryptionBackend` protocol; no new protocols needed |
| II. Async-First | ✅ PASS | All methods are `async def`; uses `aiosqlite` for database |
| III. Field-Level Encryption | ✅ PASS | Encrypts state/events; metadata (app_name, user_id, timestamps) plaintext |
| IV. ADK Interface Compatibility | ✅ PASS | Implements `BaseSessionService` directly; owns independent schema |
| V. Minimal Exception Surface | ✅ PASS | Uses existing exceptions; ADK's `AlreadyExistsError` for duplicates |
| VI. Simplicity & YAGNI | ✅ PASS | Minimal implementation; no premature abstractions |

**Security Constraints Check**:
- ✅ Keys not in logs/exceptions (uses existing exception hierarchy)
- ✅ Self-describing envelope format (uses existing serialization layer)
- ✅ Authenticated encryption via Fernet (AES-128-CBC + HMAC-SHA256)

## Project Structure

### Documentation (this feature)

```text
specs/006-encrypted-session-service/
├── plan.md              # This file
├── research.md          # ADK interface research
├── data-model.md        # Entity definitions and schema
├── quickstart.md        # Usage examples
├── contracts/           # API contract definitions
│   └── encrypted_session_service.py
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/adk_secure_sessions/
├── __init__.py              # Public API exports (add EncryptedSessionService)
├── protocols.py             # EncryptionBackend protocol (existing)
├── exceptions.py            # Exception hierarchy (existing)
├── serialization.py         # Serialization layer (existing)
├── backends/
│   └── fernet.py            # FernetBackend (existing)
└── services/
    ├── __init__.py          # Export EncryptedSessionService
    └── encrypted_session.py # EncryptedSessionService implementation (NEW)

tests/unit/
├── test_protocols.py        # Protocol tests (existing)
├── test_exceptions.py       # Exception tests (existing)
├── test_fernet_backend.py   # Fernet tests (existing)
├── test_serialization.py    # Serialization tests (existing)
└── test_encrypted_session_service.py  # Session service tests (NEW)

tests/integration/
└── test_adk_integration.py  # ADK agent integration tests (NEW)
```

**Structure Decision**: Single project structure. New code goes in `src/adk_secure_sessions/services/` subdirectory to organize service classes separately from protocols and exceptions. This follows the existing pattern of `backends/` subdirectory.

## Implementation Approach

### Phase 1: Core Service Class

1. Create `src/adk_secure_sessions/services/__init__.py` and `encrypted_session.py`
2. Implement `EncryptedSessionService` class:
   - Constructor accepting `db_path`, `backend`, `backend_id`
   - Database initialization (create tables if not exist)
   - Async context manager (`__aenter__`, `__aexit__`, `close`)

### Phase 2: CRUD Operations

3. Implement `create_session`:
   - Generate UUID if session_id not provided
   - Encrypt state using `encrypt_session`
   - Insert into sessions table
   - Handle `AlreadyExistsError` for duplicate IDs

4. Implement `get_session`:
   - Query session by (app_name, user_id, session_id)
   - Decrypt state using `decrypt_session`
   - Query and decrypt events based on config
   - Merge app/user state into session state

5. Implement `list_sessions`:
   - Query sessions by (app_name) or (app_name, user_id)
   - Decrypt each session's state
   - Return `ListSessionsResponse`

6. Implement `delete_session`:
   - Delete from sessions table (cascade to events)

### Phase 3: Event Handling

7. Override `append_event`:
   - Skip persistence for partial events
   - Call base class methods for state trimming/updating
   - Encrypt event data using `encrypt_json`
   - Extract and apply state deltas (app/user/session)
   - Insert into events table

### Phase 4: State Management

8. Implement state delta handling:
   - Use `extract_state_delta` from ADK
   - Update app_states table (app: prefixed keys)
   - Update user_states table (user: prefixed keys)
   - Update session state (remaining keys)

### Phase 5: Testing

9. Unit tests for all operations
10. Integration tests with mock ADK agent
11. Edge case tests (wrong key, corrupted data, concurrent access)

## Complexity Tracking

No constitution violations to track. Implementation is straightforward:
- Uses existing encryption infrastructure
- Follows ADK's SqliteSessionService as reference
- No new abstractions or patterns introduced

## Artifacts Generated

| Artifact | Path | Status |
|----------|------|--------|
| Research | `research.md` | ✅ Complete |
| Data Model | `data-model.md` | ✅ Complete |
| Contract | `contracts/encrypted_session_service.py` | ✅ Complete |
| Quickstart | `quickstart.md` | ✅ Complete |
| Tasks | `tasks.md` | ⏳ Pending (`/speckit.tasks`) |
