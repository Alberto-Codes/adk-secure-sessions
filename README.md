# adk-secure-sessions

Encrypted session storage for [Google ADK](https://github.com/google/adk-python) — a drop-in replacement for `DatabaseSessionService` and `SqliteSessionService` that encrypts session data at rest.

ADK stores agent session state, conversation history, and metadata in plaintext SQLite or database files. For applications in healthcare, finance, and other regulated industries, this is a compliance gap. **adk-secure-sessions** closes it.

## The Problem

Google ADK's built-in session services (`InMemorySessionService`, `DatabaseSessionService`, `SqliteSessionService`) store all session data — including potentially sensitive user state, conversation history, and tool outputs — **unencrypted**. ADK's own docs acknowledge this risk for credentials and tokens but leave encryption as an exercise for the developer.

If you're building ADK agents that handle PHI (HIPAA), PII, financial data (SOC 2, PCI-DSS), or any regulated information, you need encryption at rest. There is currently no package in the ADK ecosystem that provides this.

## What This Package Does

- **Drop-in encrypted session service** that implements the same interface as ADK's session services
- **Pluggable encryption backends** — choose what fits your compliance requirements:
  - Field-level encryption via [Fernet](https://cryptography.io/en/latest/fernet/) (symmetric, from the `cryptography` library)
  - Full-database encryption via [SQLCipher](https://www.zetetic.net/sqlcipher/) (transparent 256-bit AES)
  - Bring your own backend (AWS KMS, GCP KMS, HashiCorp Vault, etc.)
- **Schema tracking** — stays up to date with ADK's evolving database schema (which changed in v1.22.0 and continues to evolve)
- **Async-first** — built for ADK's async runtime

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
from adk_secure_sessions import EncryptedSessionService

# Field-level encryption with auto-generated key
session_service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///./sessions.db",
    encryption_key="your-secret-key",
)

# Use it exactly like ADK's DatabaseSessionService
session = await session_service.create_session(
    app_name="my_agent",
    user_id="user_123",
)
```

## Planned Encryption Backends

| Backend | Encryption Level | Use Case |
|---------|-----------------|----------|
| **Fernet** | Field-level (state values, events) | Simple deployment, single-key |
| **SQLCipher** | Full database file | Maximum protection, transparent |
| **AWS KMS** | Field-level with managed keys | AWS-native compliance |
| **GCP KMS** | Field-level with managed keys | GCP-native compliance |
| **HashiCorp Vault** | Field-level with managed keys | Multi-cloud, enterprise |

## Why Not Just Use SQLCipher Directly?

You can pass a `sqlite+pysqlcipher://` URL to ADK's `DatabaseSessionService` and get full-database encryption. But:

1. **No async SQLCipher dialect exists** — ADK uses `aiosqlite`, and there's no `aiosqlcipher` equivalent out of the box
2. **Field-level encryption is often preferred** for compliance — you may need to encrypt specific state values while keeping session metadata queryable
3. **Key management matters** — production deployments need KMS integration, key rotation, and audit trails, not just a passphrase
4. **Schema migrations** — when ADK updates its schema (as it did in v1.22.0), encrypted databases need careful migration handling

This package handles all of that.

## Project Status

**Alpha** — under active development. The core encryption service and Fernet backend are being built first, with additional backends to follow.

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
```

## License

[Apache-2.0](LICENSE)
