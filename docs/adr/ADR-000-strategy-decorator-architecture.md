# ADR-000: Strategy + Decorator Architecture

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

adk-secure-sessions is a **library** that adds encryption to Google ADK's session storage. The architecture must:

1. Be transparent — users should interact with ADK's session interface, not ours
2. Support pluggable encryption backends (Fernet, SQLCipher, KMS providers)
3. Stay focused — this is not an application with complex domain logic
4. Be easy to extend without modifying existing code

We considered several architectural patterns used in the Python ecosystem for libraries with similar requirements.

## Decision

Adopt **Strategy + Decorator** as the core architectural pattern, composed of two well-understood GoF patterns:

### Decorator Pattern (Transparency)

The `EncryptedSessionService` **wraps** ADK's session services (`DatabaseSessionService`, `SqliteSessionService`). It implements the same interface and delegates all operations to the wrapped service, intercepting reads and writes to encrypt/decrypt state values.

```
User Code
    │
    ▼
EncryptedSessionService  (Decorator)
    │ encrypt on write
    │ decrypt on read
    ▼
DatabaseSessionService   (ADK's original)
    │
    ▼
SQLite / PostgreSQL / etc.
```

Users swap one line to get encryption:

```python
# Before
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///./sessions.db")

# After
session_service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///./sessions.db",
    encryption_key="your-key",
)
```

### Strategy Pattern (Extensibility)

Encryption backends are interchangeable strategies. Each implements the `EncryptionBackend` protocol (see ADR-001). The session service delegates all encrypt/decrypt operations to the configured backend.

```
EncryptedSessionService
    │
    ├── FernetBackend        (symmetric, simple)
    ├── SQLCipherBackend     (full-database, transparent)
    ├── AWSKMSBackend        (managed keys, compliance)
    └── CustomBackend        (user-provided)
```

### Project Structure

```
src/adk_secure_sessions/
├── __init__.py                  # Public API surface
├── protocols.py                 # EncryptionBackend protocol
├── exceptions.py                # Exception hierarchy
├── services/
│   ├── __init__.py
│   └── encrypted_session.py     # Decorator — wraps ADK session services
├── backends/
│   ├── __init__.py
│   ├── fernet.py                # Fernet symmetric encryption
│   ├── sqlcipher.py             # Full-database SQLCipher
│   └── kms.py                   # AWS/GCP KMS (future)
├── serialization.py             # Encrypt/decrypt serialization layer
└── _compat.py                   # ADK version detection + schema compat
```

### Layer Rules

1. **`services/`** depends on `protocols.py` (the contract), never on concrete backends
2. **`backends/`** implements `protocols.py` — each backend is self-contained
3. **`protocols.py`** has zero dependencies (stdlib `typing` only)
4. **`_compat.py`** is the only module that inspects ADK internals for version/schema detection

## Consequences

### What becomes easier

- **Adding backends**: New backend = one file, implement 2 methods, done
- **Testing**: Mock the protocol for unit tests, use real backends for integration
- **Adoption**: One-line change for existing ADK users
- **Maintenance**: Flat structure, no layer gymnastics

### What becomes harder

- **Cross-cutting concerns**: If we later need middleware chains (logging, metrics, retry around encryption), the flat structure doesn't have a natural place. We'd add a simple middleware list if needed.

### Trade-offs

- No domain layer — encryption is a behavior, not a business domain. We don't model "encrypted sessions" as entities; we intercept and transform data in transit.
- No port/adapter separation — the protocol *is* the port, and backends *are* the adapters. The vocabulary is simpler without the hexagonal ceremony.

## Alternatives Considered

### Hexagonal Architecture (Ports & Adapters)

**Rejected.** Hexagonal is designed for applications with rich domain logic and multiple I/O boundaries. adk-secure-sessions has one job (encrypt/decrypt session data) and one boundary (ADK's session service interface). Three layers of indirection would add ceremony without value.

### Simple Inheritance

**Rejected.** Subclassing ADK's `DatabaseSessionService` directly would couple us to their internal implementation. When ADK refactors (as they did in v1.22.0), our subclass breaks. The decorator pattern wraps the public interface, insulating us from internal changes.

### Middleware/Pipeline Pattern

**Considered for future.** If we need composable transformations (encrypt → compress → sign), a middleware chain would fit. For now, single-backend encryption doesn't warrant the complexity. The architecture allows adding this later without breaking changes.
