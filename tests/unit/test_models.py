"""Unit tests for encrypted ORM model methods.

Tests ``EncryptedStorageSession.get_update_marker()``,
``update_timestamp_tz``, and ``to_session()`` marker stamping
without touching a database.

Typical usage::

    uv run pytest tests/unit/test_models.py -v
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import JSON

from adk_secure_sessions.services.models import create_encrypted_models


@pytest.fixture(scope="module")
def schema():
    """Create model classes with a real JSON column type."""
    _, schema = create_encrypted_models(JSON())
    return schema


@pytest.fixture
def make_session(schema):
    """Factory for EncryptedStorageSession with a given update_time."""

    def _make(update_time: datetime) -> object:
        return schema.StorageSession(
            app_name="test-app",
            user_id="user-1",
            id="session-1",
            state={},
            create_time=update_time,
            update_time=update_time,
        )

    return _make


# =============================================================================
# get_update_marker()
# =============================================================================


class TestGetUpdateMarker:
    """Unit tests for EncryptedStorageSession.get_update_marker()."""

    def test_naive_datetime_returns_iso_string(self, make_session):
        """AC1: Naive datetime returns ISO 8601 with microsecond precision."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)

        result = session.get_update_marker()

        assert result == "2026-03-28T12:00:00.123456"

    def test_tz_aware_datetime_normalizes_to_utc(self, make_session):
        """AC2: Timezone-aware datetime is converted to UTC."""
        utc_plus_5 = timezone(timedelta(hours=5))
        dt = datetime(2026, 3, 28, 17, 0, 0, 0, tzinfo=utc_plus_5)
        session = make_session(dt)

        result = session.get_update_marker()

        # 17:00 UTC+5 == 12:00 UTC
        assert result == "2026-03-28T12:00:00.000000+00:00"

    def test_utc_datetime_preserves_value(self, make_session):
        """UTC-aware datetime passes through unchanged."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 500000, tzinfo=timezone.utc)
        session = make_session(dt)

        result = session.get_update_marker()

        assert result == "2026-03-28T12:00:00.500000+00:00"

    def test_behavioral_equivalence_with_known_input(self, make_session):
        """AC4a: Output matches the upstream formula for a known input."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)

        result = session.get_update_marker()

        # Upstream formula: dt.isoformat(timespec="microseconds")
        assert result == dt.isoformat(timespec="microseconds")

    def test_zero_microseconds(self, make_session):
        """Microsecond field is always present even when zero."""
        dt = datetime(2026, 1, 1, 0, 0, 0, 0)
        session = make_session(dt)

        result = session.get_update_marker()

        assert result == "2026-01-01T00:00:00.000000"


# =============================================================================
# update_timestamp_tz
# =============================================================================


class TestUpdateTimestampTz:
    """Unit tests for EncryptedStorageSession.update_timestamp_tz property."""

    def test_returns_float_timestamp(self, make_session):
        """AC7: update_timestamp_tz returns a POSIX float."""
        dt = datetime(2026, 3, 28, 12, 0, 0, tzinfo=timezone.utc)
        session = make_session(dt)

        result = session.update_timestamp_tz

        assert isinstance(result, float)

    def test_matches_get_update_timestamp_non_sqlite(self, make_session):
        """AC7: Equivalent to get_update_timestamp(is_sqlite=False)."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456, tzinfo=timezone.utc)
        session = make_session(dt)

        assert session.update_timestamp_tz == session.get_update_timestamp(
            is_sqlite=False
        )

    def test_naive_datetime_delegates_correctly(self, make_session):
        """Naive datetime (SQLite production path) delegates to non-SQLite path."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)

        assert session.update_timestamp_tz == session.get_update_timestamp(
            is_sqlite=False
        )


# =============================================================================
# get_update_timestamp() — dialect flags are signature parity only
# =============================================================================


class TestGetUpdateTimestamp:
    """Unit tests for EncryptedStorageSession.get_update_timestamp()."""

    def test_accepts_is_postgresql_keyword(self, make_session):
        """AC1: is_postgresql (google-adk >= 2.4.0) is accepted, not rejected."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)

        result = session.get_update_timestamp(is_sqlite=False, is_postgresql=True)

        assert isinstance(result, float)

    def test_naive_datetime_is_interpreted_as_utc(self, make_session):
        """AC2: Naive datetime is treated as UTC regardless of dialect flags."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)
        expected = dt.replace(tzinfo=timezone.utc).timestamp()

        assert session.get_update_timestamp() == expected
        assert session.get_update_timestamp(is_sqlite=True) == expected
        assert session.get_update_timestamp(is_postgresql=True) == expected

    def test_tz_aware_datetime_is_converted_directly(self, make_session):
        """AC2: Timezone-aware datetime keeps its own offset."""
        dt = datetime(
            2026, 3, 28, 12, 0, 0, 123456, tzinfo=timezone(timedelta(hours=5))
        )
        session = make_session(dt)

        assert session.get_update_timestamp() == dt.timestamp()
        assert session.get_update_timestamp(is_sqlite=True) == dt.timestamp()


# =============================================================================
# _dialect_name — read by google-adk 1.22.0 through 1.25.x
# =============================================================================


class TestDialectName:
    """Unit tests for the EncryptedStorageSession._dialect_name property."""

    def test_detached_instance_returns_none(self, make_session):
        """AC3: A row not attached to any ORM session reports no dialect."""
        session = make_session(datetime(2026, 3, 28, 12, 0, 0))

        assert session._dialect_name is None

    def test_property_exists_on_class(self, schema):
        """AC3: google-adk 1.22.0 append_event() reads this attribute."""
        assert isinstance(
            inspect.getattr_static(schema.StorageSession, "_dialect_name"), property
        )


# =============================================================================
# to_session() — _storage_update_marker stamping
# =============================================================================


class TestToSessionMarker:
    """Unit tests for _storage_update_marker stamping in to_session()."""

    def test_to_session_sets_storage_update_marker(self, make_session):
        """AC3: to_session() sets _storage_update_marker on returned Session."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        storage_session = make_session(dt)

        session = storage_session.to_session(
            state={"key": "value"},
            events=[],
            is_sqlite=True,
        )

        assert session._storage_update_marker == storage_session.get_update_marker()

    def test_to_session_accepts_is_postgresql_keyword(self, make_session):
        """AC1: to_session(is_postgresql=...) matches the upstream call site."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        storage_session = make_session(dt)

        session = storage_session.to_session(
            state={"key": "value"},
            events=[],
            is_sqlite=False,
            is_postgresql=True,
        )

        assert session.id == "session-1"
        assert session.state == {"key": "value"}
        assert session.last_update_time == storage_session.get_update_timestamp()
        assert session._storage_update_marker == storage_session.get_update_marker()

    def test_marker_matches_iso_format(self, make_session):
        """Marker value matches the ISO 8601 microsecond format."""
        dt = datetime(2026, 3, 28, 15, 30, 45, 678901)
        storage_session = make_session(dt)

        session = storage_session.to_session()

        assert session._storage_update_marker == "2026-03-28T15:30:45.678901"
