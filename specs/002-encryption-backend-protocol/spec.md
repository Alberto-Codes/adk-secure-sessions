# Feature Specification: EncryptionBackend Protocol

**Feature Branch**: `002-encryption-backend-protocol`
**Created**: 2026-02-01
**Status**: Draft
**Input**: GitHub Issue #2 — Implement EncryptionBackend protocol

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Encryption Contract (Priority: P1)

As a library maintainer, I need a formal protocol that defines the
encryption backend contract so that all backends (Fernet, KMS, Vault)
conform to the same interface and the session service can depend on
a single, stable abstraction.

**Why this priority**: The protocol is the foundation that every other
encryption component depends on. Without it, no backend or session
service can be built.

**Independent Test**: Can be verified by creating a minimal class with
`encrypt` and `decrypt` methods and confirming it satisfies the
protocol contract without inheriting from any base class.

**Acceptance Scenarios**:

1. **Given** the `EncryptionBackend` protocol exists, **When** a
   developer reads its definition, **Then** it specifies exactly two
   async methods: `encrypt(plaintext: bytes) -> bytes` and
   `decrypt(ciphertext: bytes) -> bytes`.
2. **Given** the protocol, **When** a developer implements a class
   with matching method signatures, **Then** the class satisfies the
   protocol without importing or inheriting from it.

---

### User Story 2 - Runtime Validation (Priority: P1)

As a session service consumer, I need the protocol to be runtime
checkable so that initialization can detect invalid backends early
with a clear error message rather than failing at encrypt/decrypt
time.

**Why this priority**: Runtime validation prevents silent failures
and improves developer experience. It is tightly coupled to the
protocol definition and should ship together.

**Independent Test**: Can be verified by passing both a conforming
and non-conforming object to `isinstance(obj, EncryptionBackend)`
and checking the boolean result.

**Acceptance Scenarios**:

1. **Given** a class with `async def encrypt(self, plaintext: bytes)
   -> bytes` and `async def decrypt(self, ciphertext: bytes) ->
   bytes`, **When** checked with `isinstance(obj, EncryptionBackend)`,
   **Then** it returns `True`.
2. **Given** a class missing the `decrypt` method, **When** checked
   with `isinstance(obj, EncryptionBackend)`, **Then** it returns
   `False`.
3. **Given** a class with synchronous `encrypt`/`decrypt` methods
   (not async), **When** checked with
   `isinstance(obj, EncryptionBackend)`, **Then** it returns `True`
   (structural typing checks signatures, not async status at
   runtime — this is a known Python limitation to document).

---

### User Story 3 - Third-Party Extensibility (Priority: P2)

As a third-party developer, I want to implement a custom encryption
backend (e.g., for AWS KMS) without importing or depending on the
`adk-secure-sessions` package, so that my backend library remains
decoupled.

**Why this priority**: Extensibility is a key design goal but is a
consequence of the protocol-based approach rather than a separate
deliverable.

**Independent Test**: Can be verified by implementing a backend in
an isolated module that does not import `adk_secure_sessions` and
confirming it passes runtime and static type checks.

**Acceptance Scenarios**:

1. **Given** a third-party class with matching method signatures
   defined in a separate package, **When** the session service
   receives it, **Then** it passes the runtime protocol check and
   can be used for encryption/decryption.

---

### Edge Cases

- What happens when a backend implements `encrypt` but not `decrypt`?
  The runtime check MUST return `False` and the session service
  MUST raise a clear error at initialization.
- What happens when method signatures have wrong parameter types
  (e.g., `encrypt(self, plaintext: str)` instead of `bytes`)?
  Runtime `isinstance` checks do not validate parameter types in
  Python's `typing.Protocol` — this is a known limitation.
  Static type checkers MUST catch this.
- What happens when a backend's methods are synchronous instead of
  async? `@runtime_checkable` does not distinguish coroutine
  functions from regular functions. This MUST be documented as a
  known limitation. Static type checkers MUST catch the mismatch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST provide an `EncryptionBackend`
  protocol with exactly two methods: `encrypt` and `decrypt`.
- **FR-002**: Both methods MUST accept `bytes` as input and return
  `bytes` as output.
- **FR-003**: Both methods MUST be defined as `async def`.
- **FR-004**: The protocol MUST be decorated with
  `@runtime_checkable` to support `isinstance()` validation.
- **FR-005**: The protocol MUST use structural subtyping — no
  inheritance or registration required from implementors.
- **FR-006**: The protocol module MUST have zero external
  dependencies (stdlib `typing` only).
- **FR-007**: The protocol MUST be the sole public interface that
  encryption backends conform to — the library MUST NOT provide
  an alternative abstract base class for the same purpose.

### Key Entities

- **EncryptionBackend**: The protocol defining the contract for all
  encryption backends. Attributes: two async methods (`encrypt`,
  `decrypt`), both operating on raw bytes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can implement a conforming backend in
  under 5 minutes by reading only the protocol definition.
- **SC-002**: A conforming backend passes `isinstance()` checks
  without importing or inheriting from any library class.
- **SC-003**: A non-conforming object (missing methods) fails the
  `isinstance()` check and does not cause runtime exceptions in
  unrelated code paths.
- **SC-004**: Static type checkers (mypy, pyright) detect
  signature mismatches (wrong parameter types, missing async)
  at analysis time.

### Assumptions

- Python 3.10+ is the minimum supported version (required for
  stable `typing.Protocol` + `@runtime_checkable` behavior).
- The protocol operates on raw `bytes` — serialization (JSON to
  bytes conversion) is handled by a separate serialization layer,
  not the backend.
- Optional capability protocols (e.g., `SupportsKeyRotation`,
  `SupportsMetadata`) are out of scope for this feature and will
  be specified separately when needed.
