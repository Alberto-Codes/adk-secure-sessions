"""Unit tests for encrypted ORM model methods.

Tests ``EncryptedStorageSession.get_update_marker()``,
``update_timestamp_tz``, and ``to_session()`` marker stamping
without touching a database.

Typical usage::

    uv run pytest tests/unit/test_models.py -v
"""

from __future__ import annotations

import inspect
import os
import time
from datetime import UTC, datetime, timedelta, timezone

import pytest
from google.adk.events.event import Event
from google.adk.sessions.session import Session
from sqlalchemy import JSON, create_engine
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import Session as OrmSession

from adk_secure_sessions.services.models import (
    _EVENT_TIMESTAMPS_ARE_UTC,
    _NAIVE_UPDATE_TIME_IS_UTC,
    create_encrypted_models,
)


@pytest.fixture
def new_york_tz():
    """Run the test with the process timezone set to America/New_York.

    Makes naive-local and naive-UTC datetimes differ by hours, so any code
    that confuses the two produces a visibly wrong value instead of passing
    by coincidence on UTC hosts such as CI runners. Only ``TZ`` is touched,
    and it is restored (and ``tzset`` re-run) even if the test fails.
    """
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset() is unavailable on this platform")
    previous = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"
    time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        time.tzset()


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
        dt = datetime(2026, 3, 28, 12, 0, 0, 500000, tzinfo=UTC)
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
        dt = datetime(2026, 3, 28, 12, 0, 0, tzinfo=UTC)
        session = make_session(dt)

        result = session.update_timestamp_tz

        assert isinstance(result, float)

    def test_matches_get_update_timestamp_non_sqlite(self, make_session):
        """AC7: Equivalent to get_update_timestamp(is_sqlite=False)."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456, tzinfo=UTC)
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

    def test_bound_sqlite_row_uses_sqlite_convention(self, make_session, new_york_tz):
        """AC7: When attached to a SQLite engine the naive value is read as UTC.

        google-adk 1.22.0 through 1.25.x call only this property and wrote
        naive UTC for SQLite, so a local-time reading would be hours off.
        """
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        row = make_session(dt)
        with OrmSession(create_engine("sqlite://")) as orm:
            orm.add(row)
            result = row.update_timestamp_tz

        assert result == dt.replace(tzinfo=UTC).timestamp()
        assert result == row.get_update_timestamp(is_sqlite=True)


# =============================================================================
# get_update_timestamp() — dialect flags are signature parity only
# =============================================================================


class TestGetUpdateTimestamp:
    """Unit tests for EncryptedStorageSession.get_update_timestamp()."""

    def test_accepts_is_postgresql_keyword(self, make_session):
        """AC1: is_postgresql (google-adk >= 2.4.0) is accepted and means UTC."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)

        result = session.get_update_timestamp(is_sqlite=False, is_postgresql=True)

        assert result == dt.replace(tzinfo=UTC).timestamp()

    def test_naive_datetime_with_dialect_flag_is_utc(self, make_session, new_york_tz):
        """AC2: Either dialect flag makes a naive value UTC on every ADK version."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)
        expected = dt.replace(tzinfo=UTC).timestamp()

        assert session.get_update_timestamp(is_sqlite=True) == expected
        assert session.get_update_timestamp(is_postgresql=True) == expected

    def test_naive_datetime_without_flags_follows_upstream(
        self, make_session, new_york_tz
    ):
        """AC2: With no flags, naive means whatever the installed ADK wrote.

        google-adk >= 2.4.0 writes and reads naive UTC for every dialect.
        Earlier releases wrote naive local time for non-SQLite dialects and
        read it back with ``.timestamp()``; interpreting that as UTC would
        shift ``last_update_time`` by the host's UTC offset.
        """
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        session = make_session(dt)
        if _NAIVE_UPDATE_TIME_IS_UTC:
            expected = dt.replace(tzinfo=UTC).timestamp()
        else:
            expected = dt.timestamp()

        assert session.get_update_timestamp() == expected
        assert expected != (
            dt.timestamp()
            if _NAIVE_UPDATE_TIME_IS_UTC
            else dt.replace(tzinfo=UTC).timestamp()
        ), "New York offset must make the two conventions distinguishable"

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

    def test_bound_instance_reports_engine_dialect(self, make_session):
        """AC3: Attached to a SQLite engine, the property reports ``sqlite``.

        This is the value google-adk 1.22.0 ``append_event()`` branches on.
        """
        row = make_session(datetime(2026, 3, 28, 12, 0, 0))
        with OrmSession(create_engine("sqlite://")) as orm:
            orm.add(row)
            assert row._dialect_name == "sqlite"

    def test_session_without_bind_returns_none(self, make_session):
        """AC3: An ORM session with no engine bound yields no dialect."""
        row = make_session(datetime(2026, 3, 28, 12, 0, 0))
        with OrmSession() as orm:
            orm.add(row)
            assert row._dialect_name is None

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
        assert session.last_update_time == storage_session.get_update_timestamp(
            is_sqlite=False, is_postgresql=True
        )
        assert session._storage_update_marker == storage_session.get_update_marker()

    def test_marker_matches_iso_format(self, make_session):
        """Marker value matches the ISO 8601 microsecond format."""
        dt = datetime(2026, 3, 28, 15, 30, 45, 678901)
        storage_session = make_session(dt)

        session = storage_session.to_session()

        assert session._storage_update_marker == "2026-03-28T15:30:45.678901"


# =============================================================================
# Mutation tracking — attribute-level, no global listeners
# =============================================================================


def _global_mapper_configured_listener_count() -> int:
    """Count process-global ``mapper_configured`` listeners on ``Mapper``.

    ``MutableDict.as_mutable`` adds one of these per call and never removes
    it; ``associate_with_attribute`` adds none.
    """
    return len(Mapper.dispatch.mapper_configured._clslevel[Mapper])


class TestMutationTracking:
    """State dicts are change-tracked without leaking global listeners."""

    def test_state_attribute_is_mutable_dict(self, make_session):
        """AC4: Assigning a dict to ``state`` coerces it to a MutableDict."""
        session = make_session(datetime(2026, 3, 28, 12, 0, 0))

        assert isinstance(session.state, MutableDict)

    def test_event_data_is_not_mutation_tracked(self, schema):
        """AC4: ``event_data`` stays a plain dict, matching upstream."""
        row = schema.StorageEvent(
            id="e1",
            app_name="test-app",
            user_id="user-1",
            session_id="session-1",
            invocation_id="inv-1",
            event_data={"author": "user"},
        )

        assert type(row.event_data) is dict

    def test_factory_installs_no_global_mapper_listeners(self):
        """AC4: Repeated factory calls do not grow process-global listeners.

        Global listeners would retain every service's ``EncryptedJSON`` and
        therefore its key material for the life of the process.
        """
        before = _global_mapper_configured_listener_count()

        for _ in range(5):
            create_encrypted_models(JSON())

        assert _global_mapper_configured_listener_count() == before


# =============================================================================
# Event timestamps — convention follows the installed google-adk
# =============================================================================


class TestEventTimestampRoundTrip:
    """from_event()/to_event() preserve the exact epoch on non-UTC hosts."""

    EPOCH = 1_700_000_000.123456
    """A fixed POSIX timestamp (2023-11-14T22:13:20.123456Z)."""

    @pytest.fixture
    def adk_session(self) -> Session:
        """An ADK Session shell for from_event()."""
        return Session(app_name="test-app", user_id="user-1", id="session-1")

    def test_round_trip_preserves_epoch(self, schema, adk_session, new_york_tz):
        """AC5: to_event(from_event(e)).timestamp == e.timestamp exactly."""
        event = Event(
            id="e1", invocation_id="inv-1", author="user", timestamp=self.EPOCH
        )

        row = schema.StorageEvent.from_event(adk_session, event)

        assert row.to_event().timestamp == self.EPOCH

    def test_stored_column_matches_upstream_convention(
        self, schema, adk_session, new_york_tz
    ):
        """AC5: The ``timestamp`` column uses upstream's storage convention.

        google-adk >= 2.7.0 filters ``after_timestamp`` against naive UTC;
        earlier releases against naive local time. Storing the other one
        silently drops or leaks events on non-UTC hosts.
        """
        event = Event(
            id="e1", invocation_id="inv-1", author="user", timestamp=self.EPOCH
        )

        row = schema.StorageEvent.from_event(adk_session, event)

        if _EVENT_TIMESTAMPS_ARE_UTC:
            expected = datetime.fromtimestamp(self.EPOCH, tz=UTC).replace(tzinfo=None)
        else:
            expected = datetime.fromtimestamp(self.EPOCH)
        assert row.timestamp == expected
        assert row.timestamp.tzinfo is None

    def test_to_event_falls_back_to_column_when_payload_lacks_timestamp(
        self, schema, adk_session, new_york_tz
    ):
        """AC5: Rows without a payload timestamp still reconstruct the epoch."""
        event = Event(
            id="e1", invocation_id="inv-1", author="user", timestamp=self.EPOCH
        )
        row = schema.StorageEvent.from_event(adk_session, event)
        row.event_data = {k: v for k, v in row.event_data.items() if k != "timestamp"}

        assert row.to_event().timestamp == self.EPOCH
