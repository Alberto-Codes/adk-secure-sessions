# ADR-004: ADK Interface Compatibility Strategy

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

We implement `BaseSessionService` directly (ADR-000), which means we own our own database schema. We do NOT need to track ADK's internal table structures (`StorageSession`, `StorageEvent`, schema V0/V1, etc.).

What we do need to track:

1. **`BaseSessionService` method signatures** — our superclass interface
2. **`Session` and `Event` model classes** — the data objects we serialize/deserialize
3. **`_session_util.extract_state_delta`** — the utility that splits state by prefix (`app:`, `user:`, unprefixed)
4. **`State.APP_PREFIX` / `State.USER_PREFIX` / `State.TEMP_PREFIX`** — the prefix constants

These are ADK's **public API surface** and change far less frequently than internal schemas.

## Decision

Adopt an **interface tracking + self-describing encrypted values** approach.

### Principles

1. **We own our schema.** We define our own database tables. Our schema is independent of ADK's `DatabaseSessionService` or `SqliteSessionService` schemas. We never need to run ADK's migration scripts.

> **Revision Note (2026-03-05):** "Own our schema" is more precisely characterized as "schema derived from ADK's data model contract with encrypted column types." Our tables (`app_states`, `user_states`, `sessions`, `events`) mirror ADK's public Session/Event data model — operationally independent (own tables, own migrations, own encryption) but structurally coupled to ADK's model contract. This applies to Phase 1-2. **ADR-007** changes the schema ownership model: ADK owns the base schema via `DatabaseSessionService`, and we own the `EncryptedJSON` TypeDecorator and encrypted model classes. See [ADR-007](ADR-007-architecture-migration.md) and Issue #118.

2. **We depend on `BaseSessionService`'s interface, not internals.** The four abstract methods and the `Session`/`Event` models are our contract. We pin to `google-adk>=1.22.0` because that's when the current `BaseSessionService` interface stabilized.

3. **Encrypted value format is self-describing.** Each encrypted blob includes a version prefix so we can decrypt data regardless of when or how it was encrypted:

   ```
   [version byte][backend id byte][ciphertext...]
   ```

   This allows us to rotate backends or upgrade encryption schemes without re-encrypting all existing data.

4. **Our own migration path.** If we change our schema (e.g., add columns, restructure tables), we provide our own migration utilities. These are independent of ADK's migration scripts.

### What We Track in ADK

| ADK Surface | Stability | How We Track |
|-------------|-----------|-------------|
| `BaseSessionService` method signatures | High (public ABC) | CI tests against min + latest ADK |
| `Session` / `Event` model fields | High (Pydantic models, public API) | Type checking + integration tests |
| `_session_util.extract_state_delta` | Medium (internal but stable utility) | Import and use directly |
| `State.APP_PREFIX`, `State.USER_PREFIX` | High (string constants) | Import and use directly |

### Testing Strategy

- **CI matrix**: Test against `google-adk>=1.22.0` (minimum) and `google-adk@latest`
- **Interface tests**: Assert that `BaseSessionService` still has the expected abstract methods
- **Round-trip tests**: Create session → encrypt → persist → read → decrypt → verify
- **Upgrade tests**: Encrypt with our v1 format, verify decryption still works after library updates

## Consequences

### What becomes easier

- **Independence from ADK internals**: ADK can refactor `DatabaseSessionService`, change their table structures, add schema V2/V3 — none of it affects us
- **Our own migration pace**: We change our schema when we need to, not when ADK forces us
- **Simpler codebase**: No `_compat.py` module sniffing ADK versions and branching on internal schema versions

### What becomes harder

- **ADK interface changes**: If `BaseSessionService` adds a new abstract method or changes a signature, we need to update. This is rare for a public ABC — it would be a breaking change for all session service implementations, not just ours.
- **Utility drift**: If `_session_util.extract_state_delta` changes behavior, our state splitting could diverge. Mitigated by integration tests.

### Trade-offs

- We replicate some logic that ADK's built-in services share (state prefix splitting, event timestamp handling). This is a small amount of code and gives us full control.
- The self-describing encrypted value prefix adds 2 bytes per encrypted field. Negligible.

## Alternatives Considered

### Track ADK's Internal Schema with `_compat.py`

**Rejected.** This was the original plan (version detection, column path mapping, schema snapshot tests). Since we implement `BaseSessionService` directly and own our schema, there's nothing internal to track. The `_compat.py` approach solved a problem that doesn't exist.

### Pin to a Single ADK Version

**Rejected.** Would force users to choose between our library and ADK updates. We pin a minimum and test against latest.

### Fork `_session_util`

**Rejected.** The state prefix splitting logic is simple but must stay in sync with ADK's prefix constants. Importing directly from ADK is better than maintaining a copy that could drift.
