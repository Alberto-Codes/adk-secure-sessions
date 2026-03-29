# How-To: Write a Custom Encryption Backend

This guide walks you through implementing a custom encryption backend that
conforms to the `EncryptionBackend` protocol, registering it with the
service, and testing it for correctness.

## When to Write a Custom Backend

Write a custom backend when:

- You need to integrate with an external **Key Management Service** (AWS KMS,
  GCP Cloud KMS, HashiCorp Vault)
- Your deployment requires a **Hardware Security Module** (HSM) for key
  storage or encryption operations
- Compliance policy mandates a **specific cipher** not covered by the built-in
  Fernet or AES-256-GCM backends
- You want to wrap a **custom algorithm** or proprietary encryption library

If your need is simply to rotate keys or migrate between the built-in
backends, see [Key Rotation](key-rotation.md) instead.

## The Protocol Contract

All backends must satisfy the
[`EncryptionBackend`][adk_secure_sessions.protocols.EncryptionBackend]
protocol. The protocol has five members:

| Member | Kind | Signature | Purpose |
|--------|------|-----------|---------|
| `backend_id` | `@property` | `-> int` | Unique byte for envelope header dispatch |
| `sync_encrypt` | method | `(self, plaintext: bytes) -> bytes` | Sync encryption (TypeDecorator path) |
| `sync_decrypt` | method | `(self, ciphertext: bytes) -> bytes` | Sync decryption (TypeDecorator path) |
| `encrypt` | `async def` | `(self, plaintext: bytes) -> bytes` | Async encryption (application code) |
| `decrypt` | `async def` | `(self, ciphertext: bytes) -> bytes` | Async decryption (application code) |

**Why both sync and async?** The `EncryptedJSON` TypeDecorator runs in
SQLAlchemy's synchronous execution context (`process_bind_param` /
`process_result_value`). These call `sync_encrypt` / `sync_decrypt` directly.
The async methods exist for application-level usage and **must** delegate to
the sync methods via `asyncio.to_thread()` to avoid blocking the event loop.

**Structural subtyping (PEP 544):** Backends do **not** inherit from
`EncryptionBackend`. Any class with matching method signatures conforms
automatically. `isinstance(MyBackend(), EncryptionBackend)` returns `True` at
runtime, but `@runtime_checkable` only checks method **existence** — use a
static type checker (mypy, pyright) for full signature validation.

## Backend ID Assignment

Every backend needs a unique `backend_id` byte. The envelope header stores
this byte to dispatch decryption to the correct backend at read time.

### Reserved and Community Ranges

| Range | Owner | Examples |
|-------|-------|---------|
| `0x01` - `0x0F` | Official (adk-secure-sessions) | `0x01` Fernet, `0x02` AES-GCM |
| `0x10` - `0xFF` | Community / custom | Your backend starts here |

### Choosing Your ID

| Scenario | Recommended ID | Rationale |
|----------|---------------|-----------|
| Internal / single-project use | `0x10` | First community slot |
| Published PyPI package | `0x10` - `0x1F` | Coordinate with other packages to avoid collisions |
| Organization-wide standard | Pick one ID per org | Document in your internal standards |
| Multiple custom backends | Increment from `0x10` | `0x10`, `0x11`, `0x12`, ... |

The envelope uses the `backend_id` byte to look up which backend should
decrypt each record. If two backends share an ID, the service raises
`ConfigurationError` at init. Choose an ID and stick with it — changing it
later means existing encrypted data becomes unreadable without a migration.

## Walkthrough: AesGcmBackend

The [`AesGcmBackend`][adk_secure_sessions.backends.aes_gcm.AesGcmBackend] is
the simpler of the two official backends. Here are the key patterns to follow.

### The `backend_id` Property

```python
from adk_secure_sessions.serialization import BACKEND_AES_GCM

@property
def backend_id(self) -> int:
    return BACKEND_AES_GCM  # 0x02
```

Returns a constant integer. No computation, no side effects.
[Source: `backends/aes_gcm.py`][adk_secure_sessions.backends.aes_gcm.AesGcmBackend.backend_id]

### Sync Encrypt with Nonce Generation

```python
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_LENGTH = 12

def sync_encrypt(self, plaintext: bytes) -> bytes:
    nonce = os.urandom(_NONCE_LENGTH)  # fresh nonce every call
    ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext_and_tag
```

A fresh random nonce is generated per call. The output format is
`nonce || ciphertext + tag` — the backend decides its own wire format for the
ciphertext portion. The envelope layer wraps this with a version byte and
backend ID.
[Source: `backends/aes_gcm.py`][adk_secure_sessions.backends.aes_gcm.AesGcmBackend.sync_encrypt]

### Sync Decrypt with Error Wrapping

```python
from cryptography.exceptions import InvalidTag

from adk_secure_sessions.exceptions import DecryptionError

def sync_decrypt(self, ciphertext: bytes) -> bytes:
    nonce = ciphertext[:_NONCE_LENGTH]
    ct_and_tag = ciphertext[_NONCE_LENGTH:]
    try:
        return self._aesgcm.decrypt(nonce, ct_and_tag, None)
    except InvalidTag:
        msg = "Decryption failed: invalid tag or wrong key"
        raise DecryptionError(msg) from None
```

All cryptographic failures are caught and re-raised as `DecryptionError`.
The `from None` suppresses the original traceback to prevent leaking
internal details.
[Source: `backends/aes_gcm.py`][adk_secure_sessions.backends.aes_gcm.AesGcmBackend.sync_decrypt]

### Async Methods via `asyncio.to_thread()`

```python
import asyncio

async def encrypt(self, plaintext: bytes) -> bytes:
    return await asyncio.to_thread(self.sync_encrypt, plaintext)

async def decrypt(self, ciphertext: bytes) -> bytes:
    return await asyncio.to_thread(self.sync_decrypt, ciphertext)
```

Async methods delegate to the sync implementations via `asyncio.to_thread()`.
This offloads CPU-bound cryptographic operations to a thread pool so they
don't block the event loop.
[Source: `backends/aes_gcm.py`][adk_secure_sessions.backends.aes_gcm.AesGcmBackend.encrypt]

## Starter Template

Copy this skeleton and fill in your encryption logic:

```python
from __future__ import annotations

import asyncio

from adk_secure_sessions.exceptions import DecryptionError

BACKEND_MY_CRYPTO = 0x10  # community range start


class MyBackend:
    """Custom encryption backend conforming to EncryptionBackend.

    Replace the placeholder encrypt/decrypt logic with your
    actual cryptographic operations.
    """

    def __init__(self, key: bytes) -> None:
        # Validate and store key material.
        # Raise ConfigurationError for invalid keys.
        self._key = key

    @property
    def backend_id(self) -> int:
        return BACKEND_MY_CRYPTO

    def sync_encrypt(self, plaintext: bytes) -> bytes:
        # 1. Generate a fresh nonce/IV (if your cipher requires one).
        # 2. Encrypt plaintext using self._key.
        # 3. Return nonce + ciphertext (or whatever format your cipher uses).
        raise NotImplementedError

    def sync_decrypt(self, ciphertext: bytes) -> bytes:
        # 1. Split nonce/IV from ciphertext.
        # 2. Decrypt using self._key.
        # 3. On failure: raise DecryptionError("decryption failed") from None
        #    NEVER include key material in the error message.
        try:
            raise NotImplementedError
        except Exception:
            msg = "Decryption failed"
            raise DecryptionError(msg) from None

    async def encrypt(self, plaintext: bytes) -> bytes:
        return await asyncio.to_thread(self.sync_encrypt, plaintext)

    async def decrypt(self, ciphertext: bytes) -> bytes:
        return await asyncio.to_thread(self.sync_decrypt, ciphertext)
```

After implementing the encrypt/decrypt logic, verify protocol conformance:

```python
from adk_secure_sessions.protocols import EncryptionBackend

backend = MyBackend(key=b"your-key-here")
assert isinstance(backend, EncryptionBackend)
```

## Registering Your Backend

### Current Approach

To use your backend with `EncryptedSessionService`, two steps are required:

**Step 1:** Add your backend ID to `BACKEND_REGISTRY` in
[`serialization.py`][adk_secure_sessions.serialization]:

```python
# In src/adk_secure_sessions/serialization.py
BACKEND_REGISTRY: dict[int, str] = {
    BACKEND_FERNET: "Fernet",       # 0x01
    BACKEND_AES_GCM: "AES-GCM",    # 0x02
    0x10: "MyBackend",              # add your backend
}
```

Without this entry, `_parse_envelope()` rejects envelopes with your
`backend_id` as unrecognized.

**Step 2:** Pass your backend to the service:

```python
from adk_secure_sessions import EncryptedSessionService

service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=MyBackend(key=my_key),
)
```

For multi-backend setups (e.g., migrating from Fernet to your custom
backend), use `additional_backends`:

```python
from adk_secure_sessions import EncryptedSessionService, FernetBackend

service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=MyBackend(key=my_key),               # new writes
    additional_backends=[FernetBackend("old-pw")],  # legacy reads
)
```

!!! note "Registration will change"
    The manual `BACKEND_REGISTRY` edit described here is the current process.
    A future release will introduce entry-point discovery (see [Roadmap](../ROADMAP.md)),
    allowing backends to register automatically via their package metadata.

## Testing Checklist

Use these seven checks to verify your backend is correct. Each item
references a test in the existing suite as a pattern to follow.

| # | Test | Pattern Source | Notes |
|---|------|---------------|-------|
| 1 | `isinstance(MyBackend(...), EncryptionBackend)` is `True` | `test_protocols.py` | Protocol conformance |
| 2 | `encrypt(b"hello")` then `decrypt()` returns `b"hello"` | `test_fernet_backend.py` | Round-trip correctness |
| 3 | `encrypt(b"")` then `decrypt()` returns `b""` | `test_fernet_backend.py` | Empty bytes edge case |
| 4 | `decrypt(wrong_key_ciphertext)` raises `DecryptionError` | `test_aes_gcm_backend.py` | Wrong-key rejection |
| 5 | 100x `encrypt(same_plaintext)` produces 100 unique ciphertexts | `test_aes_gcm_backend.py` | Nonce uniqueness (nonce-based backends only) |
| 6 | Cross-backend: decrypt with wrong backend raises `DecryptionError` | `test_aes_gcm_backend.py` | Cross-backend confusion |
| 7 | Error messages don't contain key material | Pattern from codebase | NFR6 safety |

!!! tip "Nonce uniqueness (test #5)"
    Test #5 applies to nonce-based backends (AES-GCM, ChaCha20). KMS backends
    with server-side encryption may produce deterministic ciphertext for the
    same plaintext and key — skip this test if your backend is deterministic
    by design.

See [`test_aes_gcm_backend.py`](https://github.com/Alberto-Codes/adk-secure-sessions/tree/main/tests/unit/test_aes_gcm_backend.py)
for the canonical test reference implementation.

## Common Pitfalls

### 1. Nonce Reuse (Catastrophic for AEAD)

If your cipher is nonce-based (AES-GCM, ChaCha20-Poly1305), reusing a nonce
with the same key allows key recovery. **Generate a fresh random nonce per
`sync_encrypt` call** using `os.urandom()`.

- ✅ `nonce = os.urandom(12)` inside `sync_encrypt`
- ⚠️ Counter-based nonces in a multi-process environment (risk of collision)

### 2. Blocking the Event Loop

All `cryptography` library calls are CPU-bound. Async methods **must**
delegate via `asyncio.to_thread()`:

```python
async def encrypt(self, plaintext: bytes) -> bytes:
    return await asyncio.to_thread(self.sync_encrypt, plaintext)
```

- ✅ `await asyncio.to_thread(self.sync_encrypt, plaintext)`
- ⚠️ `return self.sync_encrypt(plaintext)` in an async method (blocks the loop)

### 3. Key Material in Exception Messages

Error messages must **never** contain passphrases, key bytes, or plaintext.
Use generic messages and suppress the original traceback:

```python
except SomeCryptoError:
    msg = "Decryption failed"
    raise DecryptionError(msg) from None
```

- ✅ `raise DecryptionError("Decryption failed") from None`
- ⚠️ `raise DecryptionError(f"Failed with key={self._key!r}")`

### 4. Forgetting Sync Methods

If `sync_encrypt` or `sync_decrypt` are missing, the `EncryptedJSON`
TypeDecorator path fails at runtime. The `@runtime_checkable` protocol
check catches this at service initialization — but only if you pass
the backend to `EncryptedSessionService`. Always implement all five
protocol members.

### 5. Mutable State in Backends

Backend instances may be shared across coroutines. Avoid mutable instance
state unless protected by a lock. Prefer stateless operations where
the only instance state is the immutable key material set at init.

- ✅ Immutable key stored at `__init__`, stateless encrypt/decrypt
- ⚠️ `self._counter += 1` without a lock (race condition)

### 6. Adding Envelope Framing

The backend's `encrypt` / `decrypt` handle **raw ciphertext only**. The
envelope (`version_byte + backend_id + ciphertext`) is managed by the
[serialization layer][adk_secure_sessions.serialization]. Do **not** add
your own envelope framing — the serialization layer wraps your output
automatically.

- ✅ Return raw `nonce + ciphertext` from `sync_encrypt`
- ⚠️ Return `bytes([0x01, 0x10]) + nonce + ciphertext` (double framing)

## Security Notes

- **Key material safety**: Never log, print, or include key bytes in
  exception messages. Store keys in environment variables or a secrets
  manager, not in source code.
- **Nonce requirements**: For AEAD ciphers, use `os.urandom()` for nonce
  generation. Never use a predictable or reused nonce.
- **`DecryptionError` wrapping**: Always catch library-specific exceptions
  and re-raise as
  [`DecryptionError`][adk_secure_sessions.exceptions.DecryptionError]. Use
  `from None` to suppress the original traceback and prevent leaking
  internal details.
- **Input validation**: Validate key length and type in `__init__`. Raise
  [`ConfigurationError`][adk_secure_sessions.exceptions.ConfigurationError]
  for invalid keys — fail fast at construction, not at first encrypt call.

## Related

- [ADR-001: Protocol-Based Interfaces](../adr/ADR-001-protocol-based-interfaces.md) —
  why PEP 544 Protocols instead of ABC inheritance
- [ADR-002: Async-First Design](../adr/ADR-002-async-first.md) —
  `asyncio.to_thread()` requirement and sync/async boundary
- [Envelope Protocol](../envelope-protocol.md) —
  binary wire format specification
- [`AesGcmBackend` API Reference][adk_secure_sessions.backends.aes_gcm.AesGcmBackend] —
  full auto-generated documentation
- [Key Rotation](key-rotation.md) —
  rotating keys and migrating between backends
- [Roadmap](../ROADMAP.md) —
  entry-point discovery for automatic backend registration
