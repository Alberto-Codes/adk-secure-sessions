"""Exception hierarchy for adk-secure-sessions.

All library exceptions inherit from ``SecureSessionError`` to enable
broad exception handling while keeping specific failure modes
distinguishable in control flow.

Examples:
    Catch all library errors:

    ```python
    from adk_secure_sessions.exceptions import SecureSessionError

    try:
        await backend.decrypt(ciphertext)
    except SecureSessionError:
        ...
    ```

    Catch only decryption failures:

    ```python
    from adk_secure_sessions.exceptions import DecryptionError

    try:
        await backend.decrypt(ciphertext)
    except DecryptionError:
        ...
    ```

See Also:
    [`adk_secure_sessions.protocols`][adk_secure_sessions.protocols]:
    Encryption backend protocol definition.
"""

from sqlalchemy.exc import DontWrapMixin


class SecureSessionError(Exception):
    """Base exception for all adk-secure-sessions errors.

    All library-specific exceptions inherit from this class so callers
    can use a single ``except SecureSessionError`` clause to handle any
    failure originating from this package.

    Examples:
        Catch any library error regardless of type:

        ```python
        try:
            await backend.encrypt(plaintext)
        except SecureSessionError:
            log.error("adk-secure-sessions operation failed")
        ```
    """


class EncryptionError(SecureSessionError, DontWrapMixin):
    """Raised when encryption fails.

    Inherits ``DontWrapMixin`` so SQLAlchemy propagates this directly
    instead of wrapping it in ``StatementError``.

    Possible causes include invalid plaintext input or backend-specific
    errors. Error messages intentionally exclude key material, plaintext,
    and ciphertext to prevent information leakage.

    Examples:
        Handle encryption failures specifically:

        ```python
        try:
            ciphertext = await backend.encrypt(plaintext)
        except EncryptionError:
            log.error("Encryption failed")
        ```
    """


class DecryptionError(SecureSessionError, DontWrapMixin):
    """Raised when decryption fails.

    Inherits ``DontWrapMixin`` so SQLAlchemy propagates this directly
    instead of wrapping it in ``StatementError``.

    Possible causes include a wrong key, tampered ciphertext, or
    malformed input. Error messages intentionally exclude key material,
    ciphertext, and plaintext to prevent information leakage.

    Examples:
        Handle decryption failures specifically:

        ```python
        try:
            plaintext = await backend.decrypt(ciphertext)
        except DecryptionError:
            log.error("Decryption failed, check key")
        ```
    """


class SerializationError(SecureSessionError, DontWrapMixin):
    """Raised when data cannot be serialized to JSON.

    Inherits ``DontWrapMixin`` so SQLAlchemy propagates this directly
    instead of wrapping it in ``StatementError``.

    This indicates a caller bug — the input contains types that are not
    JSON-serializable (e.g., ``datetime``, custom objects). This is
    distinct from encryption/decryption failures which indicate
    configuration or data integrity issues.

    Examples:
        Handle serialization failures:

        ```python
        try:
            envelope = await encrypt_session(data, backend, backend_id)
        except SerializationError:
            log.error("Data contains non-JSON-serializable values")
        ```
    """


class ConfigurationError(SecureSessionError):
    """Raised when the service is misconfigured at startup.

    Covers invalid encryption keys, backends that do not conform to the
    ``EncryptionBackend`` protocol, invalid backend IDs, empty database
    paths, and database connection failures. Error messages never include
    key material or other sensitive data.

    Examples:
        Handle configuration failures at startup:

        ```python
        try:
            service = EncryptedSessionService(
                db_url="sqlite+aiosqlite:///sessions.db",
                backend=my_backend,
            )
        except ConfigurationError as exc:
            log.error("Service misconfigured: %s", exc)
        ```
    """
