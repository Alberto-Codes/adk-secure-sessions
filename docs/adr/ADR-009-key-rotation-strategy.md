# ADR-009: Key Rotation Strategy

> **Status**: Accepted
> **Date**: 2026-03-11
> **Deciders**: adk-secure-sessions maintainers

## Context

Story 3.3 party-mode consensus (2026-03-07) asked Story 4.4 to evaluate whether
extracting an `EncryptionCoordinator` class is needed for key rotation. The
coordinator was deferred from the original architecture design as a potential
abstraction over multi-backend dispatch, key provider selection, and migration
strategy.

### Background: Two Distinct Rotation Scenarios

Key rotation in production presents two fundamentally different use cases:

**Path A — Cross-backend lazy rotation** (e.g., Fernet to AES-GCM):
Already works today via `additional_backends`. Old sessions encrypted with
`backend_id=0x01` are read transparently while new sessions are written with
`backend_id=0x02`. No migration utility is required. Old data accumulates
indefinitely with the old backend.

**Path B — Same-backend passphrase rotation** (e.g., two `FernetBackend`
instances with different passphrases):
Cannot use `additional_backends` because both backends share `backend_id=0x01`.
The duplicate backend ID check in `EncryptedSessionService.__init__` raises
`ConfigurationError`. Requires a migration function that reads with the old
key and writes with the new key.

### Concurrency Constraint (NFR27)

The `sessions` table has an `update_time` column maintained by ADK's
`DatabaseSessionService` (via SQLAlchemy `onupdate=func.now()`). This column
is a natural optimistic concurrency guard: if a session is modified between
the rotation function's read and write, the `UPDATE WHERE update_time =
<read_value>` will affect zero rows, signalling a concurrent write. The record
is skipped rather than overwritten with stale re-encrypted data.

A `version` column was reserved in Story 1.2 but was never added to the Epic 7
wrapper models. Adding it would require overriding ADK's CRUD write methods
(`create_session`, `append_event`) to increment the counter — a violation of
the ADK-is-upstream convention (ADR-004). The `update_time` column is
functionally equivalent and requires no ADK method overrides.

### Coordinator Evaluation

Multi-backend dispatch is already fully implemented via `EncryptedJSON`'s
`decrypt_dispatch` dictionary (mapping `backend_id → sync_decrypt callable`),
populated at service init time from `additional_backends`. Key rotation adds
"re-encrypt all records" — a migration task, not a dispatch task. A coordinator
class would conflate dispatch (a read-time concern) with migration (a one-time
operational concern), creating an unnecessary coupling.

## Decision

### No EncryptionCoordinator Class

A standalone `rotate_encryption_keys()` async function in a dedicated
`rotation.py` module is the right abstraction. Rationale:

1. **Single responsibility** — the function has exactly one job: re-encrypt all
   records from one backend key to another. This is a batch migration, not a
   runtime dispatch concern.
2. **Minimal surface** — a class would add a public symbol with no protocol
   boundary, giving callers nothing they need beyond what the function provides.
3. **No coordinator protocol needed** — the `EncryptionBackend` protocol already
   captures the backend contract. Adding a coordinator protocol for a single
   operation is premature generalization.
4. **Dispatch already solved** — `EncryptedJSON.decrypt_dispatch` handles
   runtime cross-backend dispatch. Key rotation bypasses the TypeDecorator
   entirely and operates on raw TEXT column values.

### Two-Path Rotation Strategy

#### Path A: Lazy Cross-Backend Migration (Zero Code Changes)

Configure `EncryptedSessionService` with `additional_backends`:

```python
old_fernet = FernetBackend("old-passphrase")
new_aes_gcm = AesGcmBackend(key=AESGCM.generate_key(bit_length=256))
service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=new_aes_gcm,
    additional_backends=[old_fernet],
)
```

- New writes use `new_aes_gcm` (backend_id=0x02)
- Old sessions (backend_id=0x01) are read transparently via dispatch
- No data migration required; old ciphertext accumulates

**Trade-offs**: No forced migration of old data; mixed-backend storage persists
indefinitely until records are overwritten by normal application activity.

#### Path B: Batch Same-Backend Rotation

Call `rotate_encryption_keys(db_url, old_backend, new_backend)`:

```python
old_fernet = FernetBackend("old-passphrase")
new_fernet = FernetBackend("new-passphrase")
result = await rotate_encryption_keys(
    db_url="sqlite+aiosqlite:///sessions.db",
    old_backend=old_fernet,
    new_backend=new_fernet,
)
# result.rotated: count of re-encrypted records
# result.skipped: count skipped due to concurrent writes
```

The function:
1. Opens an async engine from `db_url`
2. For each of the 4 encrypted tables (`sessions`, `app_states`, `user_states`,
   `events`): reads all rows, identifies records matching `old_backend.backend_id`
   by parsing the envelope header from the base64-decoded TEXT column
3. For each matching row: decrypts with `old_backend.sync_decrypt`, re-encrypts
   with `new_backend.sync_encrypt`, builds a new envelope, and writes back with
   an optimistic concurrency check on `update_time`
4. Crypto calls are wrapped in `asyncio.to_thread()` (CPU-bound rule, ADR-002)
5. Returns `RotationResult(rotated=N, skipped=M)`

**Trade-offs**: Complete migration in a single operation, but may require a
maintenance window for large databases. Concurrent writes during rotation are
handled gracefully (skipped records can be rotated in a follow-up call).

### `update_time` as Optimistic Concurrency Guard

The rotation function reads a row's `update_time`, re-encrypts the state, and
executes:

```sql
UPDATE sessions
SET state = :new_encrypted_state
WHERE app_name = :app_name
  AND user_id = :user_id
  AND id = :id
  AND update_time = :read_update_time
```

If `rows_affected == 0`, a concurrent write occurred between read and write.
The record is added to the `skipped` count. This is intentional: skipping
preserves the most recent write and avoids data loss. Operators can run
`rotate_encryption_keys` again to pick up skipped records.

### Key Safety (NFR6)

No key material, passphrases, or derived key bytes may appear in any error
message or log output from the rotation function. Record identifiers (row
primary keys) are safe metadata and may appear in logs.

## Alternatives Considered

### EncryptionCoordinator Class

**Rejected.** A class would create a public symbol with no protocol boundary,
conflating runtime dispatch (already solved by `EncryptedJSON`) with batch
migration. The single-responsibility `rotate_encryption_keys()` function is
simpler, more discoverable, and covers all required use cases.

### `version` Column for Optimistic Concurrency

**Rejected.** Adding a `version` column to the encrypted models would require
overriding ADK's CRUD write methods to increment the counter, violating the
ADK-is-upstream principle (ADR-004). The `update_time` column provides
equivalent protection with no override required.

### Lazy-Only Strategy (No Batch Migration)

**Rejected.** Same-backend passphrase rotation is a legitimate compliance
requirement (FR48). Lazy rotation via `additional_backends` cannot address this
scenario because duplicate `backend_id` values are rejected at service init.

### Envelope Header Extension for Old/New Key Tracking

**Rejected.** Adding key identity to the envelope header would break the binary
wire protocol (ADR-000) and require all consumers to be updated simultaneously.
The rotation function's approach — detect by backend_id byte in existing envelope
— is backward-compatible and requires no protocol changes.

## Consequences

### Positive

- `rotate_encryption_keys()` provides a complete, production-safe batch
  migration path for same-backend passphrase rotation
- Path A (lazy cross-backend) remains zero-change for operators migrating
  between backend types
- Optimistic concurrency prevents data loss during concurrent writes
- No key material in error messages (NFR6 compliance)
- No ADK method overrides required

### Negative

- Batch rotation requires an async database connection at call time; the caller
  owns the database URL, not just the service instance
- `update_time` is not incremented by the rotation function itself (it reads
  and conditionally updates in a single `UPDATE` statement); SQLAlchemy
  `onupdate` triggers only on ORM-level writes, not raw SQL
- Skipped records require a follow-up rotation call; there is no automatic retry

### Neutral

- The rotation function operates outside the `EncryptedJSON` TypeDecorator —
  it reads raw TEXT column values and manually parses envelopes. This is
  intentional: the rotation function must control which key is used for
  decryption, bypassing the TypeDecorator's configured dispatch.
- `_build_envelope` and `_parse_envelope` from `serialization.py` are reused
  directly in `rotation.py`

## References

- [ADR-000](ADR-000-strategy-decorator-architecture.md): Envelope wire protocol
- [ADR-002](ADR-002-async-first.md): Async-first design, `asyncio.to_thread()` rule
- [ADR-004](ADR-004-adk-schema-compatibility.md): ADK-is-upstream principle
- [ADR-007](ADR-007-architecture-migration.md): `update_time` column source and TypeDecorator architecture
- [ADR-008](ADR-008-per-key-random-salt.md): Per-key salt in FernetBackend (relevant to same-backend rotation)
- `src/adk_secure_sessions/services/encrypted_session.py`: `additional_backends` dispatch implementation
- Story 3.3 party-mode consensus (2026-03-07): coordinator evaluation trigger
