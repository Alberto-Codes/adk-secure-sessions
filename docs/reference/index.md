# API Reference

This reference documents all public APIs in adk-secure-sessions.

## Quick Navigation

### Core

- **[`EncryptionBackend`](adk_secure_sessions/protocols.md#adk_secure_sessions.protocols.EncryptionBackend)** — Protocol defining the encrypt/decrypt contract

### Backends

- **[`FernetBackend`](adk_secure_sessions/backends/fernet.md#adk_secure_sessions.backends.fernet.FernetBackend)** — Fernet symmetric encryption backend

### Exceptions

- **[`SecureSessionError`](adk_secure_sessions/exceptions.md#adk_secure_sessions.exceptions.SecureSessionError)** — Base exception for all library errors
- **[`EncryptionError`](adk_secure_sessions/exceptions.md#adk_secure_sessions.exceptions.EncryptionError)** — Raised when encryption fails
- **[`DecryptionError`](adk_secure_sessions/exceptions.md#adk_secure_sessions.exceptions.DecryptionError)** — Raised when decryption fails

---

## Module Organization

### Core Modules
- **[`adk_secure_sessions`](adk_secure_sessions/index.md)** — Package root, public exports
- **[`adk_secure_sessions.protocols`](adk_secure_sessions/protocols.md)** — `EncryptionBackend` protocol (PEP 544)
- **[`adk_secure_sessions.exceptions`](adk_secure_sessions/exceptions.md)** — Exception hierarchy

### Backend Modules
- **[`adk_secure_sessions.backends.fernet`](adk_secure_sessions/backends/fernet.md)** — Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)

---

## Common Use Cases

**Encrypt session data with Fernet:**
```python
from adk_secure_sessions import FernetBackend

backend = FernetBackend(key="my-secret-passphrase")
ciphertext = await backend.encrypt(b"sensitive data")
plaintext = await backend.decrypt(ciphertext)
```

**Custom encryption backend:**
```python
from adk_secure_sessions import EncryptionBackend

class MyBackend:
    async def encrypt(self, plaintext: bytes) -> bytes: ...
    async def decrypt(self, ciphertext: bytes) -> bytes: ...

assert isinstance(MyBackend(), EncryptionBackend)
```
