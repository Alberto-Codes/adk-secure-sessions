# adk-secure-sessions

Encrypted session storage for [Google ADK](https://github.com/google/adk-python) — a drop-in replacement for `DatabaseSessionService` and `SqliteSessionService` that encrypts session data at rest.

ADK stores agent session state, conversation history, and metadata in plaintext SQLite or database files. For applications in healthcare, finance, and other regulated industries, this is a compliance gap. **adk-secure-sessions** closes it.

## The Problem

Google ADK's built-in session services (`InMemorySessionService`, `DatabaseSessionService`, `SqliteSessionService`) store all session data — including potentially sensitive user state, conversation history, and tool outputs — **unencrypted**. ADK's own docs acknowledge this risk for credentials and tokens but leave encryption as an exercise for the developer.

If you're building ADK agents that handle PHI (HIPAA), PII, financial data (SOC 2, PCI-DSS), or any regulated information, you need encryption at rest. There is currently no package in the ADK ecosystem that provides this.

## What This Package Does

- **Drop-in encrypted session service** that implements `BaseSessionService` — the same ABC that ADK's built-in services implement
- **Pluggable encryption backends** via a simple protocol (2 methods: `encrypt`, `decrypt`)
- **Field-level encryption** — state values and conversation history are encrypted; session metadata (IDs, timestamps) stays queryable
- **Async-first** — built on `aiosqlite`, matching ADK's async runtime

## Installation

```bash
pip install adk-secure-sessions
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add adk-secure-sessions
```

## Quick Start

```python
from adk_secure_sessions import (
    EncryptedSessionService,
    FernetBackend,
    BACKEND_FERNET,
)

# Create encryption backend
backend = FernetBackend("your-secret-passphrase")

# Use as async context manager
async with EncryptedSessionService(
    db_path="sessions.db",
    backend=backend,
    backend_id=BACKEND_FERNET,
) as session_service:
    # Use it exactly like ADK's DatabaseSessionService
    session = await session_service.create_session(
        app_name="my_agent",
        user_id="user_123",
        state={"api_key": "sk-secret", "preferences": {}},
    )
```

## What Gets Encrypted

| Data | Encrypted | Rationale |
|------|-----------|-----------|
| `state` values (user_state, app_state, session_state) | Yes | Contains sensitive user/app data |
| `events` (conversation history) | Yes | Contains user messages, tool outputs, PII |
| `session_id`, `app_name`, `user_id` | No | Needed for lookups and filtering |
| `create_time`, `update_time` | No | Needed for expiration/cleanup |

## EncryptionBackend Protocol

All backends implement the `EncryptionBackend` protocol — two async methods (`encrypt` and `decrypt`) operating on raw bytes. No inheritance required; any class with matching signatures conforms via structural subtyping (PEP 544).

```python
from adk_secure_sessions import EncryptionBackend

class MyBackend:
    async def encrypt(self, plaintext: bytes) -> bytes: ...
    async def decrypt(self, ciphertext: bytes) -> bytes: ...

assert isinstance(MyBackend(), EncryptionBackend)  # True
```

See `src/adk_secure_sessions/protocols.py` for the full protocol definition and known limitations.

## Encryption Backends

### v1 (Current)

| Backend | Encryption Level | Use Case |
|---------|-----------------|----------|
| **Fernet** | Field-level (state values, events) | Simple deployment, single symmetric key |

### Future

| Backend | Encryption Level | Use Case |
|---------|-----------------|----------|
| **SQLCipher** | Full database file | Maximum at-rest protection |
| **AWS KMS** | Field-level with managed keys | AWS-native compliance |
| **GCP KMS** | Field-level with managed keys | GCP-native compliance |
| **HashiCorp Vault** | Field-level with managed keys | Multi-cloud, enterprise |

Custom backends can be added by implementing the `EncryptionBackend` protocol (two async methods: `encrypt` and `decrypt`).

## How It Works

Unlike a wrapper or decorator, `EncryptedSessionService` directly implements ADK's `BaseSessionService` ABC — the same base class that `DatabaseSessionService` and `SqliteSessionService` extend. It owns its own database schema and adds encryption at the JSON serialization boundary:

```
create_session / append_event:
    state dict → json.dumps → encrypt → write to DB

get_session:
    read from DB → decrypt → json.loads → state dict
```

This is the same approach used by community session services like `adk-extra-services` (MongoDB, Redis). It avoids coupling to ADK's internal schema, which has changed across versions and will continue to evolve.

## Project Status

**Alpha** — core functionality complete. The `EncryptedSessionService` and `FernetBackend` are implemented and tested. See [ROADMAP](docs/ROADMAP.md) for planned features (PostgreSQL, KMS backends, key rotation).

## Development

```bash
# Clone and install
git clone https://github.com/Alberto-Codes/adk-secure-sessions.git
cd adk-secure-sessions
git checkout develop
uv sync --dev

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Full quality check (lint, format, docstrings, types, tests)
bash scripts/code_quality_check.sh --all --verbose
```

## License

[Apache-2.0](LICENSE)
