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

## Using with a Session Service

```python
from adk_secure_sessions.protocols import EncryptionBackend


class SessionService:
    """Example of how a session service could depend on EncryptionBackend."""

    def __init__(self, backend: EncryptionBackend) -> None:
        self._backend = backend

    async def create_session(self, data: bytes) -> bytes:
        return await self._backend.encrypt(data)

    async def read_session(self, token: bytes) -> bytes:
        return await self._backend.decrypt(token)


service = SessionService(backend=MyBackend())
```

## Known Limitations

- `isinstance()` checks verify method existence only — not parameter
  types, return types, or async status. Use a static type checker
  (mypy, pyright) for full validation.
- A class with synchronous `encrypt`/`decrypt` will pass the
  `isinstance()` check but fail at call time in an async context.
