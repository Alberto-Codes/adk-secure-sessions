"""Integration tests for event timestamp handling on non-UTC hosts.

google-adk stores event timestamps as naive datetimes and builds the
``after_timestamp`` filter in ``get_session()`` from a naive datetime too.
The convention changed in google-adk 2.7.0 (naive local -> naive UTC). If our
``EncryptedStorageEvent`` stores the other convention, events silently vanish
or leak around the cutoff on any host whose local timezone is not UTC. CI
runners are UTC, so these tests force a timezone with ``time.tzset()``.

See Also:
    [`adk_secure_sessions.services.models`][adk_secure_sessions.services.models]:
    Where the version-aware conversion lives.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest
from google.adk.events.event import Event
from google.adk.sessions.base_session_service import GetSessionConfig

from adk_secure_sessions import EncryptedSessionService

pytestmark = pytest.mark.integration

APP_NAME = "tz_app"
"""Shared app name for every row created in this module."""

USER_ID = "user-1"
"""Shared user id for every row created in this module."""

T0 = 1_700_000_000.0
"""First event timestamp (2023-11-14T22:13:20Z)."""

T1 = T0 + 3600.0
"""Second event timestamp, one hour after the first."""


@pytest.fixture(params=["America/New_York", "Asia/Tokyo"])
def process_timezone(request, monkeypatch) -> Iterator[str]:
    """Run the test under a fixed non-UTC process timezone, west and east.

    A wrong convention loses events west of UTC and leaks them east of it,
    so both directions are exercised.
    """
    monkeypatch.setenv("TZ", request.param)
    time.tzset()
    yield request.param
    monkeypatch.undo()
    time.tzset()


async def _seed_two_events(service: EncryptedSessionService):
    """Create a session and append events at T0 and T1."""
    session = await service.create_session(app_name=APP_NAME, user_id=USER_ID)
    for idx, ts in enumerate((T0, T1)):
        await service.append_event(
            session,
            Event(
                id=f"e{idx}", invocation_id=f"inv-{idx}", author="user", timestamp=ts
            ),
        )
    return session


class TestAfterTimestampFilter:
    """AC5: ``after_timestamp`` selects exactly the events after the cutoff."""

    async def test_cutoff_between_events_returns_only_later_one(
        self, encrypted_service: EncryptedSessionService, process_timezone: str
    ) -> None:
        """Events at T0 and T1 with cutoff T0+1 -> only T1 comes back."""
        session = await _seed_two_events(encrypted_service)

        fetched = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session.id,
            config=GetSessionConfig(after_timestamp=T0 + 1),
        )

        assert fetched is not None
        assert [e.timestamp for e in fetched.events] == [T1]

    async def test_cutoff_before_events_returns_both(
        self, encrypted_service: EncryptedSessionService, process_timezone: str
    ) -> None:
        """Cutoff one minute before T0 -> both events, exact timestamps."""
        session = await _seed_two_events(encrypted_service)

        fetched = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session.id,
            config=GetSessionConfig(after_timestamp=T0 - 60),
        )

        assert fetched is not None
        assert sorted(e.timestamp for e in fetched.events) == [T0, T1]

    async def test_cutoff_after_events_returns_none(
        self, encrypted_service: EncryptedSessionService, process_timezone: str
    ) -> None:
        """Cutoff one hour after T1 -> no events leak through."""
        session = await _seed_two_events(encrypted_service)

        fetched = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session.id,
            config=GetSessionConfig(after_timestamp=T1 + 3600),
        )

        assert fetched is not None
        assert fetched.events == []

    async def test_unfiltered_round_trip_preserves_exact_timestamps(
        self, encrypted_service: EncryptedSessionService, process_timezone: str
    ) -> None:
        """Without a filter, both events come back with their exact epochs."""
        session = await _seed_two_events(encrypted_service)

        fetched = await encrypted_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session.id
        )

        assert fetched is not None
        assert sorted(e.timestamp for e in fetched.events) == [T0, T1]
