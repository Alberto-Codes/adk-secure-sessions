# ADR-008: Per-Key Random Salt Key Derivation

> **Status**: Accepted
> **Date**: 2026-03-07
> **Deciders**: adk-secure-sessions maintainers

## Context

`FernetBackend` derives encryption keys from passphrases via PBKDF2-HMAC-SHA256.
Prior to this change, derivation used a **fixed, application-scoped salt**
(`b"adk-secure-sessions-fernet-v1"`) and **480,000 iterations**. This meant:

1. Identical passphrases always produced the same Fernet key across all
   `FernetBackend` instances, enabling precomputation (rainbow table) attacks.
2. The iteration count fell below the OWASP 2023 Password Storage Cheat Sheet
   recommendation of 600,000 for PBKDF2-HMAC-SHA256.

Both limitations were documented in `docs/algorithms.md` as planned Phase 3
improvements (FR47, NFR11).

### Design Constraints

- The `EncryptionBackend` protocol and envelope format must not change.
- Salt is a backend-internal concern, opaque to the serialization layer.
- Backward compatibility with pre-3.2 ciphertext is required.
- Per-operation PBKDF2 is unacceptable (0.3--0.5 s per call at 600k iterations).
- Pre-generated Fernet keys (passthrough mode) must remain unaffected.

## Decision

### 1. Per-Key Random Salt via Two-Phase Key Derivation

Adopt the RFC 5869 "extract-then-expand" pattern:

**Phase 1 — Extract (init time, once)**:
`PBKDF2(passphrase, fixed_app_salt, 600_000) -> master_key (32 bytes)`

This is the slow password-stretching step. The master key is stored in
`self._passphrase_key` for the backend's lifetime.

**Phase 2 — Expand (per operation)**:
`HKDF(SHA256, salt=random_16_bytes, info=b"adk-fernet-v2", length=32).derive(master_key) -> per_op_key`

A fresh 16-byte random salt is generated per `sync_encrypt()` call via
`os.urandom(16)`. The per-operation key is base64url-encoded to create a valid
Fernet key. HKDF completes in microseconds.

### 2. PBKDF2 Iterations Increased to 600,000

The iteration count is increased from 480,000 to 600,000 to meet OWASP 2023+
guidance. A `_PBKDF2_ITERATIONS_LEGACY = 480_000` constant is retained for
backward-compatible decryption (see below).

### 3. Salt Stored Inside Backend Ciphertext Blob

The salt is embedded in the backend's ciphertext output, not in the envelope
header. This keeps the envelope format `[version][backend_id][ciphertext]`
stable and makes salt a backend-internal detail.

**New ciphertext format** (passphrase mode):

```
[0x01][salt: 16 bytes][fernet_token]
 ^--- SALT_MARKER
```

**Legacy ciphertext format** (pre-3.2 or direct-key mode):

```
[fernet_token]
 ^--- starts with base64url character (>= 0x2B)
```

### 4. Backward Compatibility via Marker Byte Detection

`sync_decrypt()` checks the first byte of the ciphertext:

- `0x01` with length >= 117: new format. Extract salt, derive per-op key via
  HKDF from the 600k master key, decrypt the Fernet token.
- `>= 0x2B`: legacy format. Delegate to the legacy Fernet instance (derived at
  init with 480k iterations and fixed salt).
- Otherwise: raise `DecryptionError`.

At init, the backend derives both:
- `self._passphrase_key`: PBKDF2 at 600,000 iterations (for new data)
- `self._legacy_fernet`: Fernet from PBKDF2 at 480,000 iterations (for old data)

This adds ~0.6 s to backend construction (two PBKDF2 calls) but is a one-time
cost for a long-lived service.

## Alternatives Considered

### A. Per-operation PBKDF2 with random salt

**Rejected.** PBKDF2 at 600,000 iterations takes ~0.3--0.5 s per call. Running
it per encrypt/decrypt would cause unacceptable latency in session services.

### B. HKDFExpand instead of full HKDF

**Rejected.** `HKDFExpand` has no `salt` parameter; the random salt would need
to be concatenated into the `info` field. Full `HKDF` uses `salt` as intended
by RFC 5869 for proper domain separation at negligible additional cost (one
extra HMAC call).

### C. Salt in envelope header

**Rejected.** Extending the envelope format `[version][backend_id][salt][...]`
would break the wire protocol and require all backends to handle salt, even
those that don't use key derivation (e.g., AES-GCM). Salt is a backend-specific
concern.

### D. New backend ID for salted Fernet

**Rejected.** Assigning `0x03` for "Fernet with salt" would split Fernet data
across two backend IDs, complicating multi-backend dispatch. The marker byte
inside the ciphertext blob is sufficient for format detection.

### E. Defer iteration count bump

**Rejected.** The project has minimal adoption, so backward compatibility cost
is near-zero. Shipping per-key salt without meeting OWASP iteration guidance
would be a half-measure. Both improvements share the same detection mechanism,
adding no extra complexity.

## Consequences

### Positive

- Identical passphrases now produce different ciphertexts (precomputation
  resistance).
- PBKDF2 iterations meet OWASP 2023+ guidance.
- Backward-compatible: pre-3.2 data decrypts transparently.
- Envelope format unchanged; no impact on AES-GCM or future backends.
- Pattern consistent with AES-GCM's nonce-in-ciphertext approach.

### Negative

- Backend construction is ~0.6 s slower in passphrase mode (two PBKDF2 calls).
- Each passphrase-mode encryption creates a temporary `Fernet` instance.
- Legacy iteration count (480,000) is frozen; future bumps require a new
  constant.

### Neutral

- Direct-key mode (pre-generated Fernet keys) is completely unaffected.
- The `EncryptionBackend` protocol, serialization layer, and service layer
  require no changes.
