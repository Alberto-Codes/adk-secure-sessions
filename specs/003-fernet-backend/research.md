# Research: FernetBackend

**Feature**: 003-fernet-backend
**Date**: 2026-02-01

## R1: Key Derivation Strategy for Arbitrary String/Bytes Input

**Decision**: Use PBKDF2-HMAC-SHA256 to derive a 32-byte key from arbitrary input, then base64url-encode it to produce a valid Fernet key. If the input is already a valid 44-character base64url-encoded string (32 bytes decoded), use it directly as a Fernet key.

**Rationale**: Fernet requires a 32-byte base64url-encoded key. Users will often provide passphrases or arbitrary byte sequences. PBKDF2 is the standard KDF available in `cryptography` and provides sufficient security for passphrase-based key derivation. Using a fixed salt derived from the project name keeps initialization simple (no salt storage needed) while still providing KDF benefits over raw hashing.

**Alternatives considered**:
- **Hashing (SHA-256)**: Simpler but no key stretching; vulnerable to brute-force on weak passphrases.
- **HKDF**: Better for deriving keys from already-strong key material, but PBKDF2 is more appropriate for passphrase input.
- **Argon2**: Superior KDF but requires additional dependency (`argon2-cffi`); YAGNI per constitution.

**Implementation detail**: Use 480,000 iterations (OWASP 2023 recommendation for PBKDF2-HMAC-SHA256). Salt: `b"adk-secure-sessions-fernet-v1"` (constant, application-scoped).

**Security tradeoff — fixed salt**: A fixed salt means identical passphrases produce the same derived key across all deployments. An attacker who knows the public salt can precompute PBKDF2 outputs for common passphrases and reuse that work across targets. This is a deliberate simplicity tradeoff: per-key random salts would require salt storage alongside session metadata, adding API complexity. Users concerned about this should use unique passphrases per application or pass pre-generated Fernet keys directly (bypassing PBKDF2 entirely). A future iteration may introduce per-key random salts if the session metadata layer supports salt storage.

## R2: Exception Hierarchy

**Decision**: Create `SecureSessionError(Exception)` as base, with `DecryptionError(SecureSessionError)` as the only subclass for now.

**Rationale**: Constitution Principle V requires all exceptions inherit from a single base class. `DecryptionError` is needed because callers must distinguish decryption failures (wrong key, tampered data) from other errors in control flow.

**Alternatives considered**:
- **Single exception class**: Too coarse; callers need to distinguish decryption failures from configuration errors.
- **Multiple subclasses upfront** (EncryptionError, KeyError, etc.): Violates YAGNI; add when callers need them.

## R3: Async Wrapping Strategy for CPU-Bound Fernet Operations

**Decision**: Use `await asyncio.to_thread()` to run `Fernet.encrypt()` and `Fernet.decrypt()` off the event loop.

**Rationale**: Constitution Principle II requires async interface. Fernet operations are CPU-bound and fast (~microseconds for small payloads) but could block the event loop for large payloads. `asyncio.to_thread()` is the standard stdlib approach and avoids introducing executor configuration.

**Alternatives considered**:
- **Direct call without to_thread**: Simpler, but blocks the event loop. For small payloads this is negligible, but for consistency and safety with large payloads, wrapping is preferred.
- **Custom executor**: Over-engineering per YAGNI principle.

## R4: Direct Fernet Key Detection

**Decision**: Attempt to decode the input as a Fernet key first (base64url-decode to 32 bytes). If it succeeds and produces exactly 32 bytes, treat it as a direct Fernet key. Otherwise, derive via PBKDF2.

**Rationale**: Users who already have a proper Fernet key should be able to use it directly without unnecessary key derivation. This provides a fast path for advanced users while the PBKDF2 path handles passphrase input.

**Validation**: `Fernet(key)` constructor validates the key format; if it raises `ValueError`, fall back to PBKDF2 derivation.
