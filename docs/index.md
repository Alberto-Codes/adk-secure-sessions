# adk-secure-sessions

**Encrypted session storage for Google ADK**

adk-secure-sessions is a drop-in replacement for ADK's `DatabaseSessionService` and `SqliteSessionService` that encrypts session data at rest. Built for applications in healthcare, finance, and other regulated industries.

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
from adk_secure_sessions import EncryptionBackend

class MyBackend:
    async def encrypt(self, plaintext: bytes) -> bytes: ...
    async def decrypt(self, ciphertext: bytes) -> bytes: ...

assert isinstance(MyBackend(), EncryptionBackend)  # True
```

## Project Status

Alpha — under active development. See the [Architecture Decision Records](adr/index.md) for design rationale.

## License

Apache License 2.0 - see [LICENSE](https://github.com/Alberto-Codes/adk-secure-sessions/blob/HEAD/LICENSE) for details.
