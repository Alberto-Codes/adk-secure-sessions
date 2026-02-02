# Data Model: FernetBackend

**Feature**: 003-fernet-backend
**Date**: 2026-02-01

## Entities

### FernetBackend

An encryption backend that implements the `EncryptionBackend` protocol using Fernet symmetric encryption.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `_fernet` | `Fernet` | Internal Fernet instance initialized with derived/direct key |

**Initialization Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | `str \| bytes` | Yes | Encryption key — either a valid Fernet key or arbitrary passphrase |

**Methods**:

| Method | Signature | Description |
|--------|-----------|-------------|
| `encrypt` | `async (plaintext: bytes) -> bytes` | Encrypts plaintext bytes, returns Fernet token |
| `decrypt` | `async (ciphertext: bytes) -> bytes` | Decrypts Fernet token, returns plaintext bytes |

**State Transitions**: None — stateless after initialization.

**Validation Rules**:
- `key` must not be empty (raises `ValueError`)
- `key` as `str` is encoded to bytes before processing
- Valid Fernet key format (44 base64url chars / 32 bytes) used directly
- All other keys derived via PBKDF2-HMAC-SHA256

### SecureSessionError

Base exception for all library errors.

| Attribute | Type | Description |
|-----------|------|-------------|
| (standard Exception attributes) | — | Inherits from `Exception` |

### DecryptionError

Raised when decryption fails.

| Attribute | Type | Description |
|-----------|------|-------------|
| (standard Exception attributes) | — | Inherits from `SecureSessionError` |

**Trigger conditions**: Wrong key, tampered ciphertext, malformed ciphertext, truncated data.

## Relationships

```text
EncryptionBackend (Protocol)
    ↑ structurally conforms
FernetBackend
    → raises DecryptionError (on decrypt failure)
    → DecryptionError inherits SecureSessionError
```
