# Feature Specification: Exception Hierarchy

**Feature Branch**: `004-exception-hierarchy`
**Created**: 2026-02-02
**Status**: Draft
**Input**: GitHub Issue #4 — Implement exception hierarchy for encryption failures

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catch All Library Errors (Priority: P1)

As a developer integrating adk-secure-sessions, I want a single base exception class so that I can write a catch-all handler for any error originating from this library without catching unrelated exceptions.

**Why this priority**: This is the foundation — every consumer needs a reliable way to catch library errors without over-broad exception handling.

**Independent Test**: Can be tested by raising any library exception and verifying it is caught by a single `except SecureSessionError` handler.

**Acceptance Scenarios**:

1. **Given** an encryption operation fails, **When** I catch `SecureSessionError`, **Then** the error is caught regardless of whether it was an encryption or decryption failure.
2. **Given** a library error is raised, **When** I catch `Exception` subclasses outside the hierarchy, **Then** `SecureSessionError` is not accidentally caught by unrelated handlers (it only inherits from `Exception`).

---

### User Story 2 - Distinguish Encryption from Decryption Errors (Priority: P1)

As a developer, I want separate exception types for encryption and decryption failures so that I can implement different recovery strategies (e.g., retry with a different key for decryption vs. report a configuration error for encryption).

**Why this priority**: Equally critical — the entire purpose of the hierarchy is to enable granular error handling.

**Independent Test**: Can be tested by raising `DecryptionError`, verifying it is caught by `except DecryptionError` but not by `except EncryptionError`, and vice versa.

**Acceptance Scenarios**:

1. **Given** a decryption failure (e.g., wrong key), **When** I catch `DecryptionError`, **Then** it matches, and `except EncryptionError` does not catch it.
2. **Given** an encryption failure, **When** I catch `EncryptionError`, **Then** it matches, and `except DecryptionError` does not catch it.
3. **Given** either failure type, **When** I catch `SecureSessionError`, **Then** both are caught by the base class handler.

---

### User Story 3 - Safe Error Messages (Priority: P2)

As a developer, I want exception messages that provide useful debugging context without leaking sensitive data (keys, plaintext, ciphertext) so that I can safely log errors in production.

**Why this priority**: Important for security but does not affect core functionality — developers can use the library without this, but production safety depends on it.

**Independent Test**: Can be tested by inspecting exception message content and verifying no sensitive material is present.

**Acceptance Scenarios**:

1. **Given** a decryption failure caused by an invalid key, **When** the exception is raised, **Then** the message describes the failure category (e.g., "Decryption failed") without including the key material or ciphertext.
2. **Given** any library exception, **When** the message is logged, **Then** it contains no sensitive data such as keys, tokens, or plaintext content.

---

### Edge Cases

- What happens when a developer subclasses `SecureSessionError` in their own code? The hierarchy should remain stable and not break `isinstance` checks.
- How does the hierarchy behave with exception chaining (`raise ... from ...`)? Original cause should be preserved without leaking sensitive data in the chain.
- What happens when exception messages are serialized (e.g., JSON logging)? Messages must remain safe for serialization.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST provide a base exception class `SecureSessionError` that all library-specific exceptions inherit from.
- **FR-002**: The library MUST provide an `EncryptionError` class that is a direct subclass of `SecureSessionError` for encryption-specific failures.
- **FR-003**: The library MUST provide a `DecryptionError` class that is a direct subclass of `SecureSessionError` for decryption-specific failures.
- **FR-004**: `EncryptionError` and `DecryptionError` MUST be sibling classes (neither inherits from the other).
- **FR-005**: All exception classes MUST support a human-readable message parameter.
- **FR-006**: Exception messages MUST NOT contain sensitive data (encryption keys, plaintext, ciphertext, or tokens).
- **FR-007**: All three exception classes MUST be importable from the library's public API.
- **FR-008**: The exception hierarchy MUST NOT swallow or suppress underlying causes — exception chaining MUST be preserved when wrapping lower-level errors.

### Key Entities

- **SecureSessionError**: Base exception for all adk-secure-sessions errors. Inherits from `Exception`.
- **EncryptionError**: Raised when an encryption operation fails. Inherits from `SecureSessionError`.
- **DecryptionError**: Raised when a decryption operation fails (e.g., wrong key, corrupted data). Inherits from `SecureSessionError`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can catch all library errors with a single handler using the base exception class, with 100% coverage of library exception types.
- **SC-002**: Developers can distinguish between encryption and decryption failures using specific exception types, enabling targeted error recovery.
- **SC-003**: No exception message produced by the library contains sensitive data (keys, plaintext, ciphertext), verified by inspection of all raise sites.
- **SC-004**: Exception chaining preserves the original cause for all wrapped errors, enabling full debugging without information loss.

## Assumptions

- The hierarchy is intentionally small (three classes) to match current needs. Additional exception types (e.g., `SerializationError`, `KeyManagementError`) will be added in future phases as needed.
- `SecureSessionError` inherits directly from `Exception` (not `RuntimeError` or other built-in subclasses) to avoid accidental catching by overly broad handlers.
- Exception classes do not carry structured metadata (error codes, context dicts) in this phase — just a message string.

## Dependencies

- Part of Epic #1 (Phase 1: Core Encryption + Fernet MVP).
- No external library dependencies — uses only Python built-in exception mechanisms.
- Will be consumed by the Fernet backend (#3, already merged) and future components (serialization layer #5, session service #6).
