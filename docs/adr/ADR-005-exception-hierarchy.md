# ADR-005: Exception Hierarchy

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

Encryption operations can fail in ways that are distinct from general session service errors. Users need to distinguish between:

- Wrong encryption key (decryption failure)
- Corrupted or tampered ciphertext
- Backend configuration errors

Generic `Exception` or `ValueError` does not give users enough information to handle these cases. ADK's own session services raise their own exceptions, and we should not swallow or re-wrap those unnecessarily.

## Decision

Start with a minimal exception hierarchy. Add subclasses when the code demands them, not before.

### Initial Hierarchy

```
SecureSessionError                    # Base — catch-all for this library
├── EncryptionError                   # Encryption operation failed
└── DecryptionError                   # Decryption operation failed (wrong key, tampered data, etc.)
```

Three classes. That's it for v1.

### Rules

1. **All library exceptions inherit from `SecureSessionError`**. Users can catch the base to handle any library error.

2. **Never swallow ADK exceptions.** If ADK's base class raises (e.g., stale session in `append_event`), let it propagate. We only wrap errors from our own encryption/decryption layer.

3. **`DecryptionError` covers multiple failure modes.** Wrong key, corrupted data, and tampered ciphertext all raise `DecryptionError` with a descriptive message. If we later find that callers need to distinguish these programmatically, we add subclasses then.

4. **No sensitive data in exception messages.** Never include ciphertext, key material, or plaintext in error messages to avoid leaking into logs.

### Example Usage

```python
from adk_secure_sessions.exceptions import (
    DecryptionError,
    SecureSessionError,
)

try:
    session = await service.get_session(
        app_name="my_agent", user_id="user_123", session_id="abc"
    )
except DecryptionError as e:
    logger.error(f"Failed to decrypt session: {e}")
    # Could be wrong key, corrupted data, or tampered ciphertext
except SecureSessionError as e:
    logger.error(f"Session encryption error: {e}")
```

### When to Add Subclasses

Add a subclass when:
- A caller has a concrete need to handle a failure mode differently in a `try/except` block
- The distinction affects control flow, not just log messages

Do not add a subclass for:
- Categorization that only matters in log messages (use the message string)
- Speculative "someone might need this" scenarios

## Consequences

### What becomes easier

- **Simplicity**: Three classes to understand, document, and test
- **Stability**: Public exception API is small, less likely to need breaking changes
- **Error handling**: Users catch `SecureSessionError` for everything, or `DecryptionError` for the most common failure mode

### What becomes harder

- **Granular handling**: A caller who needs to distinguish "wrong key" from "tampered data" programmatically would need to parse the message string until we add subclasses. This is acceptable for v1 — we add subclasses when real callers ask for them.

## Alternatives Considered

### Six-Class Hierarchy (Original)

**Deferred.** The original design had `EncryptionKeyError`, `EncryptionBackendError`, `DecryptionKeyError`, `TamperedDataError`, and `ConfigurationError`. This is speculative complexity before any code exists. The concepts are valid — `TamperedDataError` in particular is a useful security signal — but we'll add them when the implementation proves they're needed.

### Reuse ADK's Exceptions

**Rejected.** ADK doesn't have encryption-related exceptions. Using generic `ValueError` loses semantic meaning.

### Single Exception Class

**Rejected.** Callers commonly need to distinguish "encryption failed on write" from "decryption failed on read" for error handling and monitoring. Two subclasses is the minimum useful granularity.
