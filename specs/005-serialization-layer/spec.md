# Feature Specification: Serialization Layer

**Feature Branch**: `005-serialization-layer`
**Created**: 2026-02-02
**Status**: Draft
**Input**: User description: "Implement serialization layer (GH Issue #5)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Encrypt State on Write (Priority: P1)

As a session service implementor, I want to serialize a session state dictionary into a single encrypted blob so that sensitive field values are protected before storage.

**Why this priority**: This is the core write path — without it, no data can be stored securely. It is the minimum viable slice of the serialization layer.

**Independent Test**: Can be fully tested by passing a Python dictionary through the serializer and verifying the output is an opaque encrypted blob that cannot be read without the correct key.

**Acceptance Scenarios**:

1. **Given** a state dict `{"ssn": "123-45-6789"}`, **When** serialized through the encryption serializer, **Then** the output is a single encrypted blob (not readable plaintext).
2. **Given** a state dict with nested values `{"user": {"name": "Alice", "age": 30}}`, **When** serialized, **Then** the full JSON representation is encrypted as one blob.
3. **Given** an empty state dict `{}`, **When** serialized, **Then** the output is a valid encrypted blob that round-trips back to `{}`.

---

### User Story 2 - Decrypt State on Read (Priority: P1)

As a session service implementor, I want to deserialize an encrypted blob back into the original state dictionary so that the session service can work with plain data after retrieval.

**Why this priority**: Equally critical as the write path — together they form the complete round-trip that the session service depends on.

**Independent Test**: Can be tested by encrypting a known dictionary, then decrypting and comparing the result to the original.

**Acceptance Scenarios**:

1. **Given** an encrypted blob produced by the serializer, **When** deserialized, **Then** the original state dict is returned with all types preserved (strings, numbers, booleans, nulls, nested dicts, lists).
2. **Given** an encrypted blob that was tampered with, **When** deserialized, **Then** a decryption error is raised.
3. **Given** an encrypted blob produced with a different key, **When** deserialized with the current key, **Then** a decryption error is raised.

---

### User Story 3 - Self-Describing Encrypted Format (Priority: P2)

As a library maintainer, I want encrypted output to carry a version and backend identifier prefix so that future backend migrations can coexist with existing encrypted data.

**Why this priority**: Important for forward-compatibility and operational safety, but not strictly required for a single-backend MVP to function.

**Independent Test**: Can be tested by inspecting the raw bytes of an encrypted blob and verifying the first two bytes encode the expected version and backend identifiers.

**Acceptance Scenarios**:

1. **Given** data encrypted by the serializer, **When** inspecting the raw output, **Then** the first byte identifies the envelope format version and the second byte identifies the encryption backend used.
2. **Given** an encrypted blob with an unrecognized version byte, **When** deserialized, **Then** a clear error is raised indicating the format is unsupported.
3. **Given** encrypted blobs from two different backends, **When** inspecting their prefixes, **Then** the backend identifier bytes differ while the version byte may be the same.

---

### User Story 4 - Encrypt Event Data on Write (Priority: P2)

As a session service implementor, I want ADK Event objects to be serialized and encrypted before storage so that event payloads receive the same protection as session state.

**Why this priority**: Events contain user interaction data that can be sensitive. Needed for full session protection but can follow after the core state path is working.

**Independent Test**: Can be tested by passing a JSON-serialized event string through the serializer and verifying it round-trips correctly.

**Acceptance Scenarios**:

1. **Given** a JSON string representing an ADK Event (from `event.model_dump_json()`), **When** serialized, **Then** the output is an encrypted blob with the self-describing prefix.
2. **Given** an encrypted event blob, **When** deserialized, **Then** the original JSON string is returned and can be parsed back into the Event model.

---

### Edge Cases

- What happens when the input dictionary contains values that are not JSON-serializable (e.g., `datetime`, custom objects)?
  → The serializer raises a clear serialization error before attempting encryption.
- What happens when the encrypted blob is truncated or empty?
  → A decryption error is raised with a message indicating corrupt or incomplete data.
- What happens when the input is extremely large (e.g., 10 MB state)?
  → The serializer processes it without special-casing; performance is bounded by the encryption backend. No artificial size limit is imposed by the serializer itself.
- What happens when the input contains non-ASCII or Unicode characters?
  → JSON encoding handles this natively; the serializer preserves Unicode through the round-trip.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST serialize a Python dictionary into JSON and encrypt the resulting bytes using any `EncryptionBackend`-conformant backend.
- **FR-002**: System MUST decrypt an encrypted blob and deserialize the JSON back into the original Python dictionary, preserving all JSON-compatible types.
- **FR-003**: System MUST prepend a two-byte envelope (version byte + backend identifier byte) to all encrypted output.
- **FR-004**: System MUST validate the envelope prefix on decryption and raise `DecryptionError` if the version or backend identifier is unrecognized.
- **FR-005**: System MUST raise a serialization-specific error when the input cannot be serialized to JSON.
- **FR-006**: System MUST accept raw JSON strings (e.g., from `model_dump_json()`) as input for encryption, in addition to dictionaries.
- **FR-007**: System MUST expose all serialization operations as async functions, consistent with the library's async-first design.
- **FR-008**: System MUST never include plaintext data, key material, or full ciphertext in error messages or exceptions.

### Key Entities

- **Encrypted Envelope**: A byte sequence consisting of `[version byte][backend id byte][ciphertext]` that self-describes its encryption format.
- **Serializer**: The component responsible for converting between Python data structures and encrypted envelopes via a provided encryption backend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Any JSON-serializable Python dictionary can be encrypted and decrypted back to an identical dictionary in a single round-trip with 100% fidelity.
- **SC-002**: Tampering with any byte of an encrypted envelope results in a decryption error — no silent data corruption.
- **SC-003**: The serializer adds no more than 2 bytes of overhead beyond what the encryption backend itself produces.
- **SC-004**: All serializer operations complete without blocking the async event loop.
- **SC-005**: Error messages from the serializer never contain sensitive data (plaintext values, key material, or raw ciphertext).

## Assumptions

- The encryption backend is always provided by the caller; the serializer does not manage keys or backend instantiation.
- JSON is the sole interchange format; other formats (msgpack, protobuf) are out of scope.
- The version byte and backend identifier byte values will be defined during implementation planning (the spec defines the structure, not the specific byte values).
- ADK Event objects expose a `model_dump_json()` method that returns a valid JSON string; the serializer treats this as opaque string input.

## Out of Scope

- Base64 encoding for database text column storage (responsibility of the session service layer, not the serializer).
- Key management, rotation, or backend selection logic.
- Compression of data before encryption.
- Streaming or chunked encryption for very large payloads.
