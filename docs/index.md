# adk-secure-sessions

[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/adk-secure-sessions/ci.yml?branch=main)](https://github.com/Alberto-Codes/adk-secure-sessions/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Alberto-Codes/adk-secure-sessions/graph/badge.svg)](https://codecov.io/gh/Alberto-Codes/adk-secure-sessions)
[![PyPI](https://img.shields.io/pypi/v/adk-secure-sessions)](https://pypi.org/project/adk-secure-sessions/)
[![Python](https://img.shields.io/pypi/pyversions/adk-secure-sessions)](https://pypi.org/project/adk-secure-sessions/)
[![License](https://img.shields.io/pypi/l/adk-secure-sessions)](https://github.com/Alberto-Codes/adk-secure-sessions/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)

**Encrypted session storage for Google ADK**

adk-secure-sessions is an encrypted session persistence service implementing ADK's `BaseSessionService` that encrypts session data at rest. Built for applications in healthcare, finance, and other regulated industries.

## Quick Links

<div class="grid cards" markdown>

- :material-lock: **[API Reference](reference/index.md)**

    Auto-generated documentation for all modules, classes, and functions.

- :material-file-tree: **[Architecture](adr/index.md)**

    Understand the design decisions behind adk-secure-sessions.

- :material-book-open-variant: **[Contributing](contributing/docstring-templates.md)**

    Guidelines for contributing code and documentation.

</div>

## Features

- **Drop-in Replacement**: Implements ADK's `BaseSessionService` ABC
- **Pluggable Backends**: `EncryptionBackend` protocol — any class with `encrypt`/`decrypt` works
- **Field-Level Encryption**: State values and events encrypted; IDs and timestamps stay queryable
- **Async-First**: Built on `aiosqlite`, matching ADK's async runtime
- **Well-Documented**: Google-style docstrings with 95%+ coverage

## Installation

```bash
uv add adk-secure-sessions
```

## Basic Usage

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
) as service:
    # Create encrypted session
    session = await service.create_session(
        app_name="my-agent",
        user_id="user-123",
        state={"api_key": "sk-secret"},
    )

    # Retrieve with automatic decryption
    session = await service.get_session(
        app_name="my-agent",
        user_id="user-123",
        session_id=session.id,
    )
```

## Custom Encryption Backend

Any class with `encrypt` and `decrypt` methods conforms to the protocol:

```python
from adk_secure_sessions import EncryptionBackend

class MyBackend:
    async def encrypt(self, plaintext: bytes) -> bytes: ...
    async def decrypt(self, ciphertext: bytes) -> bytes: ...

assert isinstance(MyBackend(), EncryptionBackend)  # True
```

## Project Status

Alpha — core functionality complete. `EncryptedSessionService` and `FernetBackend` are implemented and tested. See the [Roadmap](ROADMAP.md) for planned features and [Architecture Decision Records](adr/index.md) for design rationale.

## License

Apache License 2.0 - see [LICENSE](https://github.com/Alberto-Codes/adk-secure-sessions/blob/HEAD/LICENSE) for details.
