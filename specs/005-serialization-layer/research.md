# Research: Serialization Layer

**Feature**: 005-serialization-layer
**Date**: 2026-02-02

## R1: Envelope Format (Version Byte + Backend ID)

**Decision**: Use a 2-byte prefix: `[0x01][backend_id][ciphertext]`.
- Version byte `0x01` indicates envelope format v1.
- Backend ID `0x01` = Fernet. Future backends get sequential IDs (e.g., `0x02` = AES-256-GCM per issue #16).

**Rationale**: Fixed 2-byte overhead is minimal, simple to parse, and supports up to 255 versions × 255 backends. No length-prefix or TLV complexity needed at this stage.

**Alternatives considered**:
- TLV (Type-Length-Value): Over-engineered for a 2-field header with known fixed size.
- Magic bytes (e.g., `ASS\x01`): Adds unnecessary bytes; version+backend is sufficient for identification.
- Single combined byte: Limits to 16 versions × 16 backends with nibble packing; not worth the complexity savings.

## R2: New Exception — SerializationError

**Decision**: Add `SerializationError(SecureSessionError)` to the exception hierarchy for JSON serialization failures (e.g., non-serializable types). Encryption/decryption failures continue using `EncryptionError`/`DecryptionError`.

**Rationale**: Callers need to distinguish "your data can't be serialized" (a bug in the caller's code) from "encryption failed" (a configuration/key issue). This aligns with Constitution V (Minimal Exception Surface) — there is a concrete control-flow need.

**Alternatives considered**:
- Reusing `EncryptionError`: Conflates two distinct failure modes with different remediation paths.
- Using stdlib `TypeError`/`ValueError`: Loses the `SecureSessionError` base class, breaking broad catch patterns.

## R3: Function vs. Class API

**Decision**: Module-level async functions (`encrypt_session`, `decrypt_session`, `encrypt_json`, `decrypt_json`) rather than a `Serializer` class.

**Rationale**: The serializer holds no state — the encryption backend is passed per call. A class would be an empty shell wrapping static methods. Constitution VI (Simplicity & YAGNI) favors the simpler approach.

**Alternatives considered**:
- `Serializer` class with `__init__(backend)`: Adds indirection for no state benefit. If the session service needs to change backends between calls, a class makes it harder.
- Protocol-based `Serializer`: Over-abstraction when there's exactly one implementation with no expected variation.

## R4: Input Handling — dict vs. str

**Decision**: Provide two function pairs:
1. `encrypt_session(data: dict, backend, backend_id) -> bytes` / `decrypt_session(blob: bytes, backend) -> dict` — for state dicts.
2. `encrypt_json(json_str: str, backend, backend_id) -> bytes` / `decrypt_json(blob: bytes, backend) -> str` — for pre-serialized JSON strings (events).

**Rationale**: The session service passes dicts for state but pre-serialized JSON strings for events (`model_dump_json()`). Two pairs keep each function focused and avoid type-checking branches.

**Alternatives considered**:
- Single function with `Union[dict, str]` input: Requires runtime isinstance checks, ambiguous return type, violates single-responsibility.
- Only dict input, caller does `json.dumps` for events: Pushes serialization responsibility outside the layer, defeating its purpose.

## R5: Backend ID Registry

**Decision**: A module-level `dict[int, str]` mapping backend IDs to names, used only for error messages. Backend ID is passed by the caller (not auto-detected from the backend object).

**Rationale**: The serializer doesn't need to know about backend internals. The caller (session service) knows which backend it's using and passes the corresponding ID. This avoids coupling the serializer to backend class names or adding an `id` property to the protocol.

**Alternatives considered**:
- Adding `backend_id` property to `EncryptionBackend` protocol: Breaks Constitution I (minimal protocol surface) and all existing implementations.
- Auto-detect via `isinstance` checks: Fragile, doesn't work with structural typing, violates protocol philosophy.
