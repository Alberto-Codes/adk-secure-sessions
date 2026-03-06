"""Example: Basic encrypted session usage.

Demonstrates the core UX of adk-secure-sessions: create an encrypted
session, store sensitive state, retrieve it, and verify that the raw
database contains only ciphertext -- not plaintext.

Prerequisites:
    - Python 3.12+
    - adk-secure-sessions installed (``pip install adk-secure-sessions``)

Usage:
    python examples/basic_usage.py

Examples:
    Run directly from the project root:

    ```bash
    uv run python examples/basic_usage.py
    ```

See Also:
    [`adk_secure_sessions.EncryptedSessionService`][]: Service class used here.
    [`adk_secure_sessions.FernetBackend`][]: Encryption backend used here.
"""

from __future__ import annotations

import asyncio
import sqlite3
import tempfile
from pathlib import Path

from adk_secure_sessions import EncryptedSessionService, FernetBackend


async def main() -> None:
    """Run the basic encrypted session example."""
    # -- Setup ----------------------------------------------------------------
    db_dir = Path(tempfile.mkdtemp())
    db_path = db_dir / "sessions.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    backend = FernetBackend("my-secret-passphrase")

    print("=" * 60)
    print("adk-secure-sessions: Basic Usage Example")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")
    print("Backend:  FernetBackend (Fernet symmetric encryption)")

    # -- Create an encrypted session ------------------------------------------
    print("\n--- Step 1: Create an encrypted session ---\n")

    async with EncryptedSessionService(db_url=db_url, backend=backend) as service:
        session = await service.create_session(
            app_name="demo-agent",
            user_id="user-42",
            state={
                "patient_name": "Jane Doe",
                "ssn": "123-45-6789",
                "diagnosis": "Common cold",
                "notes": "Patient prefers morning appointments",
            },
        )

        print(f"Session created: {session.id}")
        print(f"App:     {session.app_name}")
        print(f"User:    {session.user_id}")
        print(f"State:   {session.state}")

        # -- Retrieve the session ---------------------------------------------
        print("\n--- Step 2: Retrieve the session ---\n")

        retrieved = await service.get_session(
            app_name="demo-agent",
            user_id="user-42",
            session_id=session.id,
        )

        assert retrieved is not None
        print(f"Retrieved state: {retrieved.state}")
        print(f"Match: {retrieved.state == session.state}")

    # -- Inspect the raw database ---------------------------------------------
    print("\n--- Step 3: Inspect raw database (proof of encryption) ---\n")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT state FROM sessions LIMIT 1")
    raw_state = cursor.fetchone()
    conn.close()

    if raw_state and raw_state[0]:
        raw_value = raw_state[0]
        # Show first 80 chars of the raw ciphertext
        preview = raw_value[:80] if len(raw_value) > 80 else raw_value
        print(f"Raw DB value (truncated): {preview}...")
        print(f"Contains 'Jane Doe'?     {('Jane Doe' in str(raw_value))}")
        print(f"Contains '123-45-6789'?  {('123-45-6789' in str(raw_value))}")
    else:
        # State may be in app_states/user_states tables depending on ADK version
        cursor2 = sqlite3.connect(str(db_path))
        for table in ("app_states", "user_states"):
            row = cursor2.execute(
                f"SELECT state FROM {table} LIMIT 1"  # noqa: S608
            ).fetchone()
            if row and row[0]:
                preview = row[0][:80] if len(row[0]) > 80 else row[0]
                print(f"Raw {table} value (truncated): {preview}...")
                print(
                    f"Contains plaintext?      "
                    f"{('Jane Doe' in str(row[0]) or '123-45-6789' in str(row[0]))}"
                )
        cursor2.close()

    print("\n" + "=" * 60)
    print("Sensitive data is encrypted at rest.")
    print("Only the service with the correct key can read it.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
