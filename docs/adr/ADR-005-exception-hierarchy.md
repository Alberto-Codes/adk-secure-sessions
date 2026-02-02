# ADR-005: Exception Hierarchy

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

Encryption operations can fail in ways that are distinct from general session service errors. Users need to distinguish between:

- Wrong encryption key (decryption failure)
- Corrupted or tampered ciphertext
- Backend configuration errors (missing KMS permissions, invalid key format)
- ADK compatibility issues (unsupported schema version)

Generic `Exception` or `ValueError` does not give users enough information to handle these cases. ADK's own session services raise their own exceptions, and we should not swallow or re-wrap those unnecessarily.

## Decision

Define a focused exception hierarchy rooted at `SecureSessionError`.

### Hierarchy

```
SecureSessionError                    # Base — catch-all for this library
├── EncryptionError                   # Encryption operation failed
│   ├── EncryptionKeyError            # Invalid, missing, or wrong key
│   └── EncryptionBackendError        # Backend-specific failure (KMS timeout, etc.)
├── DecryptionError                   # Decryption operation failed
│   ├── DecryptionKeyError            # Wrong key for this ciphertext
│   └── TamperedDataError             # HMAC verification failed — data integrity compromised
├── ConfigurationError                # Invalid service configuration
└── CompatibilityError                # ADK version or schema incompatibility
```

### Rules

1. **All library exceptions inherit from `SecureSessionError`**. Users can catch the base to handle any library error.

2. **Never swallow ADK exceptions.** If ADK's session service raises (e.g., database connection error), let it propagate. We only wrap errors from our own encryption/decryption layer.

3. **Include context in exceptions.** Every exception includes a human-readable message. `DecryptionKeyError` and `TamperedDataError` intentionally do NOT include the ciphertext or key material in the message to avoid leaking sensitive data into logs.

4. **`TamperedDataError` is security-critical.** This indicates data integrity has been compromised. Applications should log this at ERROR/CRITICAL level and may want to alert. It means either:
   - The encryption key changed without proper migration
   - The database was modified outside the application
   - An actual tampering attack

### Example Usage

```python
from adk_secure_sessions.exceptions import (
    DecryptionKeyError,
    SecureSessionError,
    TamperedDataError,
)

try:
    session = await service.get_session(
        app_name="my_agent", user_id="user_123", session_id="abc"
    )
except TamperedDataError:
    logger.critical("Data integrity compromised for session abc")
    # Alert security team
except DecryptionKeyError:
    logger.error("Wrong encryption key — check key configuration")
except SecureSessionError as e:
    logger.error(f"Session encryption error: {e}")
```

## Consequences

### What becomes easier

- **Error handling**: Users can catch at the granularity they need (specific or base)
- **Debugging**: Exception type immediately tells you what category of failure occurred
- **Security monitoring**: `TamperedDataError` is a distinct, monitorable signal

### What becomes harder

- **Nothing significant.** The hierarchy is small and focused. Six exception classes is manageable.

## Alternatives Considered

### Reuse ADK's Exceptions

**Rejected.** ADK doesn't have encryption-related exceptions. Raising `ValueError` or generic exceptions would lose the semantic meaning.

### Single Exception Class with Error Codes

**Rejected.** `SecureSessionError(code=TAMPERED_DATA)` is less Pythonic than distinct exception classes and doesn't support typed `except` clauses.
