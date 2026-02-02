# Quickstart: EncryptionBackend Protocol

## Implementing a Custom Backend

```python
class MyBackend:
    """A custom encryption backend — no imports needed."""

    async def encrypt(self, plaintext: bytes) -> bytes:
        # Your encryption logic here
        return encrypted_data

    async def decrypt(self, ciphertext: bytes) -> bytes:
        # Your decryption logic here
        return decrypted_data
```

That's it. No base class, no registration, no imports from
`adk-secure-sessions`.

## Verifying Conformance

```python
from adk_secure_sessions.protocols import EncryptionBackend

backend = MyBackend()
assert isinstance(backend, EncryptionBackend)  # True
```

## Using with the Session Service

```python
from adk_secure_sessions import EncryptedSessionService

service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///./sessions.db",
    backend=MyBackend(),
)
```

## Known Limitations

- `isinstance()` checks verify method existence only — not parameter
  types, return types, or async status. Use a static type checker
  (mypy, pyright) for full validation.
- A class with synchronous `encrypt`/`decrypt` will pass the
  `isinstance()` check but fail at call time in an async context.
