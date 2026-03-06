[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/adk-secure-sessions/ci.yml?branch=main)](https://github.com/Alberto-Codes/adk-secure-sessions/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Alberto-Codes/adk-secure-sessions/graph/badge.svg)](https://codecov.io/gh/Alberto-Codes/adk-secure-sessions)
[![PyPI](https://img.shields.io/pypi/v/adk-secure-sessions)](https://pypi.org/project/adk-secure-sessions/)
[![Python](https://img.shields.io/pypi/pyversions/adk-secure-sessions)](https://pypi.org/project/adk-secure-sessions/)
[![License](https://img.shields.io/pypi/l/adk-secure-sessions)](https://github.com/Alberto-Codes/adk-secure-sessions/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)

# adk-secure-sessions

The compliance gateway for [Google ADK](https://github.com/google/adk-python) — add encrypted sessions in 5 minutes.

ADK's built-in session services store all data unencrypted. If your agents handle PHI, PII, or financial data, that's a compliance gap. **adk-secure-sessions** is an encrypted session service wrapping ADK's `DatabaseSessionService` that encrypts state and conversation history at rest, so you can close the encryption-at-rest gap without changing your agent code.

## Install

```bash
pip install adk-secure-sessions
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add adk-secure-sessions
```

**2 direct runtime dependencies**: google-adk, cryptography.

## Quick Start

```python
# Before (ADK default — unencrypted):
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///sessions.db")

# After (encrypted — swap the import and constructor):
from adk_secure_sessions import EncryptedSessionService, FernetBackend
session_service = EncryptedSessionService(
    db_url="sqlite+aiosqlite:///sessions.db", backend=FernetBackend("your-secret-key")
)
```

Use `session_service` exactly like any ADK session service — `create_session`, `get_session`, `list_sessions`, `delete_session`, and `append_event` all work the same way. Wrap in `async with` for automatic cleanup — see [Documentation](https://alberto-codes.github.io/adk-secure-sessions/) for details.

> **Migration note (v1.1.0):** The constructor API changed from `(db_path, backend, backend_id)` to `(db_url, backend)`. Existing databases from v1.0.x are incompatible — create a fresh database when upgrading.

## What Gets Encrypted

| Data | Encrypted | Rationale |
|------|-----------|-----------|
| `state` values (user_state, app_state, session_state) | Yes | Contains sensitive user/app data |
| `events` (conversation history) | Yes | Contains user messages, tool outputs, PII |
| `session_id`, `app_name`, `user_id` | No | Needed for lookups and filtering |
| `create_time`, `update_time` | No | Needed for expiration/cleanup |

## Examples

See [`examples/`](examples/) for runnable scripts. The
[basic usage example](examples/basic_usage.py) runs a multi-turn ADK agent
conversation with Ollama and proves that state and conversation history are
encrypted at rest.

```bash
uv run python examples/basic_usage.py
```

Requires `OLLAMA_API_BASE` in your environment or `.env` file.

## Links

- [Documentation](https://alberto-codes.github.io/adk-secure-sessions/)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [License (Apache-2.0)](LICENSE)
