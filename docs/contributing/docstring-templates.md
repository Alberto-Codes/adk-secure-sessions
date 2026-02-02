# Docstring Templates

These templates show the preferred Google-style docstrings for this repo and
are optimized for mkdocstrings rendering. Copy and adapt them for new modules,
classes, functions, and interfaces.

## Quick Guidance

- Use **Examples** (plural) for code samples with fenced code blocks (` ```python `).
- Use **Example** (singular) only for admonition-style callouts.
- **Prefer fenced code blocks** over doctest format (`>>>`) - they copy cleanly
  without prompt characters and render better in mkdocs-material.
- Include types in **Attributes** (e.g., `name (str): Description`) since types
  aren't visible from class/module-level attributes like they are in function Args.
- Use `Note:` and `Warning:` sections for short admonitions.
- Use `Warns:` for `warnings.warn(...)` emissions.
- Use `Other Parameters:` for optional keyword-only or `**kwargs` arguments (include types!).
- Keep the first line as a concise summary (imperative tone).

## Module Template (__init__.py)

```python
"""Encryption backends for adk-secure-sessions.

This package contains pluggable encryption backends that handle the
actual encrypt/decrypt operations for session data.

Attributes:
    FernetBackend (class): Symmetric encryption using Fernet.
    EncryptionBackend (class): Protocol for custom backends.

Examples:
    Basic usage with Fernet:

    ```python
    from adk_secure_sessions.backends import FernetBackend

    backend = FernetBackend(key="your-secret-key")
    ```

See Also:
    - [`adk_secure_sessions.services`][adk_secure_sessions.services]: Session service implementations.
"""
```

## Class Template

```python
class EncryptedSessionService:
    """Encrypted drop-in replacement for ADK's DatabaseSessionService.

    Attributes:
        db_url (str): SQLAlchemy database URL.
        backend (EncryptionBackend): Encryption backend instance.

    Examples:
        Create an encrypted session service:

        ```python
        service = EncryptedSessionService(
            db_url="sqlite+aiosqlite:///./sessions.db",
            encryption_key="your-secret-key",
        )
        session = await service.create_session(
            app_name="my_agent", user_id="user_123"
        )
        ```

    Note:
        All session state values are encrypted before storage.
        Session metadata (app_name, user_id, timestamps) remains queryable.
    """
```

## __init__ Method Template

```python
def __init__(
    self,
    db_url: str,
    *,
    encryption_key: str | bytes | None = None,
    backend: EncryptionBackend | None = None,
) -> None:
    """Initialize the encrypted session service.

    Args:
        db_url: SQLAlchemy async database URL.

    Other Parameters:
        encryption_key (str | bytes | None): Key for the default Fernet backend.
        backend (EncryptionBackend | None): Custom encryption backend (overrides key).

    Raises:
        ConfigurationError: If neither key nor backend is provided.

    Note:
        Provide either ``encryption_key`` (uses Fernet) or ``backend`` (custom), not both.
    """
```

## Async Method Template

```python
async def encrypt_state(
    self,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Encrypt all values in a session state dictionary.

    Args:
        state: Plaintext session state key-value pairs.

    Returns:
        Dictionary with encrypted values (keys remain plaintext).

    Raises:
        EncryptionError: If encryption fails for any value.

    Examples:
        Encrypt sensitive state:

        ```python
        encrypted = await backend.encrypt_state({"ssn": "123-45-6789"})
        assert encrypted["ssn"] != "123-45-6789"
        ```

    Warning:
        Keys are NOT encrypted — do not store sensitive data in key names.
    """
```

## Protocol / Interface Template

```python
from typing import Protocol


class EncryptionBackend(Protocol):
    """Protocol for encryption backends.

    Implement this protocol to create custom encryption backends
    (e.g., AWS KMS, GCP KMS, HashiCorp Vault).

    Examples:
        Implement a custom backend:

        ```python
        class MyKMSBackend:
            async def encrypt(self, plaintext: bytes) -> bytes:
                return await kms_client.encrypt(plaintext)

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return await kms_client.decrypt(ciphertext)
        ```
    """

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes.

        Args:
            plaintext: Data to encrypt.

        Returns:
            Encrypted ciphertext bytes.
        """

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes.

        Args:
            ciphertext: Data to decrypt.

        Returns:
            Decrypted plaintext bytes.
        """
```

## Exception Template

```python
class EncryptionError(Exception):
    """Base exception for encryption errors.

    Args:
        message: Human-readable error message.
        cause: Optional underlying exception.

    Note:
        All encryption exceptions inherit from this base for consistent handling.
    """


class DecryptionError(EncryptionError):
    """Raised when decryption fails.

    This typically indicates a wrong key, corrupted data, or tampered ciphertext.

    Args:
        message: Human-readable error message.
    """
```

## Dataclass Model Template

```python
from dataclasses import dataclass


@dataclass(slots=True)
class EncryptionMetadata:
    """Metadata about an encrypted field.

    Attributes:
        backend_name (str): Name of the encryption backend used.
        encrypted_at (str): ISO 8601 timestamp of encryption.
        key_id (str | None): Identifier for the encryption key (for rotation).

    Examples:
        ```python
        meta = EncryptionMetadata(
            backend_name="fernet",
            encrypted_at="2026-01-15T10:30:00Z",
            key_id=None,
        )
        ```
    """

    backend_name: str
    encrypted_at: str
    key_id: str | None = None
```

## Supported Sections (Quick Reference)

| Section | Purpose | Aliases |
| --- | --- | --- |
| `Args` | Parameters for functions/methods | `Arguments`, `Params` |
| `Other Parameters` | Secondary `**kwargs` (include types!) | `Keyword Args`, `Keyword Arguments` |
| `Returns` | Return values | |
| `Yields` | Generator yields | |
| `Raises` | Exceptions raised | |
| `Warns` | Warnings emitted | `Warnings` |
| `Attributes` | Module/class attributes | |
| `Examples` | Fenced code block examples (prefer ` ```python `) | |
| `See Also` | Related APIs | |
| `Note` | Brief admonitions | |
| `Warning` | Important warnings | |
