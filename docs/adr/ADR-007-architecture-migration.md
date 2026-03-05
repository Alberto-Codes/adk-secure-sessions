# ADR-007: Architecture Migration — DatabaseSessionService Wrapping

> **Status**: Accepted
> **Date**: 2026-03-05
> **Deciders**: adk-secure-sessions maintainers

## Context

ADR-000 established a **Strategy + Direct Implementation** architecture: `EncryptedSessionService` directly implements ADK's `BaseSessionService`, owning its own database connection, schema, and serialization via raw aiosqlite SQL.

ADR-000 explicitly rejected wrapping `DatabaseSessionService` for three reasons:

1. `append_event` used SQL-side `json_patch` operations with no interception point for encryption
2. State split across 3 tables required knowledge of ADK internals
3. No community precedent for wrapping built-in services

**These objections were correct for ADK V0.** However, ADK V1 (>=1.22.0) fundamentally changed the state merging mechanism: `_merge_state()` now uses Python-side `dict | delta` operations instead of SQL-side `json_patch`. This removes the interception barrier described in objection #1 — the TypeDecorator pattern can transparently encrypt/decrypt at the ORM boundary before state reaches the database.

Issue #118 (documentation honesty audit) identified that our ~800-line raw aiosqlite implementation reimplements persistence logic that ADK already provides, creating a feature parity burden and limiting us to SQLite. This prompted Epic 7 to explore wrapping `DatabaseSessionService` as an alternative.

Story 7.1 (TypeDecorator Wrapping Spike) validated the approach with a working prototype: 8/8 tests passed, conformance verified, and all assessment criteria met. The spike findings document contains the full evidence base.

This ADR supersedes the **"Direct Implementation"** portion of ADR-000. The **"Strategy"** portion (pluggable encryption backends via `EncryptionBackend` protocol) remains fully valid and unchanged.

## Decision

Migrate from direct `BaseSessionService` implementation to **wrapping `DatabaseSessionService`** via a custom SQLAlchemy `TypeDecorator`.

### Architecture

```
User Code
    |
    v
EncryptedDatabaseSessionService  (subclasses DatabaseSessionService)
    |  overrides: _get_schema_classes(), _prepare_tables()
    |
    v
DatabaseSessionService  (ADK's implementation)
    |  all CRUD: create_session, get_session, list_sessions,
    |            delete_session, append_event
    |  state merging: _merge_state() (Python-side dict | delta)
    |
    v
SQLAlchemy ORM
    |  EncryptedJSON TypeDecorator on state/event_data columns
    |  process_bind_param: dict -> JSON -> encrypt -> base64 -> TEXT
    |  process_result_value: TEXT -> base64 -> decrypt -> JSON -> dict
    |
    v
SQLite / PostgreSQL / MySQL / MariaDB
```

### Key Design Decisions

1. **`EncryptedJSON` TypeDecorator** replaces ADK's `DynamicJSON` on all `state` and `event_data` columns. It encrypts on write (`process_bind_param`) and decrypts on read (`process_result_value`), making encryption transparent to `DatabaseSessionService`.

2. **Override `_get_schema_classes()`** to return custom model classes with `EncryptedJSON` instead of `DynamicJSON`. This is a clean internal override point — the method is called before every DB operation.

3. **Override `_prepare_tables()`** to use our `DeclarativeBase.metadata` for table creation, ensuring the encrypted models are used.

4. **Sync Fernet in TypeDecorator** — `process_bind_param` and `process_result_value` call `Fernet.encrypt()`/`decrypt()` synchronously. This is safe because SQLAlchemy's `AsyncSession` runs ORM operations in a thread pool via `run_sync()`.

5. **Envelope preservation** — each encrypted value uses the existing `[version_byte][backend_id_byte][ciphertext]` binary format, enabling future key rotation and backend migration.

6. **Base64 encoding** — encrypted bytes are base64-encoded for TEXT column compatibility across all SQL dialects. This adds ~33% storage overhead but is acceptable for session state (typically small).

### What We Keep

| Component | Reason |
|-----------|--------|
| `FernetBackend` class | Key resolution (passphrase to Fernet key) |
| `EncryptionBackend` protocol | Public API contract for pluggable backends (ADR-001) |
| Envelope format constants | Used by TypeDecorator for envelope construction |
| Exception hierarchy | `DecryptionError`, `ConfigurationError` still needed |
| `serialization.py` | Envelope format logic reused by TypeDecorator |

### What We Replace

| Component | Disposition |
|-----------|-------------|
| `EncryptedSessionService` (current) | Replaced by `EncryptedDatabaseSessionService` |
| Raw aiosqlite DB access | Replaced by SQLAlchemy ORM (via ADK) |
| Custom schema management | Replaced by ADK's schema + our TypeDecorator |
| Manual encrypt/decrypt in CRUD methods | Replaced by automatic TypeDecorator |

## Consequences

### What becomes easier

- **Multi-database support** — SQLite, PostgreSQL, MySQL, and MariaDB work via `DatabaseSessionService`'s dialect handling. No additional code needed.
- **Connection pooling** — SQLAlchemy's connection pool is inherited automatically.
- **Row-level locking** — database-native locking via SQLAlchemy, replacing our manual concurrency handling.
- **Schema migration** — SQLAlchemy + Alembic can manage schema changes. No custom migration utilities needed.
- **Maintenance** — ~800 lines of raw SQL replaced by a thin wrapper focused solely on encryption, the project's actual value-add.
- **Feature parity** — new `DatabaseSessionService` features (query filters, pagination) are inherited automatically.

### What becomes harder

- **Coupled to `DatabaseSessionService` internals** — we depend on `_get_schema_classes()` and `_prepare_tables()`, which are internal methods (underscore-prefixed). While stable across ADK v1.x, they could change in future major versions. Mitigated by sentinel tests that detect signature changes.
- **Schema ownership shift** — we no longer "own our schema" in the ADR-004 sense. ADK owns the base schema; we own the TypeDecorator and encrypted model classes. This is a narrower but more focused ownership.
- **Error surface change** — wrong-key decryption in TypeDecorator raises `cryptography.fernet.InvalidToken`, which SQLAlchemy wraps in `StatementError`. The wrapper must catch and re-raise as `DecryptionError` to preserve the library's error contract.

### Trade-offs

- **Base64 overhead** — 33% storage increase per encrypted field. Acceptable for session state, which is typically small (< 10KB). If problematic, switching to `LargeBinary` column type eliminates the overhead.
- **Internal method dependency** — `_get_schema_classes` and `_prepare_tables` are not public API. The risk is mitigated by: (a) ADK version pinning (`>=1.22.0`), (b) sentinel tests in CI that fail immediately on signature changes, (c) these methods are stable across v1.x.
- **Model class isolation** — custom encrypted models use a separate `DeclarativeBase`. Both ADK's models and ours must never share the same engine to avoid table name conflicts.
- **Migration path** — existing databases (raw aiosqlite, BLOB columns) are incompatible with the new architecture (SQLAlchemy, TEXT columns). Fresh databases required. Acceptable because we have no existing users with production data (confirmed in Epic 6 retrospective).

## Alternatives Considered

### Keep Current Direct Implementation (ADR-000 Architecture)

**Rejected.** The current `EncryptedSessionService` works but carries significant costs:

- ~800 lines of raw SQL reimplementing persistence logic that ADK provides
- Feature parity burden — every new `DatabaseSessionService` feature must be manually replicated
- SQLite-only — no path to PostgreSQL, MySQL, or MariaDB without writing additional persistence backends (Epic 4 Stories 4.1-4.3)
- The raw aiosqlite approach was correct when wrapping wasn't viable (ADK V0), but ADK V1's change to Python-side state merging eliminates the technical barrier

### Full ORM Rewrite (Custom SQLAlchemy Models Without Wrapping)

**Rejected.** Building a standalone SQLAlchemy-based session service from scratch would gain multi-database support but would still reimplement all CRUD logic. Wrapping `DatabaseSessionService` gets multi-database support, connection pooling, and all CRUD logic for free while focusing our code on encryption — the sole value-add.

### Middleware/Pipeline Pattern

**Deferred.** A middleware chain (encrypt -> compress -> sign) would fit if we need composable transformations. For now, single-backend encryption via TypeDecorator is simpler and sufficient. Can be revisited when multiple transformation steps are needed.

## Evidence

- **Spike findings**: `_bmad-output/implementation-artifacts/7-1-spike-findings.md` — GO decision with 8/8 tests passing, conformance verified, all assessment criteria met
- **Issue #118**: Documentation honesty audit that identified the architecture evolution opportunity
- **ADR-000 Revision Note (2026-03-04)**: Acknowledged ADK V1 changed the calculus for wrapping viability
