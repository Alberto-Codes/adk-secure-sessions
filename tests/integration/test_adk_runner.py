"""Integration tests for EncryptedSessionService as ADK Runner drop-in.

Verifies that ``EncryptedSessionService`` works as a genuine
``BaseSessionService`` drop-in by passing it to an actual ``Runner``
instance and executing agent turns through ``Runner.run_async()``.

This is the definitive NFR20 verification — real execution through
the ADK pipeline, not just ``isinstance`` checks.

Typical usage::

    uv run pytest tests/integration/test_adk_runner.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]
    [`Runner`](https://google.github.io/adk-docs/)
"""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncGenerator

import pytest
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.genai import types

from adk_secure_sessions import EncryptedSessionService

pytestmark = pytest.mark.integration

APP_NAME = "test_app"
"""Shared constant — Runner and create_session MUST match."""


async def echo_callback(callback_context: object) -> types.Content:
    """Short-circuit LLM — returns content directly."""
    return types.Content(parts=[types.Part(text="Agent response")])


async def stateful_callback(callback_context: object) -> types.Content:
    """Short-circuit LLM with state mutation via callback_context.state."""
    callback_context.state["agent_ran"] = True  # type: ignore[union-attr]
    callback_context.state["agent_response_count"] = 1  # type: ignore[union-attr]
    return types.Content(parts=[types.Part(text="Stateful response")])


async def counting_callback(callback_context: object) -> types.Content:
    """Short-circuit LLM that increments a counter each turn."""
    current = callback_context.state.get("turn_count", 0)  # type: ignore[union-attr]
    callback_context.state["turn_count"] = current + 1  # type: ignore[union-attr]
    return types.Content(parts=[types.Part(text=f"Turn {current + 1}")])


@pytest.fixture
def _make_runner(
    encrypted_service: EncryptedSessionService,
) -> object:
    """Factory that creates a Runner with a given callback, with cleanup."""
    import contextlib
    from collections.abc import Callable

    @contextlib.asynccontextmanager
    async def factory(
        callback: Callable[..., object],
    ) -> AsyncGenerator[Runner, None]:
        agent = LlmAgent(
            name="test_agent",
            model="gemini-2.0-flash",
            before_agent_callback=callback,
        )
        r = Runner(
            agent=agent,
            app_name=APP_NAME,
            session_service=encrypted_service,
        )
        yield r
        await r.close()

    return factory


@pytest.fixture
async def runner(
    _make_runner: object,
) -> AsyncGenerator[Runner, None]:
    """Runner with echo callback agent, properly cleaned up."""
    async with _make_runner(echo_callback) as r:  # type: ignore[misc]
        yield r


@pytest.fixture
async def stateful_runner(
    _make_runner: object,
) -> AsyncGenerator[Runner, None]:
    """Runner with stateful callback agent, properly cleaned up."""
    async with _make_runner(stateful_callback) as r:  # type: ignore[misc]
        yield r


@pytest.fixture
async def counting_runner(
    _make_runner: object,
) -> AsyncGenerator[Runner, None]:
    """Runner with counting callback agent, properly cleaned up."""
    async with _make_runner(counting_callback) as r:  # type: ignore[misc]
        yield r


# --- Story 1.6a: ADK Runner Integration Test ---


class TestADKRunnerIntegration:
    """T049: EncryptedSessionService as ADK Runner drop-in."""

    async def test_runner_accepts_encrypted_service(
        self,
        encrypted_service: EncryptedSessionService,
    ) -> None:
        """Runner instantiates with EncryptedSessionService without error."""
        agent = LlmAgent(
            name="test_agent",
            model="gemini-2.0-flash",
            before_agent_callback=echo_callback,
        )
        runner = Runner(
            agent=agent,
            app_name=APP_NAME,
            session_service=encrypted_service,
        )
        assert runner is not None
        await runner.close()

    async def test_full_lifecycle_through_runner(
        self,
        runner: Runner,
        encrypted_service: EncryptedSessionService,
        db_path: str,
    ) -> None:
        """Create -> run turn -> get -> raw-DB encryption check -> delete."""
        # 1. Create session
        session = await encrypted_service.create_session(
            app_name=APP_NAME,
            user_id="test_user",
            state={"initial": "state"},
        )

        # 2. Run agent turn through Runner
        message = types.Content(parts=[types.Part(text="Hello")])
        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=message,
        ):
            events.append(event)

        assert len(events) > 0

        # 3. Get session and verify events persisted
        retrieved = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=session.id,
        )
        assert retrieved is not None
        assert len(retrieved.events) == 2  # Exactly 1 user + 1 agent event

        # Verify agent response content is present in events
        agent_texts = [
            part.text
            for event in retrieved.events
            for part in (event.content.parts if event.content else [])
            if hasattr(part, "text") and part.text
        ]
        assert "Agent response" in agent_texts

        # 4. Raw-DB encryption assertion (TEXT column, base64-encoded)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT state FROM sessions")
        row = cursor.fetchone()
        assert row is not None
        raw_state = row[0]
        assert isinstance(raw_state, str)
        assert "initial" not in raw_state

        # Verify event data is also encrypted in raw database
        evt_cursor = conn.execute("SELECT event_data FROM events")
        evt_rows = evt_cursor.fetchall()
        conn.close()
        assert len(evt_rows) > 0
        for evt_row in evt_rows:
            raw_event = evt_row[0]
            assert isinstance(raw_event, str)
            # No plaintext agent or user messages should be visible
            assert "Agent response" not in raw_event
            assert "Hello" not in raw_event
            # No obvious JSON structure markers
            assert '"author"' not in raw_event
            assert '"parts"' not in raw_event

        # 5. Delete session
        await encrypted_service.delete_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=session.id,
        )

        # 6. Verify deletion
        deleted = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=session.id,
        )
        assert deleted is None


class TestStateDeltas:
    """T050: State delta verification through Runner turn."""

    async def test_state_delta_persists_through_runner(
        self,
        stateful_runner: Runner,
        encrypted_service: EncryptedSessionService,
    ) -> None:
        """State changes via callback_context.state persist encrypted."""
        # Create session
        session = await encrypted_service.create_session(
            app_name=APP_NAME,
            user_id="test_user",
        )

        # Run agent turn that mutates state
        message = types.Content(parts=[types.Part(text="Do something")])
        async for _ in stateful_runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=message,
        ):
            pass

        # Retrieve and verify state was persisted
        retrieved = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state.get("agent_ran") is True
        assert retrieved.state.get("agent_response_count") == 1

    async def test_state_delta_is_encrypted_in_database(
        self,
        stateful_runner: Runner,
        encrypted_service: EncryptedSessionService,
        db_path: str,
    ) -> None:
        """State set through Runner turn is encrypted in raw database."""
        session = await encrypted_service.create_session(
            app_name=APP_NAME,
            user_id="test_user",
        )

        message = types.Content(parts=[types.Part(text="Do something")])
        async for _ in stateful_runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=message,
        ):
            pass

        # Raw DB should not contain plaintext state values
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT state FROM sessions")
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        raw_state = row[0]
        assert isinstance(raw_state, str)
        assert "agent_ran" not in raw_state
        assert "agent_response_count" not in raw_state


class TestMultiTurnConversation:
    """T051: Multi-turn conversation through Runner."""

    async def test_two_turns_produce_four_events(
        self,
        counting_runner: Runner,
        encrypted_service: EncryptedSessionService,
    ) -> None:
        """Two sequential turns produce exactly 4 events."""
        session = await encrypted_service.create_session(
            app_name=APP_NAME,
            user_id="test_user",
        )

        # Turn 1
        message_1 = types.Content(parts=[types.Part(text="First message")])
        async for _ in counting_runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=message_1,
        ):
            pass

        # Turn 2
        message_2 = types.Content(parts=[types.Part(text="Second message")])
        async for _ in counting_runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=message_2,
        ):
            pass

        # Retrieve session and verify event count
        retrieved = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=session.id,
        )
        assert retrieved is not None
        assert len(retrieved.events) == 4

    async def test_state_accumulates_across_turns(
        self,
        counting_runner: Runner,
        encrypted_service: EncryptedSessionService,
    ) -> None:
        """State counter increments correctly across multiple turns."""
        session = await encrypted_service.create_session(
            app_name=APP_NAME,
            user_id="test_user",
        )

        # Run two turns
        for i in range(2):
            message = types.Content(parts=[types.Part(text=f"Turn {i + 1}")])
            async for _ in counting_runner.run_async(
                user_id="test_user",
                session_id=session.id,
                new_message=message,
            ):
                pass

        # Verify accumulated state
        retrieved = await encrypted_service.get_session(
            app_name=APP_NAME,
            user_id="test_user",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state.get("turn_count") == 2
