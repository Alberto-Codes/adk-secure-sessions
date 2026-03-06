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
        decrypt_fn=fernet.decrypt,
        backend_id=0x01,
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
    ``TEXT -> base64 decode -> parse envelope -> decrypt_fn(ciphertext) -> json.loads -> dict``

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
            decrypt_fn=fernet.decrypt,
            backend_id=0x01,
        )
        state: Mapped[dict] = mapped_column(encrypted)
        ```
    """

    impl = Text
    cache_ok = True

    def __init__(
        self,
        encrypt_fn: Callable[[bytes], bytes],
        decrypt_fn: Callable[[bytes], bytes],
        backend_id: int,
    ) -> None:
        """Initialize the EncryptedJSON TypeDecorator.

        Args:
            encrypt_fn: Synchronous callable that encrypts plaintext bytes.
            decrypt_fn: Synchronous callable that decrypts ciphertext bytes.
            backend_id: Integer identifying the encryption backend for
                the envelope header.
        """
        super().__init__()
        self._encrypt_fn = encrypt_fn
        self._decrypt_fn = decrypt_fn
        self._backend_id = backend_id

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

        Args:
            value: Base64-encoded encrypted envelope string, or None.
            dialect: SQLAlchemy dialect (unused).

        Returns:
            Decrypted Python dict, or None.

        Raises:
            DecryptionError: If decryption fails due to wrong key,
                tampered ciphertext, malformed input, or unencrypted
                data (invalid envelope format).
        """
        if value is None:
            return None

        try:
            envelope = base64.b64decode(value.encode("ascii"), validate=True)
            _version, _backend_id, ciphertext = _parse_envelope(envelope)
            plaintext = self._decrypt_fn(ciphertext)
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
