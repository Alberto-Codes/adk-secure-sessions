# Quickstart: FernetBackend

## Basic Usage

```python
import asyncio
from adk_secure_sessions import FernetBackend

async def main():
    backend = FernetBackend(key="my-secret-passphrase")

    ciphertext = await backend.encrypt(b"sensitive session data")
    plaintext = await backend.decrypt(ciphertext)

    assert plaintext == b"sensitive session data"

asyncio.run(main())
```

## Using a Pre-Generated Fernet Key

```python
from cryptography.fernet import Fernet
from adk_secure_sessions import FernetBackend

key = Fernet.generate_key()  # 44-char base64url key
backend = FernetBackend(key=key)
```

## Error Handling

```python
from adk_secure_sessions import FernetBackend, DecryptionError

backend_a = FernetBackend(key="key-a")
backend_b = FernetBackend(key="key-b")

ciphertext = await backend_a.encrypt(b"secret")

try:
    await backend_b.decrypt(ciphertext)
except DecryptionError:
    print("Decryption failed — wrong key")
```

## Protocol Conformance

```python
from adk_secure_sessions import EncryptionBackend, FernetBackend

backend = FernetBackend(key="my-key")
assert isinstance(backend, EncryptionBackend)  # True
```
