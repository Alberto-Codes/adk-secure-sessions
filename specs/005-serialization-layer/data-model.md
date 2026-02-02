# Data Model: Serialization Layer

**Feature**: 005-serialization-layer
**Date**: 2026-02-02

## Entities

### Encrypted Envelope

A byte sequence with a fixed 2-byte header followed by backend-produced ciphertext.

```
Offset  Size    Field           Values
0       1 byte  version         0x01 = envelope format v1
1       1 byte  backend_id      0x01 = Fernet, 0x02 = AES-256-GCM (future)
2..N    N bytes ciphertext      Output from EncryptionBackend.encrypt()
```

**Validation rules**:
- Total length MUST be >= 3 bytes (2-byte header + at least 1 byte ciphertext).
- Version byte MUST be a recognized value (currently only `0x01`).
- Backend ID MUST be a recognized value.
- Unrecognized version or backend ID raises `DecryptionError`.

### Backend ID Registry

A lookup mapping integer backend IDs to human-readable names. Used for error messages only.

| ID     | Name       | Status  |
|--------|------------|---------|
| `0x01` | Fernet     | Active  |
| `0x02` | AES-256-GCM| Planned |

### SerializationError

New exception class inheriting from `SecureSessionError`. Raised when input data cannot be converted to JSON (e.g., non-serializable types).

**Relationships**:
- `SecureSessionError` (parent)
- Sibling to `EncryptionError` and `DecryptionError`
- Raised by `encrypt_session` and `encrypt_json` on JSON encoding failure

## Data Flow

```
encrypt_session(dict, backend, backend_id):
  dict → json.dumps() → bytes → backend.encrypt() → [version][backend_id][ciphertext]

decrypt_session(envelope, backend):
  [version][backend_id][ciphertext] → validate header → backend.decrypt() → bytes → json.loads() → dict

encrypt_json(str, backend, backend_id):
  str → .encode("utf-8") → backend.encrypt() → [version][backend_id][ciphertext]

decrypt_json(envelope, backend):
  [version][backend_id][ciphertext] → validate header → backend.decrypt() → bytes → .decode("utf-8") → str
```
