# ADR-002: Async-First Design

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

Google ADK is async-first. Its session services use `async def` methods, its database layer uses `aiosqlite` for SQLite and async SQLAlchemy for other backends, and its `Runner` executes agents in an async event loop.

Any session service replacement must be async-compatible to work with ADK's runtime.

## Decision

All public APIs in adk-secure-sessions are **`async def`**.

### Rules

1. **All protocol methods are `async def`** — `encrypt`, `decrypt`, and all session service methods
2. **No sync wrappers** — we don't provide `encrypt_sync()` or `create_session_sync()` convenience methods. Users in sync contexts can use `asyncio.run()` or `nest_asyncio` themselves.
3. **Backends must be async** — even if the underlying operation is CPU-bound (e.g., Fernet encryption), the method signature is `async def` for interface consistency. CPU-bound backends can use `await asyncio.to_thread()` internally if they block.
4. **Database operations use async drivers** — `aiosqlite` for SQLite, async SQLAlchemy for others, matching ADK's own approach.

### Rationale

- ADK's `BaseSessionService` methods are async — our decorator must match the signature exactly
- Encryption backends that call external services (KMS, Vault) are inherently async I/O
- Mixing sync and async creates `RuntimeError` in event loops and forces `nest_asyncio` hacks
- One consistent model is easier to reason about than sync/async dual APIs

## Consequences

### What becomes easier

- **ADK integration**: Direct drop-in, no async/sync bridging
- **KMS backends**: Network calls to key management services are naturally async
- **Consistency**: One calling convention everywhere

### What becomes harder

- **Simple scripts**: Users who aren't in an async context need `asyncio.run()`. This is standard Python and well-documented.
- **CPU-bound backends**: Fernet encryption is CPU-bound and technically doesn't benefit from async. The overhead of `async def` on a CPU-bound operation is negligible (one coroutine frame).

## Alternatives Considered

### Dual Sync/Async API

**Rejected.** Maintaining two versions of every method doubles the API surface, test matrix, and documentation. Libraries like `httpx` that do this report significant maintenance burden. ADK is async-only, so our users are already in an async context.

### Sync-Only with `run_in_executor`

**Rejected.** Would require wrapping every call site in ADK's async runtime, defeating the purpose.
