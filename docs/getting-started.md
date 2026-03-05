# Getting Started

Add encrypted sessions to your ADK agent in under 5 minutes. This guide walks
you through installation, a full working example, and verification that your
session data is actually encrypted at rest.

## Prerequisites

- **Python 3.12+**
- An existing [Google ADK](https://github.com/google/adk-python) agent, or
  willingness to create a minimal one
- A terminal with `pip` or [uv](https://docs.astral.sh/uv/) available

## Installation

```bash
pip install adk-secure-sessions
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add adk-secure-sessions
```

This installs three runtime dependencies: `google-adk`, `cryptography`, and
`aiosqlite`.

## Quick Start

If you already have an ADK agent using `DatabaseSessionService`, the swap is
just two changes:

```python
# Before (unencrypted):
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")

# After (encrypted):
from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET
session_service = EncryptedSessionService(
    db_path="sessions.db",
    backend=FernetBackend("your-secret-key"),
    backend_id=BACKEND_FERNET,
)
```

The rest of your agent code stays the same — `create_session`, `get_session`,
`list_sessions`, `delete_session`, and `append_event` all work identically.

For the full picture, read on.

## Full Working Example

Copy this script, save it as `demo.py`, and run it with `python demo.py`:

```python
import asyncio

from cryptography.fernet import Fernet

from adk_secure_sessions import (
    BACKEND_FERNET,
    EncryptedSessionService,
    FernetBackend,
)


async def main() -> None:
    # Generate a proper Fernet key (in production, load from env / secrets manager)
    key = Fernet.generate_key().decode()

    backend = FernetBackend(key)

    async with EncryptedSessionService(
        db_path="getting_started.db",
        backend=backend,
        backend_id=BACKEND_FERNET,
    ) as service:
        # Create a session with realistic state
        session = await service.create_session(
            app_name="shopping-agent",
            user_id="user-42",
            state={
                "user_preferences": {"theme": "dark", "language": "en"},
                "cart_items": [
                    {"id": "prod-1", "name": "Widget", "qty": 2},
                    {"id": "prod-2", "name": "Gadget", "qty": 1},
                ],
                "last_active": "2026-03-04T10:30:00Z",
            },
        )
        print(f"Created session: {session.id}")

        # Retrieve the session — state is decrypted automatically
        retrieved = await service.get_session(
            app_name="shopping-agent",
            user_id="user-42",
            session_id=session.id,
        )
        assert retrieved is not None
        print(f"Retrieved state: {retrieved.state}")

        # Confirm round-trip fidelity
        assert retrieved.state["cart_items"][0]["name"] == "Widget"
        print("Round-trip verified — encryption is transparent.")


asyncio.run(main())
```

!!! tip "Key management"

    The example generates a random key for simplicity. In production, store your
    key in an environment variable or a secrets manager and load it at startup:

    ```python
    import os
    key = os.environ["SESSION_ENCRYPTION_KEY"]
    backend = FernetBackend(key)
    ```

## Verify Encryption

After running the example above, the SQLite file `getting_started.db` contains
your session — but the state is stored as encrypted bytes, not readable JSON.

Inspect it with Python (no extra tools needed):

```python
import sqlite3

conn = sqlite3.connect("getting_started.db")
row = conn.execute("SELECT state FROM sessions LIMIT 1").fetchone()
print(row[0][:20].hex())  # e.g. 0101674141...
conn.close()
```

Or, if you have the `sqlite3` CLI available:

```bash
sqlite3 getting_started.db "SELECT hex(substr(state, 1, 20)) FROM sessions LIMIT 1;"
```

Either way, you will see a hex string like `0101674141...` — not your plaintext
JSON. The first two bytes are the envelope header:

| Byte | Meaning | Value |
|------|---------|-------|
| 1 | Envelope version | `01` (version 1) |
| 2 | Backend ID | `01` (Fernet) |
| 3+ | Ciphertext | Fernet token (opaque) |

Session metadata (`session_id`, `app_name`, `user_id`) stays in plaintext so
that `list_sessions` can filter without decrypting every row. Only sensitive
payload fields are encrypted. See the
[Envelope Protocol](envelope-protocol.md) for the full binary layout.

## What's Next?

- **[API Reference](reference/index.md)** — full module, class, and function
  documentation
- **[Architecture Decisions](adr/index.md)** — why the library is designed the
  way it is
- **[FAQ](faq.md)** — common questions about algorithms, compliance, and
  custom backends
- **[Envelope Protocol](envelope-protocol.md)** — the binary wire format that
  tags every ciphertext with version and backend info

## Related

- [Algorithm Documentation](algorithms.md) — encryption algorithms, parameters, and NIST compliance mapping
- [Envelope Protocol](envelope-protocol.md) — binary envelope format and backend coexistence
- [FAQ](faq.md) — frequently asked questions
- [Roadmap](ROADMAP.md) — planned backends, features, and timeline
