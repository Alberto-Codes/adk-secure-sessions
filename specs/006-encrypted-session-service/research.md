# Research: Encrypted Session Service

**Feature Branch**: `006-encrypted-session-service`
**Date**: 2026-02-03

## ADK BaseSessionService Interface

### Decision: Implement BaseSessionService directly
**Rationale**: The constitution (Principle IV) mandates implementing BaseSessionService directly rather than wrapping/decorating ADK's built-in services. This ensures drop-in compatibility and clean separation from ADK internals.
**Alternatives considered**: Decorating DatabaseSessionService (rejected: constitution prohibits wrappers).

### Required Abstract Methods

From `google.adk.sessions.base_session_service`:

```python
@abstractmethod
async def create_session(
    self,
    *,
    app_name: str,
    user_id: str,
    state: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Session:
    """Creates a new session."""

@abstractmethod
async def get_session(
    self,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
    config: Optional[GetSessionConfig] = None,
) -> Optional[Session]:
    """Gets a session."""

@abstractmethod
async def list_sessions(
    self, *, app_name: str, user_id: Optional[str] = None
) -> ListSessionsResponse:
    """Lists all sessions for a user (or all users if user_id is None)."""

@abstractmethod
async def delete_session(
    self, *, app_name: str, user_id: str, session_id: str
) -> None:
    """Deletes a session."""
```

### Non-Abstract Methods (inherited)

```python
async def append_event(self, session: Session, event: Event) -> Event:
    """Appends an event to a session object."""
    # Default implementation calls _trim_temp_delta_state and _update_session_state
    # We MUST override to add database persistence with encryption

def _trim_temp_delta_state(self, event: Event) -> Event:
    """Removes temporary state delta keys from the event."""
    # Inherited, no override needed

def _update_session_state(self, session: Session, event: Event) -> None:
    """Updates the session state based on the event."""
    # Inherited, no override needed
```

### Supporting Types

```python
from google.adk.sessions.base_session_service import GetSessionConfig, ListSessionsResponse

class GetSessionConfig(BaseModel):
    num_recent_events: Optional[int] = None
    after_timestamp: Optional[float] = None

class ListSessionsResponse(BaseModel):
    sessions: list[Session] = Field(default_factory=list)
```

## Session and Event Models

### Decision: Use ADK's Session and Event models directly
**Rationale**: Constitution Principle IV limits dependencies to ADK's public API surface. Session and Event are public models we MUST use.
**Alternatives considered**: Creating wrapper models (rejected: would break drop-in compatibility).

### Session Model

```python
from google.adk.sessions.session import Session

class Session(BaseModel):
    id: str                              # Unique identifier
    app_name: str                        # Application name
    user_id: str                         # User identifier
    state: dict[str, Any]                # Session state (ENCRYPT THIS)
    events: list[Event]                  # Events (ENCRYPT EACH)
    last_update_time: float = 0.0        # Timestamp
```

### Event Model

```python
from google.adk.events.event import Event

class Event(LlmResponse):
    id: str                              # Unique identifier
    invocation_id: str                   # Invocation identifier
    author: str                          # 'user' or agent name
    actions: EventActions                # Contains state_delta (ENCRYPT)
    timestamp: float                     # Event timestamp
    # ... other fields from LlmResponse
```

### EventActions Model

```python
class EventActions(BaseModel):
    state_delta: dict[str, object]       # State changes (ENCRYPT)
    artifact_delta: dict[str, int]       # Artifact changes
    # ... other action fields
```

## State Management

### Decision: Use ADK's state utilities for delta extraction
**Rationale**: Issue #6 specifies reusing `extract_state_delta` and `State.APP_PREFIX`/`USER_PREFIX`.
**Alternatives considered**: Custom extraction (rejected: duplicates ADK logic).

### State Prefixes

```python
from google.adk.sessions.state import State

State.APP_PREFIX = "app:"    # App-level state keys
State.USER_PREFIX = "user:"  # User-level state keys
State.TEMP_PREFIX = "temp:"  # Temporary keys (not persisted)
```

### State Delta Extraction

```python
from google.adk.sessions._session_util import extract_state_delta

# Returns {"app": {...}, "user": {...}, "session": {...}}
deltas = extract_state_delta(state_dict)
```

## Database Schema

### Decision: Own database schema separate from ADK
**Rationale**: Constitution Principle IV mandates owning our own schema, independent of ADK's internal tables.
**Alternatives considered**: Extending ADK's schema (rejected: would couple to internal implementation).

### Schema Design

```sql
-- App-level state (encrypted)
CREATE TABLE app_states (
    app_name TEXT PRIMARY KEY,
    state BLOB NOT NULL,           -- Encrypted envelope
    update_time REAL NOT NULL
);

-- User-level state (encrypted)
CREATE TABLE user_states (
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    state BLOB NOT NULL,           -- Encrypted envelope
    update_time REAL NOT NULL,
    PRIMARY KEY (app_name, user_id)
);

-- Sessions (encrypted state)
CREATE TABLE sessions (
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    state BLOB NOT NULL,           -- Encrypted envelope
    create_time REAL NOT NULL,
    update_time REAL NOT NULL,
    PRIMARY KEY (app_name, user_id, id)
);

-- Events (encrypted data)
CREATE TABLE events (
    id TEXT NOT NULL,
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    invocation_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    event_data BLOB NOT NULL,      -- Encrypted envelope
    PRIMARY KEY (app_name, user_id, session_id, id),
    FOREIGN KEY (app_name, user_id, session_id)
        REFERENCES sessions(app_name, user_id, id) ON DELETE CASCADE
);
```

**Note**: Metadata columns (app_name, user_id, session_id, timestamps) remain plaintext for queryability per Constitution Principle III.

## Encryption Boundary

### Decision: Encrypt at JSON serialization boundary
**Rationale**: Issue #6 specifies encrypting at the JSON serialization boundary (ADR-003 pattern).
**Alternatives considered**: Field-level encryption (rejected: more complex, same security).

### Encryption Flow

1. **Write path**: `dict` → `json.dumps()` → `encrypt_session()` → `envelope bytes` → database BLOB
2. **Read path**: database BLOB → `decrypt_session()` → `dict`

### What Gets Encrypted

| Data | Encrypted? | Reason |
|------|------------|--------|
| session.state | YES | Contains sensitive user data |
| event.event_data (full JSON) | YES | Contains conversation history |
| app_name, user_id, session_id | NO | Needed for querying |
| timestamps | NO | Needed for ordering/filtering |

## Error Handling

### Decision: Use existing exception hierarchy
**Rationale**: Issue #6 depends on #4 (exception hierarchy). Use SecureSessionError subclasses.
**Alternatives considered**: ADK AlreadyExistsError (use for duplicate session_id only).

### Exception Mapping

| Scenario | Exception |
|----------|-----------|
| Duplicate session_id | `google.adk.errors.AlreadyExistsError` |
| Encryption failure | `EncryptionError` |
| Decryption failure | `DecryptionError` |
| JSON serialization failure | `SerializationError` |
| Database errors | Pass through (don't wrap) |

## Connection Lifecycle

### Decision: Implement async context manager with explicit close()
**Rationale**: FR-010 and FR-011 require this for resource cleanup.

### Pattern

```python
async def close(self) -> None:
    """Close the database connection."""
    if self._connection:
        await self._connection.close()

async def __aenter__(self) -> EncryptedSessionService:
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
    await self.close()
```

## Dependencies Summary

| Dependency | Version | Purpose |
|------------|---------|---------|
| google-adk | >=1.0.0 | BaseSessionService, Session, Event |
| aiosqlite | >=0.19.0 | Async SQLite operations |
| adk-secure-sessions (internal) | - | EncryptionBackend, serialization, exceptions |
