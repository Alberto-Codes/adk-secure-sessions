# API Reference

This reference documents all public APIs in adk-secure-sessions.

## Quick Navigation

### Core

- **[`EncryptionBackend`](adk_secure_sessions/protocols.md#adk_secure_sessions.protocols.EncryptionBackend)** — Protocol defining the encrypt/decrypt contract

---

## Module Organization

### Core Modules
- **[`adk_secure_sessions`](adk_secure_sessions/index.md)** — Package root, public exports
- **[`adk_secure_sessions.protocols`](adk_secure_sessions/protocols.md)** — `EncryptionBackend` protocol (PEP 544)

---

## Common Use Cases

**Custom encryption backend:**
```python
from adk_secure_sessions import EncryptionBackend

class MyBackend:
    async def encrypt(self, plaintext: bytes) -> bytes: ...
    async def decrypt(self, ciphertext: bytes) -> bytes: ...

assert isinstance(MyBackend(), EncryptionBackend)
```
