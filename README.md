[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/adk-secure-sessions/ci.yml?branch=main&label=tests)](https://github.com/Alberto-Codes/adk-secure-sessions/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Alberto-Codes/adk-secure-sessions/graph/badge.svg)](https://codecov.io/gh/Alberto-Codes/adk-secure-sessions)
[![PyPI](https://img.shields.io/pypi/v/adk-secure-sessions)](https://pypi.org/project/adk-secure-sessions/)
[![Python](https://img.shields.io/pypi/pyversions/adk-secure-sessions)](https://pypi.org/project/adk-secure-sessions/)
[![License](https://img.shields.io/pypi/l/adk-secure-sessions)](https://github.com/Alberto-Codes/adk-secure-sessions/blob/main/LICENSE)
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)

# adk-secure-sessions

The compliance gateway for [Google ADK](https://github.com/google/adk-python) — add encrypted sessions in 5 minutes.

ADK's built-in session services store all data unencrypted. If your agents handle PHI, PII, or financial data, that's a compliance gap. **adk-secure-sessions** is a drop-in replacement for `DatabaseSessionService` that encrypts state and conversation history at rest, so you can close the encryption-at-rest gap without changing your agent code.

## Install

```bash
pip install adk-secure-sessions
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add adk-secure-sessions
```

**3 direct runtime dependencies**: google-adk, cryptography, aiosqlite.

## Quick Start

```python
# Before (ADK default — unencrypted):
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")

# After (encrypted — swap the import and constructor):
from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET
session_service = EncryptedSessionService(
    db_path="sessions.db", backend=FernetBackend("your-secret-key"), backend_id=BACKEND_FERNET
)
```

Use `session_service` exactly like any ADK session service — `create_session`, `get_session`, `list_sessions`, `delete_session`, and `append_event` all work the same way. Wrap in `async with` for automatic cleanup — see [Documentation](https://github.com/Alberto-Codes/adk-secure-sessions/tree/main/docs) for details.

## What Gets Encrypted

| Data | Encrypted | Rationale |
|------|-----------|-----------|
| `state` values (user_state, app_state, session_state) | Yes | Contains sensitive user/app data |
| `events` (conversation history) | Yes | Contains user messages, tool outputs, PII |
| `session_id`, `app_name`, `user_id` | No | Needed for lookups and filtering |
| `create_time`, `update_time` | No | Needed for expiration/cleanup |

## Links

<!-- Update to https://alberto-codes.github.io/adk-secure-sessions/ when MkDocs deploys (Story 2.2) -->
- [Documentation](https://github.com/Alberto-Codes/adk-secure-sessions/tree/main/docs)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [License (Apache-2.0)](LICENSE)
