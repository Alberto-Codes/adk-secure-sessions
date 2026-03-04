# Project Conventions

Foundational principles for the adk-secure-sessions codebase. These guide design decisions and resolve ambiguity when facing implementation choices.

## Encryption Is a Contract, Not a Feature

Every data path to and from persistence must go through the encrypt/decrypt cycle. An unencrypted path is a security defect, not a TODO. This applies to new fields, new state keys, and any new database operations — if data touches SQLite, it goes through `encrypt_session`/`decrypt_session`.

This exists because the project's entire value proposition is at-rest encryption. A single unprotected path invalidates the security guarantee for every user. See [ADR-003: Field-Level Encryption by Default](docs/adr/ADR-003-field-level-encryption.md).

## Async-First by Design

All public APIs are `async def`. Blocking calls (especially `cryptography` library operations) are wrapped in `asyncio.to_thread()`. There are no synchronous public functions.

This enables the library to integrate naturally into async ADK agent pipelines without blocking the event loop. Fernet encrypt/decrypt is CPU-bound and must not starve other coroutines. See [ADR-002: Async-First Design](docs/adr/ADR-002-async-first.md).

## Protocols Over Inheritance

Use PEP 544 `@runtime_checkable` Protocol for all contracts. Never use ABC or abstractmethod. Backends conform to `EncryptionBackend` Protocol, not a base class.

This decouples implementations from the contract, enabling third-party backends without inheritance chains and making `isinstance()` checks work at runtime for validation. See [ADR-001: Protocol-Based Interfaces](docs/adr/ADR-001-protocol-based-interfaces.md).

## The Envelope Is a Wire Protocol

Serialized data uses the binary layout `[version_byte][backend_id_byte][ciphertext]`. The header exists for key rotation and audit. Never strip, shortcut, or skip the envelope — even for "simple" cases.

This ensures every piece of encrypted data is self-describing. When key rotation or backend migration happens, the envelope tells the system which backend and version produced the ciphertext. See [ADR-000: Strategy + Direct Implementation Architecture](docs/adr/ADR-000-strategy-decorator-architecture.md).

## ADK Is Upstream, We Are Downstream

Extend `BaseSessionService` but don't fight the ADK contract. Override only the documented public methods (`create_session`, `get_session`, `list_sessions`, `delete_session`). Never redefine `Session` or `Event` — import from `google.adk.sessions`. Check upstream signatures before overriding.

This keeps us compatible across the google-adk version matrix (1.22.0 through latest). Fighting the upstream contract creates brittle code that breaks on ADK updates. See [ADR-004: ADK Interface Compatibility Strategy](docs/adr/ADR-004-adk-schema-compatibility.md).

## Own Our Schema

Our SQLite schema (`app_states`, `user_states`, `sessions`, `events`) is derived from ADK's Session/Event data model contract with encrypted column types. Operationally independent — own tables, own migrations, own encryption — but structurally coupled to ADK's public model contract. All database access uses raw parametrized SQL via aiosqlite, not SQLAlchemy ORM.

This gives us full control over the storage layer — encryption, indexing, and migration — while acknowledging that our table structure follows ADK's data model. See [ADR-004: ADK Interface Compatibility Strategy](docs/adr/ADR-004-adk-schema-compatibility.md).
