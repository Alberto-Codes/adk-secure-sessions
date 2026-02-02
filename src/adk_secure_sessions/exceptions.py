"""Exception hierarchy for adk-secure-sessions.

All library exceptions inherit from ``SecureSessionError`` to enable
broad exception handling while keeping specific failure modes
distinguishable in control flow.

Examples:
    Catch all library errors::

        from adk_secure_sessions.exceptions import SecureSessionError

        try:
            await backend.decrypt(ciphertext)
        except SecureSessionError:
            ...

    Catch only decryption failures::

        from adk_secure_sessions.exceptions import DecryptionError

        try:
            await backend.decrypt(ciphertext)
        except DecryptionError:
            ...
"""


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


class EncryptionError(SecureSessionError):
    """Raised when encryption fails.

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


class DecryptionError(SecureSessionError):
    """Raised when decryption fails.

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


class SerializationError(SecureSessionError):
    """Raised when data cannot be serialized to JSON.

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
