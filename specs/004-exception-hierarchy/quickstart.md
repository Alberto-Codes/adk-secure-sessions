# Quickstart: Exception Hierarchy

**Feature**: 004-exception-hierarchy

## What's Changing

Adding `EncryptionError` to the existing exception hierarchy and exporting it from the public API. The hierarchy becomes:

- `SecureSessionError` (base) — catch-all for library errors
- `EncryptionError` (new) — encryption failures
- `DecryptionError` (exists) — decryption failures

## Files to Modify

1. `src/adk_secure_sessions/exceptions.py` — Add `EncryptionError` class
2. `src/adk_secure_sessions/__init__.py` — Export `EncryptionError`
3. `tests/unit/test_exceptions.py` — New test file for hierarchy tests

## Usage After Implementation

```python
from adk_secure_sessions import (
    SecureSessionError,
    EncryptionError,
    DecryptionError,
)

# Catch all library errors
try:
    await backend.encrypt(data)
except SecureSessionError:
    log.error("Library error occurred")

# Catch only encryption failures
try:
    await backend.encrypt(data)
except EncryptionError:
    log.error("Encryption failed")

# Catch only decryption failures
try:
    await backend.decrypt(data)
except DecryptionError:
    log.error("Decryption failed")
```
