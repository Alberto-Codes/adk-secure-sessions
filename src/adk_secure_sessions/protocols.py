"""Encryption backend protocol for adk-secure-sessions.

Defines the contract that all encryption backends must satisfy.
Backends implement two async methods — ``encrypt`` and ``decrypt`` —
operating on raw bytes. No inheritance or registration is required;
any class with matching method signatures conforms via structural
subtyping (PEP 544).

Examples:
    Define a conforming backend and verify at runtime:

    ```python
    class MyBackend:
        async def encrypt(self, plaintext: bytes) -> bytes: ...
        async def decrypt(self, ciphertext: bytes) -> bytes: ...


    from adk_secure_sessions.protocols import EncryptionBackend

    assert isinstance(MyBackend(), EncryptionBackend)  # True
    ```

See Also:
    [`adk_secure_sessions.backends.fernet`][adk_secure_sessions.backends.fernet]:
    Reference implementation using Fernet symmetric encryption.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EncryptionBackend(Protocol):
    """Contract for all encryption backends.

    Implementors provide ``encrypt`` and ``decrypt`` as async methods
    that accept and return raw ``bytes``. The session service uses
    this protocol for runtime validation at initialization and static
    type checkers verify conformance at analysis time.

    This is a ``typing.Protocol`` — not an abstract base class.
    Conforming classes do not need to inherit from or import this
    protocol.

    Known limitations of ``@runtime_checkable``:

    * ``isinstance()`` checks verify method **existence** only. It
      does not validate parameter types, return types, or whether
      methods are coroutines. Use a static type checker (mypy,
      pyright) for full signature validation.
    * A class with synchronous ``encrypt``/``decrypt`` methods will
      pass the ``isinstance()`` check but fail at call time in an
      async context.

    Examples:
        Define a minimal conforming backend:

        ```python
        class MyBackend:
            async def encrypt(self, plaintext: bytes) -> bytes:
                return plaintext  # replace with real encryption

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext  # replace with real decryption


        assert isinstance(MyBackend(), EncryptionBackend)
        ```
    """

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes.

        Examples:
            ```python
            ciphertext = await backend.encrypt(b"hello")
            ```
        """
        ...

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes.

        Args:
            ciphertext: Encrypted bytes to decrypt.

        Returns:
            Decrypted plaintext as bytes.

        Examples:
            ```python
            plaintext = await backend.decrypt(ciphertext)
            ```
        """
        ...
