"""Integration tests for in-place state mutation tracking.

google-adk 2.4.0+ applies state deltas by mutating the loaded ORM row's
``state`` dict in place (``storage_session.state.update(delta)``) rather than
reassigning the attribute. SQLAlchemy only detects that if the column type is
wrapped in ``MutableDict.as_mutable``. These tests exercise that contract
directly against our encrypted models, independent of which ADK version is
installed, so a regression shows up on every matrix cell.

See Also:
    [`adk_secure_sessions.services.models.create_encrypted_models`][adk_secure_sessions.services.models.create_encrypted_models]:
    Where the ``MutableDict`` wrapping lives.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from adk_secure_sessions import EncryptedSessionService

pytestmark = pytest.mark.integration

APP_NAME = "mutation_app"
"""Shared app name for every row created in this module."""

USER_ID = "user-1"
"""Shared user id for every row created in this module."""


class TestInPlaceStateMutationPersists:
    """AC4: Mutating a loaded row's state dict in place is persisted."""

    async def test_session_state_in_place_update_persists(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """A dict.update() on the loaded session row survives commit and reload."""
        created = await encrypted_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, state={"count": 0}
        )
        schema = encrypted_service._get_schema_classes()

        async with encrypted_service.database_session_factory() as sql_session:
            row = await sql_session.get(
                schema.StorageSession, (APP_NAME, USER_ID, created.id)
            )
            assert row is not None
            row.state.update({"count": 5, "new_key": "added"})
            await sql_session.commit()

        reloaded = await encrypted_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=created.id
        )
        assert reloaded is not None
        assert reloaded.state == {"count": 5, "new_key": "added"}

    async def test_app_and_user_state_in_place_update_persists(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """In-place updates on app_states and user_states rows are persisted."""
        await encrypted_service.create_session(app_name=APP_NAME, user_id=USER_ID)
        schema = encrypted_service._get_schema_classes()

        async with encrypted_service.database_session_factory() as sql_session:
            app_row = await sql_session.get(schema.StorageAppState, APP_NAME)
            user_row = await sql_session.get(
                schema.StorageUserState, (APP_NAME, USER_ID)
            )
            assert app_row is not None
            assert user_row is not None
            app_row.state.update({"theme": "dark"})
            user_row.state.update({"lang": "en"})
            await sql_session.commit()

        async with encrypted_service.database_session_factory() as sql_session:
            app_state = (
                await sql_session.execute(select(schema.StorageAppState.state))
            ).scalar_one()
            user_state = (
                await sql_session.execute(select(schema.StorageUserState.state))
            ).scalar_one()

        assert app_state == {"theme": "dark"}
        assert user_state == {"lang": "en"}
