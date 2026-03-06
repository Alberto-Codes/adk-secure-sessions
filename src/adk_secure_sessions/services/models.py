"""Encrypted SQLAlchemy ORM models for session storage.

Mirrors ADK's database schema but replaces ``DynamicJSON`` columns with
``EncryptedJSON`` for transparent field-level encryption. Uses a factory
function that creates a fresh ``DeclarativeBase`` per call to avoid
metadata conflicts between multiple service instances.

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

import uuid
from datetime import datetime
from typing import Any

from google.adk.events.event import Event
from google.adk.sessions.session import Session
from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    String,
    func,
)
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
    ``app_states``, ``user_states``, ``events``.

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
        """Encrypted session storage model."""

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

        state: Mapped[dict[str, Any]] = mapped_column(
            encrypted_json, default={}
        )

        create_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now()
        )
        update_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now(), onupdate=func.now()
        )

        storage_events: Mapped[list[EncryptedStorageEvent]] = relationship(
            "EncryptedStorageEvent",
            back_populates="storage_session",
            cascade="all, delete-orphan",
        )

        def to_session(
            self,
            state: dict[str, Any] | None = None,
            events: list[Event] | None = None,
            is_sqlite: bool = False,
        ) -> Session:
            """Convert to an ADK Session object.

            Args:
                state: Merged state dict (overrides stored state).
                events: List of Event objects.
                is_sqlite: Whether the backend is SQLite.

            Returns:
                ADK Session object.
            """
            if state is None:
                state = {}
            if events is None:
                events = []

            return Session(
                app_name=self.app_name,
                user_id=self.user_id,
                id=self.id,
                state=state,
                events=events,
                last_update_time=self.get_update_timestamp(is_sqlite=is_sqlite),
            )

        def get_update_timestamp(self, is_sqlite: bool = False) -> float:
            """Get update time as a POSIX timestamp.

            Args:
                is_sqlite: Whether the backend is SQLite (naive datetime).

            Returns:
                Update time as a float POSIX timestamp.
            """
            if is_sqlite:
                return self.update_time.replace(
                    tzinfo=__import__("datetime").timezone.utc
                ).timestamp()
            return self.update_time.timestamp()

        def __repr__(self) -> str:
            return f"<EncryptedStorageSession(id={self.id}, update_time={self.update_time})>"

    class EncryptedStorageAppState(_Base):
        """Encrypted app state storage model."""

        __tablename__ = "app_states"

        app_name: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        state: Mapped[dict[str, Any]] = mapped_column(
            encrypted_json, default={}
        )
        update_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now(), onupdate=func.now()
        )

    class EncryptedStorageUserState(_Base):
        """Encrypted user state storage model."""

        __tablename__ = "user_states"

        app_name: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        user_id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_KEY_LENGTH), primary_key=True
        )
        state: Mapped[dict[str, Any]] = mapped_column(
            encrypted_json, default={}
        )
        update_time: Mapped[datetime] = mapped_column(
            DateTime, default=func.now(), onupdate=func.now()
        )

    class EncryptedStorageEvent(_Base):
        """Encrypted event storage model."""

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

        invocation_id: Mapped[str] = mapped_column(
            String(_DEFAULT_MAX_VARCHAR_LENGTH)
        )
        timestamp: Mapped[datetime] = mapped_column(
            DateTime, default=func.now()
        )
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

            Returns:
                ADK Event object reconstructed from stored data.
            """
            data = self.event_data or {}
            return Event.model_validate({
                **data,
                "id": self.id,
                "invocation_id": self.invocation_id,
                "timestamp": self.timestamp.timestamp(),
            })

        @classmethod
        def from_event(
            cls, session: Session, event: Event
        ) -> EncryptedStorageEvent:
            """Create an EncryptedStorageEvent from an ADK Event.

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
                timestamp=datetime.fromtimestamp(event.timestamp),
                event_data=event.model_dump(exclude_none=True, mode="json"),
            )

    schema = _EncryptedSchemaClasses(
        storage_session=EncryptedStorageSession,
        storage_app_state=EncryptedStorageAppState,
        storage_user_state=EncryptedStorageUserState,
        storage_event=EncryptedStorageEvent,
    )

    return _Base, schema
