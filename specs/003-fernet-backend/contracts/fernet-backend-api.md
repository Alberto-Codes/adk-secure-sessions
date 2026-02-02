# API Contract: FernetBackend

**Feature**: 003-fernet-backend
**Date**: 2026-02-01

## Module: `adk_secure_sessions.backends.fernet`

### Class: `FernetBackend`

Structurally conforms to `EncryptionBackend` protocol.

#### Constructor

```python
FernetBackend(key: str | bytes)
```

**Parameters**:
- `key` — Encryption key. Accepts:
  - A valid 44-character base64url-encoded Fernet key (used directly)
  - An arbitrary string or bytes passphrase (derived via PBKDF2-HMAC-SHA256)

**Raises**:
- `ValueError` — If `key` is empty

#### Method: `encrypt`

```python
async def encrypt(self, plaintext: bytes) -> bytes
```

**Parameters**:
- `plaintext` — Raw bytes to encrypt (may be empty)

**Returns**: Fernet token as bytes

**Raises**:
- `TypeError` — If `plaintext` is not `bytes`

#### Method: `decrypt`

```python
async def decrypt(self, ciphertext: bytes) -> bytes
```

**Parameters**:
- `ciphertext` — Fernet token bytes to decrypt

**Returns**: Original plaintext bytes

**Raises**:
- `DecryptionError` — If decryption fails (wrong key, tampered/malformed data)

---

## Module: `adk_secure_sessions.exceptions`

### Class: `SecureSessionError(Exception)`

Base exception for all library errors.

### Class: `DecryptionError(SecureSessionError)`

Raised when decryption fails. Error messages must not contain key material, ciphertext, or plaintext.

---

## Public API Exports (`adk_secure_sessions.__init__`)

```python
from adk_secure_sessions import EncryptionBackend   # existing
from adk_secure_sessions import FernetBackend        # new
from adk_secure_sessions import SecureSessionError   # new
from adk_secure_sessions import DecryptionError      # new
```
