# ADR-006: ConfigurationError

> **Status**: Accepted
> **Date**: 2026-02-28
> **Deciders**: adk-secure-sessions maintainers

## Context

Story 1.3 introduces startup validation for `EncryptedSessionService`. Before this change, misconfigured services produced generic `TypeError`, `ValueError`, or `sqlite3.OperationalError` exceptions that gave no actionable guidance. Developers had to read stack traces to understand why their service failed to start.

ADR-005 established the "add when code demands" principle: add a subclass when a caller has a concrete need to handle a failure mode differently in a `try/except` block. Configuration errors at startup are precisely that scenario — callers want to catch misconfiguration and report it clearly (e.g., "check your encryption key" or "database path is invalid") without catching unrelated encryption or decryption failures.

Relevant requirements: FR15 (actionable error messages), FR25/NFR6 (error messages must never include key material).

## Decision

Add `ConfigurationError` as a direct subclass of `SecureSessionError`. This covers:

- Invalid encryption key (empty, wrong type) — raised by `FernetBackend.__init__`
- Invalid backend (does not conform to `EncryptionBackend` protocol) — raised by `EncryptedSessionService.__init__`
- Invalid backend_id (not an int) — raised by `EncryptedSessionService.__init__`
- Empty or non-string db_path — raised by `EncryptedSessionService.__init__`
- Database connection failures — raised by `EncryptedSessionService._init_db`, wrapping `OSError`/`sqlite3.OperationalError` with enriched messages

### Updated Hierarchy

```
SecureSessionError
├── EncryptionError
├── DecryptionError
├── SerializationError
└── ConfigurationError      # NEW — startup validation failures
```

### Error Message Safety

All `ConfigurationError` messages follow FR25/NFR6: they include type names and file paths but never encryption key values, plaintext, or ciphertext.

## Consequences

### What becomes easier

- **Startup debugging**: Developers see exactly what went wrong and how to fix it
- **Targeted error handling**: `except ConfigurationError` catches all misconfiguration without catching runtime encryption/decryption failures
- **DB path diagnostics**: Connection failures now include the path, OS error code, and a remediation hint

### What becomes harder

- Nothing meaningful — this is a single new leaf class with no impact on existing error handling patterns

## Alternatives Considered

### Separate DatabaseConnectionError

**Deferred to Phase 3.** Architecture Decision 2 reserves `DatabaseConnectionError` for when PostgreSQL support introduces additional connection failure modes. For now, database connection failures are wrapped in `ConfigurationError` since they occur exclusively during startup initialization.

### Keep using ValueError/TypeError

**Rejected.** Generic exceptions cannot be caught without also catching unrelated validation errors from other libraries. `ConfigurationError` gives callers a precise catch target.
