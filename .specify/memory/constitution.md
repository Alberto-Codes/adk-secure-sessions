<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0 (initial ratification)
- Added principles: Protocol-Based Interfaces, Async-First, Field-Level Encryption,
  ADK Interface Compatibility, Minimal Exception Surface, Simplicity & YAGNI
- Added sections: Security Constraints, Development Workflow
- Added: Governance rules
- Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no update needed (Constitution Check
    section is generic and will be filled per-feature)
  - .specify/templates/spec-template.md — ✅ no update needed
  - .specify/templates/tasks-template.md — ✅ no update needed
- Follow-up TODOs: none
-->

# adk-secure-sessions Constitution

## Core Principles

### I. Protocol-Based Interfaces

All public interfaces MUST use `typing.Protocol` (PEP 544) with
`@runtime_checkable`. Protocols MUST define the minimal surface
required — no convenience methods in the contract. Implementors
MUST NOT be required to inherit from or import our package to
satisfy a contract. Optional capabilities (key rotation, metadata)
MUST be separate protocols, never added to the core contract.

### II. Async-First

All public APIs MUST be `async def`. No sync wrappers or dual
sync/async APIs. Database operations MUST use async drivers
(`aiosqlite`, async SQLAlchemy). CPU-bound backends MAY use
`await asyncio.to_thread()` internally but MUST expose an async
interface. This matches ADK's async runtime and avoids event loop
conflicts.

### III. Field-Level Encryption by Default

Sensitive data (state values, event/conversation history) MUST be
encrypted at the JSON serialization boundary. Operational metadata
(session_id, app_name, user_id, timestamps) MUST remain in
plaintext to preserve queryability. Full-database encryption
(SQLCipher) MAY be offered as an alternative backend but MUST NOT
be the default. Exception messages MUST NOT contain ciphertext,
key material, or plaintext.

### IV. ADK Interface Compatibility

The library MUST implement `BaseSessionService` directly — not
wrap or decorate ADK's built-in services. The library MUST own
its own database schema, independent of ADK's internal tables.
Dependencies on ADK MUST be limited to the public API surface:
`BaseSessionService` method signatures, `Session`/`Event` models,
and state prefix constants. CI MUST test against both the minimum
supported ADK version and latest.

### V. Minimal Exception Surface

All library exceptions MUST inherit from a single base class
(`SecureSessionError`). New exception subclasses MUST only be
added when callers have a concrete need to handle a failure mode
differently in control flow — not for log categorization or
speculative scenarios. ADK exceptions MUST NOT be swallowed or
re-wrapped.

### VI. Simplicity & YAGNI

Start with the minimum viable implementation. Add subclasses,
configuration options, and abstractions only when real usage
demands them. Three similar lines of code are preferable to a
premature abstraction. Features planned for future phases (KMS
backends, SQLCipher) MUST NOT influence the v1 architecture
beyond ensuring extension points exist via protocols.

## Security Constraints

- Encryption keys MUST NOT appear in log output, exception
  messages, or serialized session data.
- The encrypted value format MUST be self-describing (version
  byte + backend ID) to support key rotation and backend
  migration without re-encrypting all existing data.
- Default encryption (Fernet) provides authenticated encryption
  (AES-128-CBC + HMAC-SHA256). Alternative backends MUST provide
  equivalent or stronger authenticated encryption guarantees.
- Users SHOULD use opaque identifiers for `user_id` when the
  identifier itself is PII.

## Development Workflow

- All code MUST pass `ruff check`, type checking, and `pytest`
  before merge.
- ADRs document significant architectural decisions in
  `docs/adr/`.
- Commits SHOULD be atomic and focused on a single change.
- The `develop` branch is the integration branch; `main` is
  release-only.

## Governance

This constitution is the authoritative reference for project
design decisions. All PRs and code reviews MUST verify compliance
with these principles. Amendments require:

1. A written proposal describing the change and rationale.
2. An updated ADR if the amendment changes an architectural
   decision.
3. Version bump per semantic versioning (see below).
4. Update of any dependent templates or documentation that
   reference changed principles.

Versioning policy:
- MAJOR: Principle removal or backward-incompatible redefinition.
- MINOR: New principle or materially expanded guidance.
- PATCH: Clarifications, wording, or non-semantic refinements.

**Version**: 1.0.0 | **Ratified**: 2026-02-01 | **Last Amended**: 2026-02-01
