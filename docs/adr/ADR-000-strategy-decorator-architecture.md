# ADR-000: Strategy + Direct Implementation Architecture

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

adk-secure-sessions is a **library** that adds encryption to Google ADK's session storage. The architecture must:

1. Be transparent — users should interact with ADK's session interface, not ours
2. Support pluggable encryption backends (Fernet, and later KMS providers)
3. Stay focused — this is not an application with complex domain logic
4. Be easy to extend without modifying existing code

We investigated ADK's session internals to determine the right integration approach.

## Decision

Adopt **Strategy + Direct Implementation** as the core architectural pattern.

### Direct Implementation of `BaseSessionService` (Integration)

The `EncryptedSessionService` **directly implements** ADK's `BaseSessionService` ABC. It owns its own database connection, schema, and serialization — with encryption at the serialization boundary.

This is the same approach used by every community session service (`adk-extra-services` MongoDB/Redis, `google-adk-extras`, etc.). Nobody wraps `DatabaseSessionService`; they all implement `BaseSessionService` from scratch.

```
User Code
    │
    ▼
EncryptedSessionService  (implements BaseSessionService)
    │ json.dumps → encrypt → write
    │ read → decrypt → json.loads
    ▼
SQLite (aiosqlite) / PostgreSQL
```

We model our implementation on ADK's own `SqliteSessionService`, which uses `aiosqlite` + JSON serialization. Our version is structurally identical but adds an encrypt/decrypt step around the JSON serialization boundary.

#### Why not wrap `DatabaseSessionService` (Decorator pattern)?

We initially planned a decorator approach. Reading the actual ADK source revealed this doesn't work:

1. **`append_event` has no interception point.** It reads state from the DB, merges deltas via `json_patch` SQL operations, writes the event, and commits — all in one internal transaction. There's no clean boundary to inject encryption.

2. **State is split across 3 tables** (`app_states`, `user_states`, `sessions`). A decorator would need to understand this internal split to encrypt/decrypt correctly, coupling us to ADK internals.

3. **No community precedent.** Every third-party session service (`adk-extra-services`, `google-adk-redis`) subclasses `BaseSessionService` directly. Nobody wraps the built-in services.

> **Revision Note (2026-03-05):** The rejection reasoning above was correct for ADK V0. ADK V1 changed state merging from SQL-side `json_patch` operations to Python-side `dict | delta`, removing the interception barrier described in point 1. `DatabaseSessionService` wrapping is now viable via `TypeDecorator`-based column encryption. **ADR-007** formalizes the decision to migrate to this architecture — see [ADR-007](ADR-007-architecture-migration.md) and Issue #118. This ADR's "Direct Implementation" approach is superseded by ADR-007; the "Strategy" portion (pluggable backends) remains valid.

### Strategy Pattern (Extensibility)

Encryption backends are interchangeable strategies. Each implements the `EncryptionBackend` protocol (see ADR-001). The session service delegates all encrypt/decrypt operations to the configured backend.

```
EncryptedSessionService
    │
    ├── FernetBackend        (symmetric, simple — v1)
    └── CustomBackend        (user-provided, implement 2 methods)
```

### Project Structure

```
src/adk_secure_sessions/
├── __init__.py                  # Public API surface
├── protocols.py                 # EncryptionBackend protocol
├── exceptions.py                # Exception hierarchy
├── services/
│   ├── __init__.py
│   └── encrypted_session.py     # Implements BaseSessionService
├── backends/
│   ├── __init__.py
│   └── fernet.py                # Fernet symmetric encryption (v1)
└── serialization.py             # Encrypt/decrypt at JSON boundary
```

### Layer Rules

1. **`services/`** depends on `protocols.py` (the contract), never on concrete backends
2. **`backends/`** implements `protocols.py` — each backend is self-contained
3. **`protocols.py`** has zero dependencies (stdlib `typing` only)
4. **`serialization.py`** handles the encrypt-on-write / decrypt-on-read boundary around `json.dumps` / `json.loads`

### What We Inherit from `BaseSessionService`

ADK's `BaseSessionService` provides two concrete helper methods we reuse:

- `_trim_temp_delta_state(event)` — removes temporary state keys before persistence
- `_update_session_state(session, event)` — applies state deltas to in-memory session

We implement the four abstract methods and `append_event`:

- `create_session()` — serialize state → encrypt → write to DB
- `get_session()` — read from DB → decrypt → deserialize state
- `list_sessions()` — read metadata (unencrypted) + decrypt state per session
- `delete_session()` — delete rows
- `append_event()` — encrypt state delta + event data → write, then call `super().append_event()` for in-memory update

## Consequences

### What becomes easier

- **Adding backends**: New backend = one file, implement 2 methods, done
- **Testing**: Mock the protocol for unit tests, use real backends for integration
- **Adoption**: Same interface as ADK's built-in services — one-line swap
- **Maintenance**: We own our schema, no fragile coupling to ADK internals

### What becomes harder

- **Feature parity**: We reimplement session storage rather than delegating. If ADK adds new session service features (e.g., new query filters), we need to add them too.
- **State splitting logic**: We must replicate ADK's `app_state` / `user_state` / `session_state` prefix-based splitting (via `_session_util.extract_state_delta`). This is a public utility in ADK, so it's stable.

### Trade-offs

- More code than a decorator, but it actually works. A decorator that can't intercept `append_event` is useless.
- We depend on `BaseSessionService`'s interface stability, not internal implementation details. This is the correct dependency direction for a plugin.

## Alternatives Considered

### Decorator Wrapping `DatabaseSessionService`

**Rejected.** Investigated in detail — `append_event` does state reads, delta merges, event writes, and commits in a single internal transaction with no interception points. State split across 3 tables requires knowledge of internals. No community implementations use this approach.

### Hexagonal Architecture (Ports & Adapters)

**Rejected.** Hexagonal is designed for applications with rich domain logic and multiple I/O boundaries. adk-secure-sessions has one job (encrypt/decrypt session data) and one boundary (ADK's session service interface). Three layers of indirection would add ceremony without value.

### Simple Inheritance of `DatabaseSessionService`

**Rejected.** Subclassing `DatabaseSessionService` couples us to its internal SQLAlchemy schema, `_SchemaClasses` version logic, and `StorageSession` / `StorageEvent` models. When ADK refactors internals (as they did in v1.22.0 with the V0→V1 schema migration), our subclass breaks. (See [ADR-007](ADR-007-architecture-migration.md) for how TypeDecorator-based subclassing differs from this rejected approach — it intercepts at the ORM column boundary rather than overriding CRUD methods.)

### Middleware/Pipeline Pattern

**Considered for future.** If we need composable transformations (encrypt → compress → sign), a middleware chain would fit. For now, single-backend encryption doesn't warrant the complexity.
