"""Unit tests for the key rotation utility."""

from __future__ import annotations

import base64
from datetime import datetime

import pytest

from adk_secure_sessions.exceptions import DecryptionError
from adk_secure_sessions.rotation import RotationResult, rotate_encryption_keys
from adk_secure_sessions.serialization import (
    BACKEND_AES_GCM,
    BACKEND_FERNET,
    ENVELOPE_VERSION_1,
    _build_envelope,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_DT = datetime(2026, 1, 1, 12, 0, 0)
"""Fixed datetime for test rows."""


def _make_b64_state(
    backend_id: int, ciphertext: bytes = b"test_ciphertext_data"
) -> str:
    """Build a base64-encoded encrypted envelope for testing.

    Args:
        backend_id: Backend identifier byte for the envelope header.
        ciphertext: Raw bytes to embed as the ciphertext payload.

    Returns:
        Base64-encoded envelope string (as stored in the database).
    """
    envelope = _build_envelope(ENVELOPE_VERSION_1, backend_id, ciphertext)
    return base64.b64encode(envelope).decode("ascii")


class _FakeRow:
    """Minimal row mock with ._mapping attribute."""

    def __init__(self, **data: object) -> None:
        """Initialize with column name/value keyword arguments."""
        self._mapping = data


class _FakeCursor:
    """Minimal cursor mock with .fetchall() and .rowcount."""

    def __init__(self, rows: list | None = None, rowcount: int = 0) -> None:
        """Initialize with optional rows and rowcount.

        Args:
            rows: List of _FakeRow objects returned by fetchall().
            rowcount: Number of affected rows (for UPDATE results).
        """
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchall(self) -> list:
        """Return rows stored at construction time.

        Returns:
            List of row objects.
        """
        return self._rows


def _make_execute_fn(
    mocker,
    select_rows_by_table: dict | None = None,
    update_rowcount: int = 1,
):
    """Build an async execute side_effect distinguishing SELECT from UPDATE.

    Args:
        mocker: pytest-mock mocker fixture.
        select_rows_by_table: Mapping of table name to list of _FakeRow
            objects returned for that table's SELECT query.
        update_rowcount: rowcount returned for all UPDATE calls.

    Returns:
        Async callable suitable for assignment to mock_conn.execute.
    """
    if select_rows_by_table is None:
        select_rows_by_table = {}

    async def _execute(sql, params=None):
        sql_str = str(sql)
        if sql_str.strip().upper().startswith("SELECT"):
            for table, rows in select_rows_by_table.items():
                if f"FROM {table}" in sql_str:
                    return _FakeCursor(rows=rows)
            return _FakeCursor(rows=[])
        return _FakeCursor(rows=[], rowcount=update_rowcount)

    return _execute


def _setup_mock_engine(mocker, execute_fn):
    """Patch create_async_engine and configure mock connection.

    Args:
        mocker: pytest-mock mocker fixture.
        execute_fn: Async callable for mock_conn.execute.

    Returns:
        The configured mock connection.
    """
    mock_conn = mocker.AsyncMock()
    mock_conn.execute = execute_fn

    mock_ctx = mocker.MagicMock()
    mock_ctx.__aenter__ = mocker.AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = mocker.AsyncMock(return_value=None)

    mock_eng = mocker.MagicMock()
    mock_eng.begin.return_value = mock_ctx
    mock_eng.dispose = mocker.AsyncMock()

    mocker.patch(
        "adk_secure_sessions.rotation.create_async_engine",
        return_value=mock_eng,
    )
    return mock_conn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def old_backend(mocker):
    """Mock old encryption backend with backend_id=BACKEND_FERNET."""
    b = mocker.MagicMock()
    b.backend_id = BACKEND_FERNET
    b.sync_decrypt = mocker.MagicMock(return_value=b"decrypted_plaintext")
    return b


@pytest.fixture
def new_backend(mocker):
    """Mock new encryption backend with backend_id=BACKEND_AES_GCM."""
    b = mocker.MagicMock()
    b.backend_id = BACKEND_AES_GCM
    b.sync_encrypt = mocker.MagicMock(return_value=b"new_ciphertext_bytes")
    return b


# ---------------------------------------------------------------------------
# US1: Empty database
# ---------------------------------------------------------------------------


class TestEmptyDatabase:
    """Empty database returns zero counts without error."""

    async def test_empty_db_returns_zero_result(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T001: Empty database returns RotationResult(rotated=0, skipped=0)."""
        execute_fn = _make_execute_fn(mocker, select_rows_by_table={})
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 0
        assert result.skipped == 0

    async def test_empty_db_does_not_raise(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T002: Empty database completes without raising any exception."""
        execute_fn = _make_execute_fn(mocker, select_rows_by_table={})
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert isinstance(result, RotationResult)
        old_backend.sync_decrypt.assert_not_called()


# ---------------------------------------------------------------------------
# US2: Records successfully rotated
# ---------------------------------------------------------------------------


class TestRecordsRotated:
    """Records matching old_backend.backend_id are re-encrypted."""

    async def test_one_session_returns_rotated_one(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T003: One matching session record returns RotationResult(rotated=1, skipped=0)."""
        row = _FakeRow(
            app_name="app1",
            user_id="u1",
            id="s1",
            state=_make_b64_state(BACKEND_FERNET),
            update_time=_DT,
        )
        execute_fn = _make_execute_fn(
            mocker,
            select_rows_by_table={"sessions": [row]},
            update_rowcount=1,
        )
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 1
        assert result.skipped == 0

    async def test_two_sessions_return_rotated_two(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T004: Two matching session records return RotationResult(rotated=2, skipped=0)."""
        rows = [
            _FakeRow(
                app_name="app1",
                user_id="u1",
                id=f"s{i}",
                state=_make_b64_state(BACKEND_FERNET),
                update_time=_DT,
            )
            for i in range(2)
        ]
        execute_fn = _make_execute_fn(
            mocker,
            select_rows_by_table={"sessions": rows},
            update_rowcount=1,
        )
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 2
        assert result.skipped == 0
        assert old_backend.sync_decrypt.call_count == 2


# ---------------------------------------------------------------------------
# US3: Optimistic concurrency skip
# ---------------------------------------------------------------------------


class TestOptimisticConcurrency:
    """Concurrent writes cause records to be skipped, not overwritten."""

    async def test_zero_rowcount_increments_skipped(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T005: When UPDATE rows_affected=0 for a session, skipped count increments."""
        row = _FakeRow(
            app_name="app1",
            user_id="u1",
            id="s1",
            state=_make_b64_state(BACKEND_FERNET),
            update_time=_DT,
        )
        execute_fn = _make_execute_fn(
            mocker,
            select_rows_by_table={"sessions": [row]},
            update_rowcount=0,
        )
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.skipped == 1
        assert result.rotated == 0

    async def test_partial_concurrent_writes_tracked(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T006: Mixed rowcount — one rotated, one skipped — tracked correctly."""
        rows = [
            _FakeRow(
                app_name="app1",
                user_id="u1",
                id="s1",
                state=_make_b64_state(BACKEND_FERNET),
                update_time=_DT,
            ),
            _FakeRow(
                app_name="app1",
                user_id="u1",
                id="s2",
                state=_make_b64_state(BACKEND_FERNET),
                update_time=_DT,
            ),
        ]
        call_count = {"n": 0}
        # First UPDATE succeeds, second gets concurrent write (0 rowcount)
        rowcounts = [1, 0]

        async def execute_fn(sql, params=None):
            sql_str = str(sql)
            if sql_str.strip().upper().startswith("SELECT"):
                if "FROM sessions" in sql_str:
                    return _FakeCursor(rows=rows)
                return _FakeCursor(rows=[])
            rc = rowcounts[call_count["n"] % len(rowcounts)]
            call_count["n"] += 1
            return _FakeCursor(rows=[], rowcount=rc)

        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 1
        assert result.skipped == 1


# ---------------------------------------------------------------------------
# US4: Backend ID filtering
# ---------------------------------------------------------------------------


class TestBackendIdFiltering:
    """Only records matching old_backend.backend_id are processed."""

    async def test_record_with_new_backend_id_is_silently_skipped(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T007: Record with new backend_id is skipped silently (not counted)."""
        row = _FakeRow(
            app_name="app1",
            user_id="u1",
            id="s1",
            state=_make_b64_state(BACKEND_AES_GCM),
            update_time=_DT,
        )
        execute_fn = _make_execute_fn(
            mocker,
            select_rows_by_table={"sessions": [row]},
            update_rowcount=1,
        )
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 0
        assert result.skipped == 0
        old_backend.sync_decrypt.assert_not_called()

    async def test_mixed_backends_only_processes_old_backend_records(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T008: Records with old and new backends: only old backend records rotated."""
        rows = [
            _FakeRow(
                app_name="app1",
                user_id="u1",
                id="s1",
                state=_make_b64_state(BACKEND_FERNET),
                update_time=_DT,
            ),
            _FakeRow(
                app_name="app1",
                user_id="u1",
                id="s2",
                state=_make_b64_state(BACKEND_AES_GCM),
                update_time=_DT,
            ),
        ]
        execute_fn = _make_execute_fn(
            mocker,
            select_rows_by_table={"sessions": rows},
            update_rowcount=1,
        )
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 1
        assert result.skipped == 0
        assert old_backend.sync_decrypt.call_count == 1


# ---------------------------------------------------------------------------
# US5: Error message safety (NFR6)
# ---------------------------------------------------------------------------


class TestErrorMessageSafety:
    """Key material must not appear in rotation exception messages."""

    async def test_unexpected_exception_wrapped_without_key_material(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T009: Unexpected decrypt error wrapped into safe DecryptionError message."""
        old_backend.sync_decrypt.side_effect = RuntimeError(
            "internal error: master_key=SUPER_SECRET_KEY_BYTES"
        )

        row = _FakeRow(
            app_name="app1",
            user_id="u1",
            id="s1",
            state=_make_b64_state(BACKEND_FERNET),
            update_time=_DT,
        )
        execute_fn = _make_execute_fn(mocker, select_rows_by_table={"sessions": [row]})
        _setup_mock_engine(mocker, execute_fn)

        with pytest.raises(DecryptionError) as exc_info:
            await rotate_encryption_keys(
                db_url="sqlite+aiosqlite:///test.db",
                old_backend=old_backend,
                new_backend=new_backend,
            )

        error_msg = str(exc_info.value)
        assert "SUPER_SECRET_KEY_BYTES" not in error_msg
        assert "master_key" not in error_msg


# ---------------------------------------------------------------------------
# US6: NULL encrypted column handling
# ---------------------------------------------------------------------------


class TestNullEncryptedColumn:
    """NULL encrypted column values are skipped silently without error or count."""

    async def test_null_event_data_is_skipped_silently(
        self, mocker, old_backend, new_backend
    ) -> None:
        """T010: NULL event_data row is skipped without error, not counted in rotated or skipped."""
        row = _FakeRow(
            id="evt1",
            app_name="app1",
            user_id="u1",
            session_id="s1",
            event_data=None,
        )
        execute_fn = _make_execute_fn(
            mocker,
            select_rows_by_table={"events": [row]},
            update_rowcount=0,
        )
        _setup_mock_engine(mocker, execute_fn)

        result = await rotate_encryption_keys(
            db_url="sqlite+aiosqlite:///test.db",
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert result.rotated == 0
        assert result.skipped == 0
        old_backend.sync_decrypt.assert_not_called()
