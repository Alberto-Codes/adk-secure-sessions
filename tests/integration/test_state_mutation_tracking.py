"""Integration tests for in-place state mutation tracking.

google-adk 2.4.0+ applies state deltas by mutating the loaded ORM row's
``state`` dict in place (``storage_session.state.update(delta)``) rather than
reassigning the attribute. SQLAlchemy only detects that if the ``state``
attribute is registered with ``MutableDict`` (we use
``MutableDict.associate_with_attribute``). These tests exercise that contract
directly against our encrypted models, independent of which ADK version is
installed, so a regression shows up on every matrix cell.

See Also:
    [`adk_secure_sessions.services.models.create_encrypted_models`][adk_secure_sessions.services.models.create_encrypted_models]:
    Where the ``MutableDict`` association lives.
"""

from __future__ import annotations

import sqlite3

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
        self, encrypted_service: EncryptedSessionService, db_path: str
    ) -> None:
        """A dict.update() on the loaded session row survives commit and reload.

        The re-encrypted value must also be ciphertext at rest: the in-place
        path is a new database write path and must go through the same
        ``EncryptedJSON`` boundary as every other write.
        """
        created = await encrypted_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, state={"count": 0}
        )
        schema = encrypted_service._get_schema_classes()

        async with encrypted_service.database_session_factory() as sql_session:
            row = await sql_session.get(
                schema.StorageSession, (APP_NAME, USER_ID, created.id)
            )
            assert row is not None
            row.state.update({"count": 5, "new_key": "added-in-place"})
            await sql_session.commit()

        reloaded = await encrypted_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=created.id
        )
        assert reloaded is not None
        assert reloaded.state == {"count": 5, "new_key": "added-in-place"}

        # Tokens carry "_" or "-", which the base64 ciphertext alphabet lacks,
        # so a match can only mean plaintext leaked.
        conn = sqlite3.connect(db_path)
        raw = conn.execute("SELECT state FROM sessions").fetchone()[0]
        conn.close()
        assert isinstance(raw, str)
        assert "new_key" not in raw
        assert "added-in-place" not in raw

    async def test_app_and_user_state_in_place_update_persists(
        self, encrypted_service: EncryptedSessionService, db_path: str
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
            app_row.state.update({"ui_theme": "dark-mode"})
            user_row.state.update({"lang_pref": "en-US"})
            await sql_session.commit()

        async with encrypted_service.database_session_factory() as sql_session:
            app_state = (
                await sql_session.execute(select(schema.StorageAppState.state))
            ).scalar_one()
            user_state = (
                await sql_session.execute(select(schema.StorageUserState.state))
            ).scalar_one()

        assert app_state == {"ui_theme": "dark-mode"}
        assert user_state == {"lang_pref": "en-US"}

        conn = sqlite3.connect(db_path)
        raw_app = conn.execute("SELECT state FROM app_states").fetchone()[0]
        raw_user = conn.execute("SELECT state FROM user_states").fetchone()[0]
        conn.close()
        for raw, words in (
            (raw_app, ("ui_theme", "dark-mode")),
            (raw_user, ("lang_pref", "en-US")),
        ):
            assert isinstance(raw, str)
            for word in words:
                assert word not in raw
