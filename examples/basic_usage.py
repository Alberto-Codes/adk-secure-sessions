"""Example: Encrypted ADK agent with Ollama.

Runs a real ADK agent conversation through the Runner with encrypted
session storage. Demonstrates the full UX: agent responds to user
messages, state and conversation history are encrypted at rest, and
raw database inspection proves no plaintext leaks.

Prerequisites:
    - Python 3.12+
    - adk-secure-sessions installed (``pip install adk-secure-sessions``)
    - Ollama running locally with a model pulled
    - ``.env`` file or environment variables set (see below)

Environment variables:
    OLLAMA_API_BASE: Ollama server URL (e.g., ``http://localhost:11434``).
    OLLAMA_MODEL: Model to use (default: ``gemma3:4b``).

Examples:
    Run with defaults (expects ``.env`` file):

    ```bash
    uv run python examples/basic_usage.py
    ```

    Run with explicit env vars:

    ```bash
    OLLAMA_API_BASE=http://localhost:11434 uv run python examples/basic_usage.py
    ```

See Also:
    [`adk_secure_sessions.EncryptedSessionService`][]: Encrypted service.
    [`adk_secure_sessions.FernetBackend`][]: Encryption backend.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.genai import types

from adk_secure_sessions import EncryptedSessionService, FernetBackend

load_dotenv()

APP_NAME = "secure-demo"
USER_ID = "user-42"


def create_agent() -> LlmAgent:
    """Create a simple medical intake agent.

    Returns:
        LlmAgent configured for patient intake.
    """
    model_name = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    return LlmAgent(
        name="intake_agent",
        model=LiteLlm(model=f"ollama_chat/{model_name}"),
        instruction=(
            "You are a medical intake assistant. Collect the patient's "
            "name, date of birth, and reason for visit. Be brief and "
            "professional. After collecting info, summarize what you have."
        ),
    )


async def run_turn(
    runner: Runner,
    service: EncryptedSessionService,
    session_id: str,
    message: str,
) -> None:
    """Send a message and print the agent's response.

    Args:
        runner: ADK Runner instance.
        service: Encrypted session service.
        session_id: Active session ID.
        message: User message text.
    """
    print(f"\n  You: {message}")

    content = types.Content(parts=[types.Part(text=message)])
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"  Agent: {part.text}")


async def main() -> None:
    """Run a multi-turn agent conversation with encrypted sessions."""
    if not os.getenv("OLLAMA_API_BASE"):
        print("Error: OLLAMA_API_BASE not set.")
        print("Set it in .env or run:")
        print(
            "  OLLAMA_API_BASE=http://localhost:11434 uv run python examples/basic_usage.py"
        )
        return

    db_dir = Path(tempfile.mkdtemp())
    db_path = db_dir / "sessions.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    backend = FernetBackend("my-secret-passphrase")
    model_name = os.getenv("OLLAMA_MODEL", "gemma3:4b")

    print("=" * 60)
    print("adk-secure-sessions: Encrypted Agent Example")
    print("=" * 60)
    print(f"  Database: {db_path}")
    print(f"  Model:    ollama_chat/{model_name}")
    print("  Backend:  FernetBackend")

    # -- Run agent conversation -----------------------------------------------
    print("\n--- Agent Conversation (encrypted at rest) ---")

    async with EncryptedSessionService(db_url=db_url, backend=backend) as service:
        session = await service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
        )

        agent = create_agent()
        runner = Runner(
            agent=agent,
            app_name=APP_NAME,
            session_service=service,
        )

        await run_turn(runner, service, session.id, "Hi, I need to schedule a visit.")
        await run_turn(
            runner, service, session.id, "My name is Jane Doe, born 1985-03-15."
        )
        await run_turn(
            runner, service, session.id, "I've been having headaches for about a week."
        )

        # Show final session state
        retrieved = await service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session.id,
        )
        assert retrieved is not None
        print(f"\n  Events stored: {len(retrieved.events)}")

        await runner.close()

    # -- Inspect raw database -------------------------------------------------
    print("\n--- Raw Database Inspection (proof of encryption) ---\n")

    conn = sqlite3.connect(str(db_path))

    for table in ("sessions", "events"):
        col = "state" if table == "sessions" else "event_data"
        row = conn.execute(f"SELECT {col} FROM {table} LIMIT 1").fetchone()  # noqa: S608
        if row and row[0]:
            raw = row[0]
            preview = raw[:60] if len(raw) > 60 else raw
            print(f"  {table}.{col}: {preview}...")
            print(f"    Contains 'Jane Doe'?  {('Jane Doe' in str(raw))}")
            print(f"    Contains 'headache'?  {('headache' in str(raw))}")

    conn.close()

    print("\n" + "=" * 60)
    print("Conversation history is encrypted at rest.")
    print("Only the service with the correct key can read it.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
