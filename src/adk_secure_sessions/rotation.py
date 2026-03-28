"""Key rotation utility for adk-secure-sessions.

Provides ``rotate_encryption_keys()``, a standalone async function that
re-encrypts all session data in a SQL database from one encryption backend
to another. Designed for same-backend passphrase rotation — the scenario
where ``additional_backends`` cannot be used because both old and new
backends share the same ``backend_id``.

There are two rotation paths:

* **Path A — Lazy cross-backend migration**: Already works via
  ``EncryptedSessionService(additional_backends=[old_backend])`` for
  backends with different ``backend_id`` values. No utility required.
* **Path B — Batch same-backend rotation**: Requires this utility when
  old and new backends share a ``backend_id`` (e.g., rotating Fernet
  passphrases). Reads all encrypted records, re-encrypts with the new
  backend, and writes back with optimistic concurrency protection via
  ``update_time``.

Examples:
    Rotate all session data from one Fernet passphrase to another:

    ```python
    from adk_secure_sessions import FernetBackend
    from adk_secure_sessions.rotation import RotationResult, rotate_encryption_keys

    old = FernetBackend("old-passphrase")
    new = FernetBackend("new-passphrase")
    result: RotationResult = await rotate_encryption_keys(
        db_url="sqlite+aiosqlite:///sessions.db",
        old_backend=old,
        new_backend=new,
    )
    print(f"Rotated: {result.rotated}, Skipped: {result.skipped}")
    if result.skipped:
        print("Re-run to pick up records skipped due to concurrent writes")
    ```

See Also:
    [`adk_secure_sessions.services.encrypted_session`][adk_secure_sessions.services.encrypted_session]:
    ``additional_backends`` parameter for cross-backend lazy migration (Path A).
"""

from __future__ import annotations

import asyncio
import base64
import binascii
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from adk_secure_sessions.exceptions import DecryptionError
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.serialization import (
    ENVELOPE_VERSION_1,
    _build_envelope,
    _parse_envelope,
)

# ---------------------------------------------------------------------------
# Table specifications
# ---------------------------------------------------------------------------

_TABLE_SPECS: list[dict[str, Any]] = [
    {
        "table": "sessions",
        "pk_cols": ["app_name", "user_id", "id"],
        "enc_col": "state",
        "has_update_time": True,
    },
    {
        "table": "app_states",
        "pk_cols": ["app_name"],
        "enc_col": "state",
        "has_update_time": True,
    },
    {
        "table": "user_states",
        "pk_cols": ["app_name", "user_id"],
        "enc_col": "state",
        "has_update_time": True,
    },
    {
        "table": "events",
        "pk_cols": ["id", "app_name", "user_id", "session_id"],
        "enc_col": "event_data",
        "has_update_time": False,
    },
]
"""Encrypted table specifications for the rotation pass.

Each entry describes one table: its name, primary key column names,
encrypted column name, and whether an ``update_time`` column exists
for optimistic concurrency detection.
"""


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class RotationResult:
    """Result of a completed key rotation operation.

    Attributes:
        rotated (int): Number of records successfully re-encrypted.
        skipped (int): Number of records skipped due to concurrent writes
            detected via the ``update_time`` optimistic concurrency
            check. Skipped records still use the old encryption key
            and can be picked up by running ``rotate_encryption_keys``
            again.

    Examples:
        ```python
        result = await rotate_encryption_keys(db_url, old, new)
        if result.skipped:
            print(f"{result.skipped} records need a follow-up rotation pass")
        ```
    """

    rotated: int
    skipped: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sync_reencrypt(
    ciphertext: bytes,
    old_decrypt: Callable[[bytes], bytes],
    new_encrypt: Callable[[bytes], bytes],
) -> bytes:
    """Decrypt ciphertext with old key and re-encrypt with new key synchronously.

    Intended to run inside ``asyncio.to_thread()`` because both crypto
    operations are CPU-bound and must not block the event loop.

    Args:
        ciphertext: Encrypted bytes from the old backend (ciphertext
            only, without the envelope header bytes).
        old_decrypt: Synchronous decrypt callable from the old backend.
        new_encrypt: Synchronous encrypt callable from the new backend.

    Returns:
        New ciphertext bytes encrypted with the new backend.

    Examples:
        ```python
        new_ct = await asyncio.to_thread(
            _sync_reencrypt, ciphertext, old.sync_decrypt, new.sync_encrypt
        )
        ```
    """
    plaintext = old_decrypt(ciphertext)
    return new_encrypt(plaintext)


async def _rotate_table(
    conn: Any,
    table: str,
    pk_cols: list[str],
    enc_col: str,
    has_update_time: bool,
    old_backend: EncryptionBackend,
    new_backend: EncryptionBackend,
) -> tuple[int, int]:
    """Re-encrypt all matching records in one table.

    Selects all rows, identifies records encrypted with
    ``old_backend.backend_id`` by parsing the envelope header, re-encrypts
    each with ``new_backend``, and writes back using an optimistic
    concurrency check on both ``update_time`` and the existing ciphertext
    value (``AND update_time = :update_time AND {enc_col} = :old_val``) for
    tables that have ``update_time``. Tables without ``update_time``
    (``events``) use only the ciphertext guard (``AND {enc_col} = :old_val``).

    Args:
        conn: Active SQLAlchemy async connection (within a transaction).
        table: Table name to process.
        pk_cols: Primary key column names.
        enc_col: Name of the encrypted TEXT column.
        has_update_time: Whether this table has an ``update_time`` column
            for optimistic concurrency detection.
        old_backend: Source encryption backend. Records with this
            ``backend_id`` in their envelope header are re-encrypted.
        new_backend: Target encryption backend for the new ciphertext.

    Returns:
        Tuple of ``(rotated, skipped)`` counts for this table.

    Raises:
        DecryptionError: If a record contains non-ASCII or malformed
            base64 data, has a malformed envelope, or cannot be decrypted
            with ``old_backend``.
    """
    rotated = 0
    skipped = 0

    # Build SELECT — column names are hardcoded constants, not user input
    select_col_list = pk_cols + [enc_col]
    if has_update_time:
        select_col_list = select_col_list + ["update_time"]
    select_cols = ", ".join(select_col_list)
    select_sql = f"SELECT {select_cols} FROM {table}"
    rows = (await conn.execute(text(select_sql))).fetchall()

    for row in rows:
        row_data = dict(row._mapping)
        enc_val: str | None = row_data[enc_col]

        if enc_val is None:
            continue  # NULL event_data — skip without counting

        # Base64-decode the stored TEXT value to get the raw envelope bytes
        try:
            envelope = base64.b64decode(enc_val.encode("ascii"), validate=True)
        except (binascii.Error, UnicodeEncodeError):
            msg = f"Rotation failed: base64 decode error in table {table!r}"
            raise DecryptionError(msg) from None

        # Parse the envelope header — raises DecryptionError if malformed
        _version, backend_id, ciphertext = _parse_envelope(envelope)

        if backend_id != old_backend.backend_id:
            continue  # Already on a different backend — skip silently

        # Re-encrypt: CPU-bound crypto runs in a thread to avoid blocking
        try:
            new_ciphertext = await asyncio.to_thread(
                _sync_reencrypt,
                ciphertext,
                old_backend.sync_decrypt,
                new_backend.sync_encrypt,
            )
        except DecryptionError:
            raise
        except Exception:
            msg = f"Rotation failed: re-encryption error in table {table!r}"
            raise DecryptionError(msg) from None

        # Build new envelope and base64-encode for storage
        new_envelope = _build_envelope(
            ENVELOPE_VERSION_1, new_backend.backend_id, new_ciphertext
        )
        new_b64 = base64.b64encode(new_envelope).decode("ascii")

        # Build parametrized UPDATE — values use bound parameters.
        # old_val guards against same-timestamp ciphertext collisions:
        # if another writer changed the encrypted value between our read and
        # write (even with the same update_time), rows_affected == 0.
        pk_params = {col: row_data[col] for col in pk_cols}
        update_params: dict[str, Any] = {
            **pk_params,
            "new_val": new_b64,
            "old_val": enc_val,
        }
        pk_where = " AND ".join(f"{col} = :{col}" for col in pk_cols)

        if has_update_time:
            update_params["update_time"] = row_data["update_time"]
            update_sql = (
                f"UPDATE {table} SET {enc_col} = :new_val "
                f"WHERE {pk_where} AND update_time = :update_time "
                f"AND {enc_col} = :old_val"
            )
        else:
            update_sql = (
                f"UPDATE {table} SET {enc_col} = :new_val "
                f"WHERE {pk_where} AND {enc_col} = :old_val"
            )

        result = await conn.execute(text(update_sql), update_params)

        if result.rowcount > 0:
            rotated += 1
        elif has_update_time:
            skipped += 1
        # Events (no update_time): 0 rowcount means cascade-deleted — not counted

    return rotated, skipped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def rotate_encryption_keys(
    db_url: str,
    old_backend: EncryptionBackend,
    new_backend: EncryptionBackend,
) -> RotationResult:
    """Re-encrypt all session data from one backend to another.

    Reads all encrypted records from the four session tables
    (``sessions``, ``app_states``, ``user_states``, ``events``),
    identifies records encrypted with ``old_backend`` by checking the
    envelope ``backend_id`` byte, and re-encrypts them using
    ``new_backend``. Records already on a different backend are skipped
    silently.

    Uses ``update_time`` and the existing ciphertext value as an optimistic
    concurrency guard for ``sessions``, ``app_states``, and ``user_states``.
    If a record is modified between the rotation function's read and write
    (``rows_affected == 0``), it is counted as skipped. Run the function
    again to pick up remaining records.

    **Re-run semantics differ by rotation type:**

    - *Cross-backend rotation* (``old_backend.backend_id !=
      new_backend.backend_id``): Re-runs are safe. Already-rotated records
      carry ``new_backend.backend_id`` in their envelope and are skipped
      silently by the backend-id filter.
    - *Same-backend rotation* (``old_backend.backend_id ==
      new_backend.backend_id``, e.g., two ``FernetBackend`` instances):
      A single pass is expected. Re-running with the original ``old_backend``
      will attempt to decrypt already-rotated ciphertext with the old key
      and raise ``DecryptionError``. For same-backend rotation, stop or
      pause the service before running this function, run once, then
      reconfigure the service to use ``new_backend`` and restart.

    For the ``events`` table (no ``update_time`` column), ``rows_affected
    == 0`` means the event was cascade-deleted between read and write and
    is not counted as skipped.

    Cryptographic operations (``sync_decrypt``, ``sync_encrypt``) run per
    record in a thread via ``asyncio.to_thread()`` to avoid blocking the
    event loop. For databases with very large numbers of records, run this
    utility during a low-traffic window to minimise thread-pool pressure.

    Args:
        db_url: SQLAlchemy connection string (e.g.,
            ``"sqlite+aiosqlite:///sessions.db"``).
        old_backend: Backend used to decrypt existing records. Records
            whose envelope ``backend_id`` matches ``old_backend.backend_id``
            are re-encrypted.
        new_backend: Backend used to encrypt re-written records.

    Returns:
        A ``RotationResult`` with ``rotated`` (successfully re-encrypted)
        and ``skipped`` (concurrent-write collisions) counts across all
        four tables.

    Raises:
        DecryptionError: If a record cannot be decrypted with
            ``old_backend``, or if a stored value has a malformed
            envelope. Error messages never contain key material.

    Examples:
        Rotate from one Fernet passphrase to another:

        ```python
        from adk_secure_sessions import FernetBackend
        from adk_secure_sessions.rotation import rotate_encryption_keys

        old = FernetBackend("old-passphrase")
        new = FernetBackend("new-passphrase")
        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///sessions.db",
            old_backend=old,
            new_backend=new,
        )
        print(f"Rotated {result.rotated} records, skipped {result.skipped}")
        ```

    See Also:
        [`adk_secure_sessions.services.encrypted_session`][]: Use
        ``additional_backends`` for cross-backend lazy migration
        (Path A, no utility required).
    """
    engine = create_async_engine(db_url)
    rotated = 0
    skipped = 0

    try:
        for spec in _TABLE_SPECS:
            async with engine.begin() as conn:
                r, s = await _rotate_table(
                    conn=conn,
                    table=spec["table"],
                    pk_cols=spec["pk_cols"],
                    enc_col=spec["enc_col"],
                    has_update_time=spec["has_update_time"],
                    old_backend=old_backend,
                    new_backend=new_backend,
                )
                rotated += r
                skipped += s
    finally:
        await engine.dispose()

    return RotationResult(rotated=rotated, skipped=skipped)
