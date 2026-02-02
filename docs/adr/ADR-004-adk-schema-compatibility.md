# ADR-004: ADK Schema Compatibility Strategy

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

Google ADK's database schema for session storage is not stable. Notable changes:

- **v1.22.0**: Major schema change — new JSON-based format, migration scripts provided, `SqliteSessionService` introduced alongside `DatabaseSessionService`
- **Ongoing**: ADK is pre-1.0 (currently v1.23.0) and schema changes are expected to continue

Our library wraps ADK's session services. When ADK changes its schema, we need to:

1. Continue working with the new schema
2. Handle encrypted data written under the old schema
3. Not break existing users' encrypted databases

## Decision

Adopt a **version detection + compatibility layer** approach rather than maintaining our own schema.

### Principles

1. **We do not own the schema.** ADK defines the database tables. We encrypt/decrypt values flowing through them. We never create tables, alter columns, or run DDL.

2. **Version detection at startup.** The `_compat` module detects which ADK version is installed and which session service class is being wrapped, then selects the correct serialization paths.

3. **Encrypted value format is self-describing.** Each encrypted value includes a version prefix so we can decrypt data regardless of when it was encrypted:

   ```
   [version byte][backend id byte][ciphertext...]
   ```

   This allows us to rotate backends or upgrade encryption schemes without re-encrypting existing data.

4. **Minimum supported ADK version.** We declare a minimum (`google-adk>=1.22.0`) and test against it and the latest release. We do not support versions before the v1.22.0 schema change.

5. **Migration utilities, not automatic migration.** If an ADK upgrade changes the schema, we provide a migration script/command that re-encrypts data into the new format. We never silently migrate on startup — that's dangerous for production databases.

### Compatibility Module

```python
# _compat.py — the only module that touches ADK internals

def detect_adk_version() -> tuple[int, int, int]:
    """Detect installed ADK version."""
    ...

def get_state_column_path(adk_version: tuple[int, int, int]) -> str:
    """Return the column/JSON path where state is stored."""
    ...

def get_events_column_path(adk_version: tuple[int, int, int]) -> str:
    """Return the column/JSON path where events are stored."""
    ...
```

### Testing Strategy

- **CI matrix**: Test against `google-adk>=1.22.0` (minimum) and `google-adk@latest`
- **Schema snapshot tests**: Capture ADK's table definitions at each supported version, assert our encryption/decryption works against each
- **Upgrade tests**: Encrypt with version N, upgrade ADK to N+1, verify decryption still works

## Consequences

### What becomes easier

- **ADK upgrades**: Users can upgrade ADK independently; our compatibility layer adapts
- **Debugging**: Version detection logs which ADK version and schema path is in use
- **Data longevity**: Self-describing encrypted values survive backend changes

### What becomes harder

- **New ADK releases**: Each ADK release needs compatibility testing. If they change the schema, we need to update `_compat.py` and potentially add a migration script.
- **Testing surface**: CI matrix grows with each supported ADK version

### Trade-offs

- We're coupled to ADK's release cadence for compatibility updates. This is inherent to being a plugin — the alternative is forking ADK's session service entirely, which would be worse.
- The version prefix on encrypted values adds 2 bytes per field. Negligible.

## Alternatives Considered

### Fork ADK's Session Service

**Rejected.** Maintaining our own copy of `DatabaseSessionService` with encryption baked in would give full control but create massive maintenance burden. Every ADK update would require manual merging. The decorator approach (ADR-000) avoids this.

### Pin to a Single ADK Version

**Rejected.** Would force users to choose between our library and ADK updates. Unacceptable for a library that targets production use.

### Automatic Migration on Startup

**Rejected.** Silent data migration in production is dangerous. A migration that fails partway through could leave the database in an inconsistent state with some rows encrypted under the old format and some under the new. Explicit migration commands are safer and auditable.
