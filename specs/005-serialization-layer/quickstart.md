# Quickstart: Serialization Layer

## Encrypt a session state dict

```python
from adk_secure_sessions import FernetBackend
from adk_secure_sessions.serialization import (
    encrypt_session,
    decrypt_session,
    BACKEND_FERNET,
)

backend = FernetBackend("my-secret-passphrase")

# Encrypt
state = {"ssn": "123-45-6789", "name": "Alice"}
envelope = await encrypt_session(state, backend, BACKEND_FERNET)
# envelope is opaque bytes: b'\x01\x01<ciphertext...>'

# Decrypt
restored = await decrypt_session(envelope, backend)
assert restored == state
```

## Encrypt an ADK Event (pre-serialized JSON)

```python
from adk_secure_sessions.serialization import encrypt_json, decrypt_json

json_str = event.model_dump_json()
envelope = await encrypt_json(json_str, backend, BACKEND_FERNET)

# Later, on read:
restored_json = await decrypt_json(envelope, backend)
event = Event.model_validate_json(restored_json)
```

## Error handling

```python
from adk_secure_sessions.exceptions import (
    SerializationError,
    DecryptionError,
)

# Non-serializable data
try:
    await encrypt_session({"ts": datetime.now()}, backend, BACKEND_FERNET)
except SerializationError:
    print("Data contains non-JSON-serializable values")

# Tampered envelope
try:
    await decrypt_session(tampered_bytes, backend)
except DecryptionError:
    print("Envelope is corrupt or was encrypted with a different key")
```
