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
    """


class DecryptionError(SecureSessionError):
    """Raised when decryption fails.

    Possible causes include a wrong key, tampered ciphertext, or
    malformed input. Error messages intentionally exclude key material,
    ciphertext, and plaintext to prevent information leakage.
    """
