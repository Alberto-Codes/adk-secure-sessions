# How-To: Key Rotation

Key rotation replaces the encryption key (or passphrase) protecting your
session data. This guide covers both rotation paths and their trade-offs.

## When to Rotate Keys

Key rotation is required when:

- A passphrase is compromised or suspected of exposure
- Compliance policy mandates periodic key rotation (e.g., every 90 days)
- Migrating from one encryption algorithm to another (e.g., Fernet → AES-GCM)

## Two Rotation Paths

The right path depends on whether your old and new backends have **different
`backend_id` values**.

| Scenario | Old `backend_id` | New `backend_id` | Path |
|----------|-----------------|-----------------|------|
| Fernet → AES-GCM (algorithm migration) | `0x01` | `0x02` | **Path A** (lazy) |
| Fernet passphrase rotation | `0x01` | `0x01` | **Path B** (batch) |
| AES-GCM key rotation | `0x02` | `0x02` | **Path B** (batch) |

---

## Path A: Lazy Cross-Backend Migration (Zero Code Changes)

**Use this when**: migrating from one backend *type* to another (e.g., Fernet
to AES-GCM). The two backends have different `backend_id` values, so the
`additional_backends` mechanism can dispatch transparently.

No data migration utility is required. Configure the service with the new
backend as primary and the old backend as an additional (read-only) backend:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions import (
    AesGcmBackend,
    EncryptedSessionService,
    FernetBackend,
)

old_fernet = FernetBackend("old-passphrase")
new_aes_gcm = AesGcmBackend(key=AESGCM.generate_key(bit_length=256))

service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=new_aes_gcm,           # new writes use AES-GCM (0x02)
    additional_backends=[old_fernet],  # legacy Fernet sessions remain readable
)
```

**How it works**: The envelope header in each encrypted record carries a
`backend_id` byte. When reading, the service dispatches to the backend
registered for that ID. New writes use `new_aes_gcm` (ID `0x02`); old records
with ID `0x01` are decrypted transparently by `old_fernet`.

**Trade-offs**:

- ✅ Zero downtime — no migration script required
- ✅ No maintenance window needed
- ✅ Old data remains readable during migration
- ⚠️ Old encrypted records accumulate indefinitely; they are only migrated
  when the owning session is written again via normal application activity
- ⚠️ Storage contains a mix of backends until all old records are overwritten

---

## Path B: Batch Same-Backend Rotation

**Use this when**: rotating a passphrase within the *same* backend type (e.g.,
changing the Fernet passphrase). Because both old and new backends share the
same `backend_id`, `additional_backends` cannot be used — the duplicate ID
check raises `ConfigurationError` at service init.

Use `rotate_encryption_keys()` to re-encrypt all records in a single migration
pass:

```python
from adk_secure_sessions import FernetBackend
from adk_secure_sessions.rotation import RotationResult, rotate_encryption_keys

old = FernetBackend("old-passphrase")
new = FernetBackend("new-passphrase")

result: RotationResult = await rotate_encryption_keys(
    db_url="sqlite+aiosqlite:///sessions.db",
    old_backend=old,
    new_backend=new,
)

print(f"Rotated: {result.rotated} records")
print(f"Skipped: {result.skipped} records (concurrent writes — run again)")
```

After rotation completes, reconfigure the service to use only the new backend:

```python
service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=new,  # old_backend no longer needed
)
```

**How it works**: `rotate_encryption_keys()` opens its own database connection,
reads all encrypted records from the four session tables (`sessions`,
`app_states`, `user_states`, `events`), and for each record whose envelope
header matches `old_backend.backend_id`:

1. Decrypts with `old_backend.sync_decrypt`
2. Re-encrypts with `new_backend.sync_encrypt`
3. Writes back with an optimistic concurrency check (see below)

Cryptographic calls run in `asyncio.to_thread()` to avoid blocking the event
loop.

### Optimistic Concurrency

If a session is updated by the application between the rotation function's
read and write, the `UPDATE` check (which guards on both `update_time` and
the existing ciphertext value) detects the conflict — zero rows affected.
That record is counted as **skipped**, not overwritten.

For **same-backend rotation** (the primary use case — two `FernetBackend`
instances with different keys), skipped records can be picked up by running
`rotate_encryption_keys()` again **before** stopping the old-backend service.
However, once the rotation function has completed a full pass, do **not**
re-run with the original `old_backend`: it cannot decrypt the already-rotated
ciphertext and will raise `DecryptionError`. Re-runs are only safe for
cross-backend rotation where backend IDs differ.

```python
# Recommended: pause writes (or run during low-traffic window)
# then run once; skipped count should be 0 or very low
result = await rotate_encryption_keys(db_url, old, new)
if result.skipped > 0:
    # Re-run ONLY if service is still using old_backend for reads —
    # do not re-run after reconfiguring the service to new_backend
    result2 = await rotate_encryption_keys(db_url, old, new)
    print(f"Second pass: rotated={result2.rotated}, skipped={result2.skipped}")
```

**Trade-offs**:

- ✅ Complete one-time migration — no mixed-backend storage after rotation
- ✅ Safe concurrent operation — skipped records never lose data
- ⚠️ Not idempotent for same-backend rotation — run once, then reconfigure
  the service; do not re-run with the original `old_backend` after rotation
- ⚠️ Requires a database connection at rotation time (not just the service)
- ⚠️ May require a brief maintenance window for large databases to minimise
  skipped record counts; or run with the service paused

---

## AES-GCM Key Rotation (Path B variant)

Rotating an AES-GCM key uses the same batch approach:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions import AesGcmBackend
from adk_secure_sessions.rotation import rotate_encryption_keys

old_key = AESGCM.generate_key(bit_length=256)
new_key = AESGCM.generate_key(bit_length=256)

old = AesGcmBackend(key=old_key)
new = AesGcmBackend(key=new_key)

result = await rotate_encryption_keys(
    db_url="sqlite+aiosqlite:///sessions.db",
    old_backend=old,
    new_backend=new,
)
```

---

## Security Notes

- Key material (passphrases, raw key bytes) never appears in log output or
  exception messages from `rotate_encryption_keys()`.
- The old key is not retained anywhere after the function returns — it is the
  caller's responsibility to securely delete or revoke the old key/passphrase.
- During **cross-backend rotation** (Path A), the database contains a mix of
  old-backend and new-backend records. The service can read both via
  `additional_backends` — no downtime required.
- During **same-backend rotation** (Path B), the database contains a mix of
  old-key and new-key records with identical `backend_id`. The running service
  cannot distinguish them. **Stop the service (or pause writes) before running
  `rotate_encryption_keys()`, then reconfigure and restart with `new_backend`.**

---

## Related

- [ADR-009: Key Rotation Strategy](../adr/ADR-009-key-rotation-strategy.md) —
  architecture decisions behind both paths
- [`rotate_encryption_keys` API reference][adk_secure_sessions.rotation] —
  full parameter and return type documentation
- [ADR-008: Per-Key Random Salt](../adr/ADR-008-per-key-random-salt.md) —
  explains why Fernet passphrase rotation is meaningful (each ciphertext uses
  a unique salt)
