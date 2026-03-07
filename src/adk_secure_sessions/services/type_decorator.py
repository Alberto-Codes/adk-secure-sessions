"""EncryptedJSON TypeDecorator for transparent column encryption.

Provides a SQLAlchemy ``TypeDecorator`` that encrypts Python dicts to
base64-encoded encrypted envelopes on write and decrypts back to dicts
on read. Uses the envelope format from ``serialization.py`` to ensure
all encrypted data is self-describing.

This module is an internal implementation detail and is NOT exported
in the public API.

Examples:
    Create an EncryptedJSON column type:

    ```python
    from adk_secure_sessions.services.type_decorator import EncryptedJSON

    encrypted_col = EncryptedJSON(
        encrypt_fn=fernet.encrypt,
        backend_id=0x01,
        decrypt_dispatch={0x01: fernet.decrypt},
    )
    ```

See Also:
    [`adk_secure_sessions.serialization`][adk_secure_sessions.serialization]:
    Envelope format helpers used by this TypeDecorator.
"""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Callable
from typing import Any

from cryptography.fernet import InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from adk_secure_sessions.exceptions import DecryptionError
from adk_secure_sessions.serialization import (
    ENVELOPE_VERSION_1,
    _build_envelope,
    _parse_envelope,
)


class EncryptedJSON(TypeDecorator[dict[str, Any]]):
    """TypeDecorator that encrypts dict values to TEXT columns.

    Encrypts on write via ``process_bind_param`` and decrypts on read
    via ``process_result_value``. The encrypted data is stored as a
    base64-encoded string in a TEXT column.

    The write path is:
    ``dict -> json.dumps -> encrypt_fn(plaintext) -> envelope -> base64 -> TEXT``

    The read path is:
    ``TEXT -> base64 -> envelope -> dispatch[backend_id](ct) -> json.loads -> dict``

    Attributes:
        impl (type[Text]): The underlying SQLAlchemy column type.
        cache_ok (bool): Safe to cache because behavior depends only on
            init-time parameters.

    Examples:
        Use with a SQLAlchemy model:

        ```python
        from sqlalchemy.orm import Mapped, mapped_column

        encrypted = EncryptedJSON(
            encrypt_fn=fernet.encrypt,
            backend_id=0x01,
            decrypt_dispatch={0x01: fernet.decrypt},
        )
        state: Mapped[dict] = mapped_column(encrypted)
        ```
    """

    impl = Text
    cache_ok = True

    def __init__(
        self,
        encrypt_fn: Callable[[bytes], bytes],
        backend_id: int,
        decrypt_dispatch: dict[int, Callable[[bytes], bytes]],
    ) -> None:
        """Initialize the EncryptedJSON TypeDecorator.

        Args:
            encrypt_fn: Synchronous callable that encrypts plaintext bytes.
            backend_id: Integer identifying the encryption backend for
                the envelope header (used for writes).
            decrypt_dispatch: Mapping of backend_id to sync decrypt
                callable. On read, the backend_id from the envelope
                header selects the correct decrypt function.
        """
        super().__init__()
        self._encrypt_fn = encrypt_fn
        self._backend_id = backend_id
        self._decrypt_dispatch = decrypt_dispatch

    def process_bind_param(
        self,
        value: dict[str, Any] | None,
        dialect: Any,
    ) -> str | None:
        """Encrypt a dict value for storage in the database.

        Args:
            value: Python dict to encrypt, or None.
            dialect: SQLAlchemy dialect (unused).

        Returns:
            Base64-encoded encrypted envelope string, or None.
        """
        if value is None:
            return None

        plaintext = json.dumps(value).encode("utf-8")
        ciphertext = self._encrypt_fn(plaintext)
        envelope = _build_envelope(ENVELOPE_VERSION_1, self._backend_id, ciphertext)
        return base64.b64encode(envelope).decode("ascii")

    def process_result_value(
        self,
        value: str | None,
        dialect: Any,
    ) -> dict[str, Any] | None:
        """Decrypt a stored value back to a Python dict.

        Parses the envelope header to extract the backend_id byte,
        then dispatches to the matching decrypt function from the
        ``_decrypt_dispatch`` map.

        Args:
            value: Base64-encoded encrypted envelope string, or None.
            dialect: SQLAlchemy dialect (unused).

        Returns:
            Decrypted Python dict, or None.

        Raises:
            DecryptionError: If decryption fails due to wrong key,
                tampered ciphertext, malformed input, unencrypted
                data (invalid envelope format), or unregistered
                backend_id in the dispatch map.
        """
        if value is None:
            return None

        try:
            envelope = base64.b64decode(value.encode("ascii"), validate=True)
            _version, backend_id, ciphertext = _parse_envelope(envelope)
            decrypt_fn = self._decrypt_dispatch.get(backend_id)
            if decrypt_fn is None:
                msg = f"No decrypt function registered for backend_id {backend_id:#04x}"
                raise DecryptionError(msg)
            plaintext = decrypt_fn(ciphertext)
            return json.loads(plaintext)
        except InvalidToken:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg) from None
        except DecryptionError:
            raise
        except (binascii.Error, UnicodeEncodeError):
            msg = (
                "Decryption failed: data does not appear to be encrypted "
                "(invalid envelope format)"
            )
            raise DecryptionError(msg) from None
