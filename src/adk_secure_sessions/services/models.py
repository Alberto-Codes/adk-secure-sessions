"""Encrypted SQLAlchemy ORM models for session storage.

Mirrors ADK's database schema but replaces ``DynamicJSON`` columns with
``EncryptedJSON`` for transparent field-level encryption. Uses a factory
function that creates a fresh ``DeclarativeBase`` per call to avoid
metadata conflicts between multiple service instances.

The three ``state`` columns are mutation-tracked with
``MutableDict.associate_with_attribute``. google-adk 2.4.0+ applies state
deltas by mutating the loaded dict in place
(``storage_session.state.update(delta)``); without change tracking SQLAlchemy
never issues the UPDATE and the delta is silently lost. Attribute-level
association is used instead of ``MutableDict.as_mutable`` because the latter
installs process-global mapper listeners that are never garbage collected and
would retain each service's ``EncryptedJSON`` (and thus its key material).

Timestamp storage follows the installed google-adk release. Event timestamps
are stored as naive UTC from 2.7.0 (``schemas.shared.timestamp_to_utc_datetime``)
and as naive local time before that, matching the ``after_timestamp`` filter
upstream builds in ``get_session``. Naive ``update_time`` values are read as
UTC from 2.4.0 and, for non-SQLite dialects, as local time before that.

This module is an internal implementation detail and is NOT exported
in the public API.

Examples:
    Create encrypted model classes with an EncryptedJSON instance:

    ```python
    from adk_secure_sessions.services.models import create_encrypted_models

    base, models = create_encrypted_models(encrypted_json_type)
    ```

See Also:
    [`adk_secure_sessions.services.type_decorator`][adk_secure_sessions.services.type_decorator]:
    EncryptedJSON TypeDecorator used by these models.
"""

from __future__ import annotations

import inspect as _py_inspect
import uuid
from datetime import datetime, timezone
from typing import Any

from google.adk.events.event import Event
from google.adk.sessions.schemas import shared as _adk_shared
from google.adk.sessions.schemas.v1 import StorageSession as _UpstreamStorageSession
from google.adk.sessions.session import Session
from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    String,
    func,
    inspect,
)
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from adk_secure_sessions.services.type_decorator import EncryptedJSON

_DEFAULT_MAX_KEY_LENGTH = 128
"""Maximum length for key columns (matches ADK's default)."""

_DEFAULT_MAX_VARCHAR_LENGTH = 1024
"""Maximum length for varchar columns (matches ADK's default)."""

_shared_to_utc = getattr(_adk_shared, "timestamp_to_utc_datetime", None)
"""Upstream POSIX-to-naive-UTC helper (google-adk >= 2.7.0), else None."""

_shared_from_utc = getattr(_adk_shared, "utc_datetime_to_timestamp", None)
"""Upstream naive-UTC-to-POSIX helper (google-adk >= 2.7.0), else None."""

_EVENT_TIMESTAMPS_ARE_UTC = _shared_to_utc is not None and _shared_from_utc is not None
"""Whether event timestamps are stored as naive UTC (google-adk >= 2.7.0).

Older releases store naive local time and filter ``after_timestamp`` with
``datetime.fromtimestamp(...)``; storing UTC there would shift the filter.
"""


def _event_timestamp_to_storage(timestamp: float) -> datetime:
    """Convert an ``Event.timestamp`` float to the datetime upstream would store.

    Delegates to ``schemas.shared.timestamp_to_utc_datetime`` on google-adk
    >= 2.7.0 (naive UTC). Before that, mirrors the older
    ``StorageEvent.from_event`` (naive local time).

    Args:
        timestamp: POSIX timestamp from ``Event.timestamp``.

    Returns:
        Naive datetime in the convention the installed google-adk expects.
    """
    if _shared_to_utc is not None:
        return _shared_to_utc(timestamp)
    return datetime.fromtimestamp(timestamp)  # noqa: DTZ006


def _storage_to_event_timestamp(value: datetime) -> float:
    """Convert a stored ``timestamp`` column value back to a POSIX float.

    Inverse of ``_event_timestamp_to_storage``.

    Args:
        value: Naive datetime as read from the ``timestamp`` column.

    Returns:
        POSIX timestamp under the same convention the value was stored with.
    """
    if _shared_from_utc is not None:
        return _shared_from_utc(value)
    return value.timestamp()


def _upstream_reads_naive_update_time_as_utc() -> bool:
    """Report whether upstream treats naive ``update_time`` values as UTC.

    google-adk 2.4.0 rewrote ``StorageSession.get_update_timestamp`` to decide
    on ``tzinfo`` alone (naive means UTC) and added the ``is_postgresql``
    parameter in the same change. Earlier releases wrote naive *local* time
    for non-SQLite dialects and read it back with ``.timestamp()``.

    Returns:
        True when the installed upstream uses the tzinfo-based convention.
    """
    method = getattr(_UpstreamStorageSession, "get_update_timestamp", None)
    if method is None:
        return False
    return "is_postgresql" in _py_inspect.signature(method).parameters


_NAIVE_UPDATE_TIME_IS_UTC = _upstream_reads_naive_update_time_as_utc()
"""Whether a naive ``update_time`` is UTC (google-adk >= 2.4.0) or local."""


class _EncryptedSchemaClasses:
    """Duck-typed replacement for ADK's ``_SchemaClasses``.

    Holds references to the four encrypted model classes, matching the
    attribute names that ``DatabaseSessionService`` CRUD methods expect.

    Attributes:
        StorageSession (type): Encrypted session model class.
        StorageAppState (type): Encrypted app state model class.
        StorageUserState (type): Encrypted user state model class.
        StorageEvent (type): Encrypted event model class.

    Examples:
        Access model classes:

        ```python
        schema = _EncryptedSchemaClasses(session_cls, app_cls, user_cls, event_cls)
        obj = schema.StorageSession(app_name="test", user_id="u1")
        ```
    """

    def __init__(
        self,
        storage_session: type,
        storage_app_state: type,
        storage_user_state: type,
        storage_event: type,
    ) -> None:
        """Initialize with model class references.

        Args:
            storage_session: Encrypted session model class.
            storage_app_state: Encrypted app state model class.
            storage_user_state: Encrypted user state model class.
            storage_event: Encrypted event model class.
        """
        self.StorageSession = storage_session
        self.StorageAppState = storage_app_state
        self.StorageUserState = storage_user_state
        self.StorageEvent = storage_event


def create_encrypted_models(
    encrypted_json: EncryptedJSON,
) -> tuple[type[DeclarativeBase], _EncryptedSchemaClasses]:
    """Create encrypted ORM model classes bound to an EncryptedJSON instance.

    Creates a fresh ``DeclarativeBase`` subclass and four model classes
    per call, avoiding metadata conflicts between multiple service
    instances. Table names match ADK's schema exactly: ``sessions``,
    ``app_states``, ``user_states``, ``events``. The three ``state``
    attributes are registered with ``MutableDict.associate_with_attribute``
    after class creation so in-place mutation is tracked without any
    process-global listener.

    Args:
        encrypted_json: Configured EncryptedJSON TypeDecorator instance.

    Returns:
        Tuple of (base_class, schema_classes) where base_class is the
        DeclarativeBase (needed for metadata.create_all) and
        schema_classes is a duck-typed _SchemaClasses.

    Examples:
        ```python
        base, schema = create_encrypted_models(encrypted_json)
        await conn.run_sync(base.metadata.create_all)
        ```
    """

    class _Base(DeclarativeBase):
        pass

    class EncryptedStorageSession(_Base):
        """Encrypted session storage model.

        Duck-types ADK's ``StorageSession`` with encrypted state columns.
        The ``state`` attribute is ``MutableDict``-tracked so in-place delta
        application (google-adk >= 2.4.0) is persisted. Provides
        ``get_update_marker()`` and ``update_timestamp_tz`` for optimistic
        concurrency (google-adk >= 1.28.0), ``_dialect_name`` for
        google-adk 1.22.0 through 1.25.x, and a ``to_session()`` signature
        that accepts every dialect flag upstream passes.

        Examples:
            Created internally by ``create_encrypted_models``:

            ```python
            base, schema = create_encrypted_models(encrypted_json)
            obj = schema.StorageSession(app_name="app", user_id="u1")
            ```
        """

        __tablename__ = "sessions"

        app_name: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        user_id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
        )

        state: Mapped[dict[str, Any]] = mapped_column(encrypted_json, default=dict)

        create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())
        update_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now(), onupdate=func.now()
        )

        storage_events: Mapped[list[EncryptedStorageEvent]] = relationship(
            "EncryptedStorageEvent",
            back_populates="storage_session",
            cascade="all, delete-orphan",
        )

        @property
        def _dialect_name(self) -> str | None:
            """Dialect name of the engine this row is bound to.

            google-adk 1.22.0 through 1.25.x read this private property in
            ``append_event()`` to decide how to interpret ``update_time``.
            Later releases pass dialect flags explicitly instead.

            Returns:
                The SQLAlchemy dialect name (for example ``"sqlite"``), or
                ``None`` when the instance is detached from any session.
            """
            orm_session = inspect(self).session
            if orm_session is None or orm_session.bind is None:
                return None
            return orm_session.bind.dialect.name

        def to_session(
            self,
            state: dict[str, Any] | None = None,
            events: list[Event] | None = None,
            is_sqlite: bool = False,
            is_postgresql: bool = False,
        ) -> Session:
            """Convert to an ADK Session object.

            The ``is_sqlite`` and ``is_postgresql`` flags mirror the upstream
            ``StorageSession.to_session()`` signature. ADK passes them as
            keywords from ``DatabaseSessionService`` (``is_postgresql`` since
            google-adk 2.4.0), so both must be accepted even though the
            timestamp logic no longer depends on them.

            Args:
                state: Merged state dict (overrides stored state).
                events: List of Event objects.
                is_sqlite: Whether the backend is SQLite.
                is_postgresql: Whether the backend is PostgreSQL.

            Returns:
                ADK Session object with ``_storage_update_marker`` set for
                optimistic concurrency control.
            """
            if state is None:
                state = {}
            if events is None:
                events = []

            session = Session(
                app_name=self.app_name,
                user_id=self.user_id,
                id=self.id,
                state=state,
                events=events,
                last_update_time=self.get_update_timestamp(
                    is_sqlite=is_sqlite, is_postgresql=is_postgresql
                ),
            )
            session._storage_update_marker = self.get_update_marker()  # type: ignore[attr-defined]  # PrivateAttr added in ADK 1.28.0
            return session

        def get_update_timestamp(
            self, is_sqlite: bool = False, is_postgresql: bool = False
        ) -> float:
            """Get update time as a POSIX timestamp.

            Timezone-aware values are converted directly. Naive values are
            interpreted the way the installed google-adk wrote them: as UTC
            when the dialect is SQLite (by flag, or detected from the bound
            engine when no flag is given, as google-adk 1.22.0 through 1.25.x
            did), when ``is_postgresql`` is set, or on google-adk >= 2.4.0
            (which decides on ``tzinfo`` alone); as process-local time
            otherwise, matching the ``datetime.fromtimestamp(...)`` that
            google-adk < 2.4.0 wrote for non-SQLite dialects.

            Args:
                is_sqlite: Whether the backend is SQLite. When False and
                    ``is_postgresql`` is also False, the bound engine's
                    dialect is consulted instead.
                is_postgresql: Whether the backend is PostgreSQL (passed by
                    google-adk >= 2.4.0).

            Returns:
                Update time as a float POSIX timestamp.
            """
            update_time = self.update_time
            if update_time.tzinfo is not None:
                return update_time.timestamp()
            naive_is_utc = (
                is_sqlite
                or is_postgresql
                or _NAIVE_UPDATE_TIME_IS_UTC
                or self._dialect_name == "sqlite"
            )
            if naive_is_utc:
                return update_time.replace(tzinfo=timezone.utc).timestamp()
            return update_time.timestamp()

        @property
        def update_timestamp_tz(self) -> float:
            """The update time as a POSIX timestamp.

            Compatibility alias matching upstream ``StorageSession``. This is
            the only accessor google-adk 1.22.0 through 1.25.x call.

            Returns:
                POSIX timestamp. Equivalent to ``get_update_timestamp()``
                with no flags, which derives the dialect from the bound
                engine.
            """
            return self.get_update_timestamp()

        def get_update_marker(self) -> str:
            """Return a stable revision marker for optimistic concurrency checks.

            Produces an ISO 8601 timestamp string with microsecond precision,
            matching the upstream ``StorageSession.get_update_marker()``
            contract introduced in google-adk 1.28.0.

            Returns:
                ISO 8601 formatted update time (microsecond precision).
                Naive datetimes pass through as-is (assumed UTC from
                SQLite); tz-aware datetimes are normalized to UTC.
            """
            update_time = self.update_time
            if update_time.tzinfo is not None:
                update_time = update_time.astimezone(timezone.utc)
            return update_time.isoformat(timespec="microseconds")

        def __repr__(self) -> str:
            return f"<EncryptedStorageSession(id={self.id}, update_time={self.update_time})>"

    class EncryptedStorageAppState(_Base):
        """Encrypted app state storage model.

        The ``state`` attribute is ``MutableDict``-tracked so in-place delta
        application (google-adk >= 2.4.0) is persisted.

        Examples:
            Created internally by ``create_encrypted_models``:

            ```python
            base, schema = create_encrypted_models(encrypted_json)
            obj = schema.StorageAppState(app_name="app")
            ```
        """

        __tablename__ = "app_states"

        app_name: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        state: Mapped[dict[str, Any]] = mapped_column(encrypted_json, default=dict)
        update_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now(), onupdate=func.now()
        )

    class EncryptedStorageUserState(_Base):
        """Encrypted user state storage model.

        The ``state`` attribute is ``MutableDict``-tracked so in-place delta
        application (google-adk >= 2.4.0) is persisted.

        Examples:
            Created internally by ``create_encrypted_models``:

            ```python
            base, schema = create_encrypted_models(encrypted_json)
            obj = schema.StorageUserState(app_name="app", user_id="u1")
            ```
        """

        __tablename__ = "user_states"

        app_name: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        user_id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        state: Mapped[dict[str, Any]] = mapped_column(encrypted_json, default=dict)
        update_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now(), onupdate=func.now()
        )

    class EncryptedStorageEvent(_Base):
        """Encrypted event storage model.

        Examples:
            Created internally by ``create_encrypted_models``:

            ```python
            base, schema = create_encrypted_models(encrypted_json)
            event = schema.StorageEvent(
                id="e1",
                app_name="app",
                user_id="u1",
                session_id="s1",
                invocation_id="inv-1",
            )
            ```
        """

        __tablename__ = "events"

        id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        app_name: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        user_id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        session_id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )

        invocation_id: Mapped[str] = mapped_column(String(_DEFAULT_MAX_VARCHAR_LENGTH))
        timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
        event_data: Mapped[dict[str, Any] | None] = mapped_column(
            encrypted_json, nullable=True
        )

        storage_session: Mapped[EncryptedStorageSession] = relationship(
            "EncryptedStorageSession",
            back_populates="storage_events",
        )

        __table_args__ = (
            ForeignKeyConstraint(
                ["app_name", "user_id", "session_id"],
                ["sessions.app_name", "sessions.user_id", "sessions.id"],
                ondelete="CASCADE",
            ),
        )

        def to_event(self) -> Event:
            """Convert to an ADK Event object.

            Prefers the exact POSIX float preserved in ``event_data`` over the
            ``timestamp`` column, as upstream does: rebuilding an epoch from a
            naive datetime can resolve an ambiguous local time (a DST
            fall-back hour) to the wrong instant. The column is used only for
            rows whose payload lacks a timestamp.

            Returns:
                ADK Event object reconstructed from stored data.
            """
            data = self.event_data or {}
            timestamp = data.get("timestamp")
            if timestamp is None:
                timestamp = _storage_to_event_timestamp(self.timestamp)
            return Event.model_validate(
                {
                    **data,
                    "id": self.id,
                    "invocation_id": self.invocation_id,
                    "timestamp": timestamp,
                }
            )

        @classmethod
        def from_event(cls, session: Session, event: Event) -> EncryptedStorageEvent:
            """Create an EncryptedStorageEvent from an ADK Event.

            The event ``timestamp`` float is stored with the same convention
            the installed google-adk uses for its own ``StorageEvent``: naive
            UTC from 2.7.0, naive local time before that. Upstream's
            ``get_session`` builds its ``after_timestamp`` filter with that
            convention, so storing anything else silently drops or leaks
            events on hosts whose local timezone is not UTC.

            Args:
                session: The ADK Session that owns this event.
                event: The ADK Event to store.

            Returns:
                An EncryptedStorageEvent instance.
            """
            return EncryptedStorageEvent(
                id=event.id,
                invocation_id=event.invocation_id,
                session_id=session.id,
                app_name=session.app_name,
                user_id=session.user_id,
                timestamp=_event_timestamp_to_storage(event.timestamp),
                event_data=event.model_dump(exclude_none=True, mode="json"),
            )

    # Attribute-level association tracks in-place mutation of the three state
    # dicts without the process-global, never-collected mapper listeners that
    # MutableDict.as_mutable() would install for every service instance.
    for state_attr in (
        EncryptedStorageSession.state,
        EncryptedStorageAppState.state,
        EncryptedStorageUserState.state,
    ):
        MutableDict.associate_with_attribute(state_attr)

    schema = _EncryptedSchemaClasses(
        storage_session=EncryptedStorageSession,
        storage_app_state=EncryptedStorageAppState,
        storage_user_state=EncryptedStorageUserState,
        storage_event=EncryptedStorageEvent,
    )

    return _Base, schema
