# Feature Specification: Implement FernetBackend

**Feature Branch**: `003-fernet-backend`
**Created**: 2026-02-01
**Status**: Draft
**Input**: User description: "Implement FernetBackend — a symmetric-key encryption backend using Fernet, conforming to the EncryptionBackend protocol"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Encrypt and Decrypt Round-Trip (Priority: P1)

A developer initializes a FernetBackend with a key and uses it to encrypt plaintext bytes. They then decrypt the ciphertext and receive back the original plaintext. This is the core value proposition — reliable, symmetric encryption that "just works."

**Why this priority**: Without a working encrypt/decrypt round-trip, the backend has no value. This is the fundamental capability.

**Independent Test**: Can be fully tested by encrypting a known byte string and verifying the decrypted output matches the original input.

**Acceptance Scenarios**:

1. **Given** a FernetBackend initialized with a valid key, **When** I encrypt plaintext bytes and then decrypt the result, **Then** I get back the original plaintext bytes.
2. **Given** a FernetBackend initialized with a valid key, **When** I encrypt the same plaintext twice, **Then** the two ciphertexts are different (due to Fernet's built-in nonce/timestamp).
3. **Given** a FernetBackend initialized with a valid key, **When** I encrypt an empty byte string, **Then** I can decrypt the result back to an empty byte string.

---

### User Story 2 - Wrong Key Fails Decryption (Priority: P1)

A developer attempts to decrypt ciphertext with a different key than the one used for encryption. The system raises a clear error indicating decryption failure, preventing silent data corruption.

**Why this priority**: Security-critical — silent decryption failure with a wrong key would be a serious vulnerability. Equal priority with round-trip.

**Independent Test**: Can be tested by encrypting with key A, attempting decryption with key B, and verifying a DecryptionError is raised.

**Acceptance Scenarios**:

1. **Given** ciphertext encrypted with key A, **When** I attempt to decrypt with key B, **Then** a DecryptionError is raised.
2. **Given** ciphertext encrypted with key A, **When** I attempt to decrypt with key B, **Then** the error message indicates the decryption failed without leaking key material.

---

### User Story 3 - Flexible Key Input (Priority: P2)

A developer can provide a key as either a string or bytes when initializing FernetBackend. The system derives a valid Fernet key from the input, reducing friction for developers who may not be familiar with Fernet's key format requirements.

**Why this priority**: Improves developer experience but is not required for core encryption functionality.

**Independent Test**: Can be tested by initializing FernetBackend with a string key, performing an encrypt/decrypt round-trip, and verifying success.

**Acceptance Scenarios**:

1. **Given** a key provided as a string, **When** FernetBackend is initialized, **Then** it derives a valid Fernet key and can encrypt/decrypt successfully.
2. **Given** a key provided as bytes, **When** FernetBackend is initialized, **Then** it derives a valid Fernet key and can encrypt/decrypt successfully.
3. **Given** a key provided as a valid base64-encoded Fernet key, **When** FernetBackend is initialized, **Then** it uses the key directly without derivation.

---

### Edge Cases

- What happens when an empty string or empty bytes key is provided? The system should raise a clear error during initialization.
- What happens when ciphertext is tampered with (modified bytes)? A DecryptionError should be raised.
- What happens when ciphertext is truncated or malformed? A DecryptionError should be raised.
- What happens when non-bytes plaintext is passed to encrypt? The system should raise a TypeError.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide async `encrypt(data: bytes) -> bytes` that accepts plaintext bytes and returns ciphertext bytes.
- **FR-002**: System MUST provide async `decrypt(data: bytes) -> bytes` that accepts ciphertext bytes and returns the original plaintext bytes.
- **FR-003**: System MUST conform to the `EncryptionBackend` protocol defined in the project.
- **FR-004**: System MUST accept key input as either `str` or `bytes` during initialization.
- **FR-005**: System MUST derive a valid Fernet key from arbitrary string/bytes input (e.g., via PBKDF2 or base64 encoding).
- **FR-006**: System MUST raise `DecryptionError` when decryption fails due to wrong key, tampered ciphertext, or malformed input.
- **FR-007**: System MUST raise a clear error when initialized with an empty or invalid key.
- **FR-008**: System MUST produce different ciphertext for the same plaintext on repeated calls (non-deterministic encryption).

### Key Entities

- **FernetBackend**: The encryption backend that implements the `EncryptionBackend` protocol. Holds a derived Fernet key and provides encrypt/decrypt operations.
- **DecryptionError**: Error raised when decryption fails for any reason (wrong key, tampered data, malformed ciphertext).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Encrypt/decrypt round-trip succeeds for all valid inputs, returning identical plaintext 100% of the time.
- **SC-002**: Decryption with an incorrect key raises an error 100% of the time (zero silent failures).
- **SC-003**: FernetBackend passes runtime `isinstance` check against the `EncryptionBackend` protocol.
- **SC-004**: Developers can initialize the backend with either string or bytes keys without additional conversion steps.

## Assumptions

- The `cryptography` library will be added as a runtime dependency.
- The `EncryptionBackend` protocol from `src/adk_secure_sessions/protocols.py` defines the async `encrypt` and `decrypt` method signatures.
- A `DecryptionError` exception class will be created as part of this feature (or already exists in the project).
- Key derivation from arbitrary strings will use PBKDF2 with a reasonable default salt strategy. If the input is already a valid base64-encoded 32-byte Fernet key, it will be used directly.

## Dependencies

- `EncryptionBackend` protocol (implemented in #2 / `002-encryption-backend-protocol`)
- `cryptography` Python package (Fernet implementation)
