# Getting Started

This guide takes you from install to encrypted sessions in under 5 minutes.
By the end, you'll have a working async script that creates, retrieves, lists,
and deletes encrypted sessions — and you'll verify the encryption by inspecting
the raw database.

## Installation

Install from PyPI:

```bash
pip install adk-secure-sessions
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add adk-secure-sessions
```

**2 direct runtime dependencies**: google-adk, cryptography.

Verify the install:

```bash
python -c "import adk_secure_sessions; print('OK')"
```

Check the installed version:

```bash
python -c "from importlib.metadata import version; print(version('adk-secure-sessions'))"
```

## Quick Start

If you already have an ADK agent using `DatabaseSessionService`, the swap is
just two changes:

```python
# Before (ADK default — unencrypted):
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///sessions.db")

# After (encrypted — swap the import and constructor):
from adk_secure_sessions import EncryptedSessionService, FernetBackend
session_service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db",
    backend=FernetBackend("your-secret-passphrase"),
)
```

Use `session_service` exactly like any ADK session service — `create_session`,
`get_session`, `list_sessions`, and `delete_session` all work the same way.

## Full Working Example

The script below demonstrates the complete `EncryptedSessionService` lifecycle:
create a session with sensitive data, retrieve it, list sessions, and clean up.
Copy it into a file and run it directly.

<!-- test:exec:getting-started-full-example -->
```python
import asyncio

from adk_secure_sessions import (
    EncryptedSessionService,
    FernetBackend,
)


async def main():
    backend = FernetBackend("my-secret-passphrase")

    async with EncryptedSessionService(
        db_url="sqlite+aiosqlite:///sessions.db",
        backend=backend,
    ) as service:
        # Create a session with realistic sensitive state
        session = await service.create_session(
            app_name="my-agent",
            user_id="user-123",
            state={
                "patient_name": "Jane Doe",
                "diagnosis_code": "J06.9",
                "api_key": "sk-secret-key-12345",
            },
        )
        print(f"Created session: {session.id}")

        # Retrieve the session — state is automatically decrypted
        session = await service.get_session(
            app_name="my-agent",
            user_id="user-123",
            session_id=session.id,
        )
        print(f"Decrypted state: {session.state}")

        # List all sessions for this app/user
        response = await service.list_sessions(
            app_name="my-agent",
            user_id="user-123",
        )
        print(f"Sessions found: {len(response.sessions)}")

        # Clean up
        await service.delete_session(
            app_name="my-agent",
            user_id="user-123",
            session_id=session.id,
        )
        print("Session deleted")


asyncio.run(main())
```

!!! warning "Never hardcode secrets in production"

    In production, load your passphrase from an environment variable or secret
    manager (`os.environ["ENCRYPTION_KEY"]`). Never hardcode secrets in source
    code.

## Verify Encryption

After running the example above (comment out the `delete_session` call first to
keep the data), inspect the SQLite database to confirm state is encrypted.

**Using the `sqlite3` CLI:**

```bash
sqlite3 sessions.db "SELECT state FROM sessions LIMIT 1;"
```

You'll see a base64-encoded string — the encrypted envelope — not readable JSON.

**Using Python's `sqlite3` module:**

```python
import sqlite3

conn = sqlite3.connect("sessions.db")
row = conn.execute("SELECT state FROM sessions LIMIT 1").fetchone()
print(type(row[0]))  # <class 'str'>
print(row[0][:40])   # First 40 chars of base64-encoded envelope
conn.close()
```

The `state` column contains a base64-encoded encrypted envelope, not plaintext
JSON. By contrast, ADK's unencrypted `DatabaseSessionService` stores session
state as readable JSON text — anyone with database access can read it.

## Error Handling

adk-secure-sessions raises specific exceptions so errors are never silent:

- **`ConfigurationError`** — raised at service init if the backend doesn't
  conform to the `EncryptionBackend` protocol. Catches misconfiguration before
  any data is written.
- **`DecryptionError`** — raised if the wrong key is used to decrypt session
  data. The library never returns garbage data or silently corrupts state.

```python
from adk_secure_sessions import (
    ConfigurationError,
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)

try:
    async with EncryptedSessionService(
        db_url="sqlite+aiosqlite:///sessions.db",
        backend=FernetBackend("correct-passphrase"),
    ) as service:
        # get_session returns None for missing sessions.
        # DecryptionError is raised when reading a session that
        # was encrypted with a different key.
        session = await service.get_session(
            app_name="my-agent",
            user_id="user-123",
            session_id="some-session-id",
        )
        if session is None:
            print("Session not found")
except ConfigurationError:
    print("Backend doesn't conform to EncryptionBackend protocol")
except DecryptionError:
    print("Wrong key — cannot decrypt session data")
```

## Multi-Database Support

`EncryptedSessionService` wraps ADK's `DatabaseSessionService`, which supports
any SQLAlchemy-compatible async database. Pass a different connection string to
`db_url` to use PostgreSQL, MySQL, or MariaDB:

```python
# PostgreSQL
service = EncryptedSessionService(
    db_url="postgresql+asyncpg://user:pass@host/dbname",
    backend=FernetBackend("your-secret-passphrase"),
)

# MySQL
service = EncryptedSessionService(
    db_url="mysql+aiomysql://user:pass@host/dbname",
    backend=FernetBackend("your-secret-passphrase"),
)

# MariaDB
service = EncryptedSessionService(
    db_url="mariadb+aiomysql://user:pass@host/dbname",
    backend=FernetBackend("your-secret-passphrase"),
)
```

!!! note "Only SQLite is tested in CI"

    PostgreSQL, MySQL, and MariaDB support is inherited from
    `DatabaseSessionService` but not independently verified by this project.
    Contributions welcome!

## What's Next?

- [API Reference](reference/index.md) — full module documentation
- [Architecture Decisions](adr/index.md) — design rationale
- [FAQ](faq.md) — common questions answered
- [Envelope Protocol](envelope-protocol.md) — how encryption envelopes work
- [Algorithm Documentation](algorithms.md) — cryptographic details

## Related

- [FAQ](faq.md) — common questions about encryption, compliance, and backends
- [Algorithm Documentation](algorithms.md) — encryption algorithms, parameters, and NIST compliance
- [Envelope Protocol](envelope-protocol.md) — binary envelope format and backend coexistence
- [Architecture Decisions](adr/index.md) — all ADRs for the project
- [Roadmap](ROADMAP.md) — planned backends, features, and timeline
