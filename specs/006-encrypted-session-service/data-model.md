# Data Model: Encrypted Session Service

**Feature Branch**: `006-encrypted-session-service`
**Date**: 2026-02-03

## Entity Overview

```
┌─────────────────┐     ┌─────────────────┐
│    AppState     │     │   UserState     │
│  (encrypted)    │     │  (encrypted)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    ┌──────────────────┘
         │    │
         ▼    ▼
┌─────────────────────────────────────────┐
│               Session                    │
│  (state encrypted, metadata plaintext)   │
└────────────────────┬────────────────────┘
                     │
                     │ 1:N
                     ▼
┌─────────────────────────────────────────┐
│                Event                     │
│   (event_data encrypted fully)           │
└─────────────────────────────────────────┘
```

## Entities

### Session

A container for agent state and conversation history.

| Field | Type | Storage | Description |
|-------|------|---------|-------------|
| id | str | plaintext | Unique identifier (UUID) |
| app_name | str | plaintext | Application name (queryable) |
| user_id | str | plaintext | User identifier (queryable) |
| state | dict[str, Any] | **encrypted** | Session state values |
| events | list[Event] | **encrypted** | Conversation events |
| last_update_time | float | plaintext | Timestamp (queryable) |

**Relationships**:
- Belongs to one AppState (via app_name)
- Belongs to one UserState (via app_name + user_id)
- Has many Events (1:N cascade delete)

**Validation**:
- id: Non-empty string, auto-generated if not provided
- app_name: Non-empty string
- user_id: Non-empty string
- state: JSON-serializable dictionary

### Event

A record of agent activity within a session.

| Field | Type | Storage | Description |
|-------|------|---------|-------------|
| id | str | plaintext (PK) | Unique identifier |
| session_id | str | plaintext (FK) | Parent session |
| app_name | str | plaintext (FK) | Application name |
| user_id | str | plaintext (FK) | User identifier |
| invocation_id | str | plaintext | Invocation grouping |
| timestamp | float | plaintext | Event time (queryable) |
| event_data | bytes | **encrypted** | Full serialized Event |

**Relationships**:
- Belongs to one Session (via app_name + user_id + session_id)

**Validation**:
- event_data: Must be valid encrypted envelope (version + backend_id + ciphertext)

### AppState

Application-level shared state.

| Field | Type | Storage | Description |
|-------|------|---------|-------------|
| app_name | str | plaintext (PK) | Application name |
| state | dict[str, Any] | **encrypted** | App-level state |
| update_time | float | plaintext | Last modified |

**Validation**:
- State keys are those with `app:` prefix (prefix stripped in storage)

### UserState

User-level shared state across sessions.

| Field | Type | Storage | Description |
|-------|------|---------|-------------|
| app_name | str | plaintext (PK) | Application name |
| user_id | str | plaintext (PK) | User identifier |
| state | dict[str, Any] | **encrypted** | User-level state |
| update_time | float | plaintext | Last modified |

**Validation**:
- State keys are those with `user:` prefix (prefix stripped in storage)

## State Transitions

### Session Lifecycle

```
         create_session()
               │
               ▼
         ┌──────────┐
         │ CREATED  │
         └────┬─────┘
              │
              │ append_event() / get_session()
              ▼
         ┌──────────┐
         │  ACTIVE  │◄────────────┐
         └────┬─────┘             │
              │                   │
              │ append_event()    │
              └───────────────────┘
              │
              │ delete_session()
              ▼
         ┌──────────┐
         │ DELETED  │
         └──────────┘
```

### State Delta Flow

```
Event.actions.state_delta
         │
         ├─── "app:*" ──────► AppState (merged, encrypted)
         │
         ├─── "user:*" ─────► UserState (merged, encrypted)
         │
         ├─── "temp:*" ─────► Discarded (not persisted)
         │
         └─── other ────────► Session.state (merged, encrypted)
```

## Encryption Envelope Format

All encrypted fields use the self-describing envelope format:

```
┌─────────┬────────────┬─────────────────────┐
│ Version │ Backend ID │     Ciphertext      │
│ (1 byte)│  (1 byte)  │   (variable len)    │
└─────────┴────────────┴─────────────────────┘
```

- **Version**: Currently `0x01` (ENVELOPE_VERSION_1)
- **Backend ID**: Currently `0x01` (BACKEND_FERNET)
- **Ciphertext**: Backend-specific encrypted payload

## Database Schema

```sql
-- App-level state
CREATE TABLE IF NOT EXISTS app_states (
    app_name TEXT PRIMARY KEY,
    state BLOB NOT NULL,
    update_time REAL NOT NULL
);

-- User-level state
CREATE TABLE IF NOT EXISTS user_states (
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    state BLOB NOT NULL,
    update_time REAL NOT NULL,
    PRIMARY KEY (app_name, user_id)
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    state BLOB NOT NULL,
    create_time REAL NOT NULL,
    update_time REAL NOT NULL,
    PRIMARY KEY (app_name, user_id, id)
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    id TEXT NOT NULL,
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    invocation_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    event_data BLOB NOT NULL,
    PRIMARY KEY (app_name, user_id, session_id, id),
    FOREIGN KEY (app_name, user_id, session_id)
        REFERENCES sessions(app_name, user_id, id) ON DELETE CASCADE
);

-- Index for efficient event queries by timestamp
CREATE INDEX IF NOT EXISTS idx_events_timestamp
    ON events(app_name, user_id, session_id, timestamp);
```

## Query Patterns

| Operation | Query Pattern |
|-----------|---------------|
| Get session | SELECT by (app_name, user_id, id) |
| List sessions | SELECT by (app_name) or (app_name, user_id) |
| Get recent events | SELECT by session + ORDER BY timestamp DESC LIMIT n |
| Get events after timestamp | SELECT by session + WHERE timestamp > ? |
| Delete session | DELETE by (app_name, user_id, id) → cascades to events |
