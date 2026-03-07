# Story 3.1: AES-256-GCM Encryption Backend

Status: ready-for-dev
Branch: feat/backend-3-1-aes-gcm
GitHub Issue:

## Story

As a security-conscious developer,
I want an AES-256-GCM encryption backend as an alternative to Fernet,
So that I can meet enterprise security requirements that mandate AES-256-GCM or authenticated encryption with associated data (AEAD).

## Acceptance Criteria

1. **Protocol Conformance**: `AesGcmBackend` conforms to the `EncryptionBackend` protocol. `isinstance(AesGcmBackend(...), EncryptionBackend)` returns `True` at runtime.

2. **AES-256-GCM Implementation**: The backend uses AES-256-GCM via `cryptography.hazmat.primitives.ciphers.aead.AESGCM` with 256-bit key, 96-bit nonce (12 bytes), and 128-bit authentication tag. Associated data (`associated_data`) is passed as `None` (AAD binding to session metadata deferred to Story 3.2+).

3. **Nonce Security**: A cryptographically random nonce is generated per encryption operation via `os.urandom(12)`. Nonce is never reused.

4. **Ciphertext Format**: The backend's `encrypt()` returns `nonce (12 bytes) || ciphertext+tag` as a single `bytes` blob. `decrypt()` splits the first 12 bytes as nonce, remainder as ciphertext+tag. Zero-length plaintext produces a valid 28-byte blob (12 nonce + 16 tag).

5. **Backend Registration**: `BACKEND_AES_GCM = 0x02` is registered in `BACKEND_REGISTRY` in `serialization.py`. Envelope format `[0x01][0x02][ciphertext]` round-trips correctly.

6. **Sync Primitive Extraction**: The `EncryptionBackend` protocol gains `sync_encrypt(plaintext: bytes) -> bytes` and `sync_decrypt(ciphertext: bytes) -> bytes` methods. `EncryptedSessionService` uses these protocol methods instead of accessing `backend._fernet` directly (resolves `TODO(epic-3)` at `encrypted_session.py:110-115`).

7. **Backend ID Property**: The `EncryptionBackend` protocol gains a `backend_id: int` read-only property. `AesGcmBackend.backend_id` returns `0x02`. `FernetBackend.backend_id` returns `0x01` (`BACKEND_FERNET`). `EncryptedSessionService` reads `backend.backend_id` instead of accepting a separate `backend_id` parameter.

8. **Async Event Loop Safety**: All cryptography operations are wrapped in `asyncio.to_thread()` in the async methods.

9. **Error Handling**: Wrong-key decryption raises `DecryptionError` (not garbage data). No key material, nonce, or ciphertext appears in error messages.

10. **Configuration Validation**: Constructor validates key is `bytes` of exactly 32 bytes. Invalid keys raise `ConfigurationError`.

11. **Public API Export**: `AesGcmBackend` and `BACKEND_AES_GCM` are exported from `adk_secure_sessions/__init__.py` and listed in `__all__`.

12. **Backward Compatibility**: All existing Fernet tests pass unchanged. `FernetBackend` gains `sync_encrypt`/`sync_decrypt` methods and `backend_id` property without breaking existing behavior.

13. **Documentation**: Google-style docstring with `Examples:` section using fenced code blocks showing initialization (including `AESGCM.generate_key(bit_length=256)` for key generation), encrypt, and decrypt.

## Tasks / Subtasks

- [ ] Task 1: Extend `EncryptionBackend` protocol with sync primitives and backend_id (AC: 6, 7)
  - [ ] 1.1 Add `backend_id` read-only property (`@property def backend_id(self) -> int`) to `protocols.py`
  - [ ] 1.2 Add `sync_encrypt(self, plaintext: bytes) -> bytes` to `protocols.py`
  - [ ] 1.3 Add `sync_decrypt(self, ciphertext: bytes) -> bytes` to `protocols.py`
  - [ ] 1.4 Update protocol docstring with sync method and backend_id documentation

- [ ] Task 2: Add sync primitives and backend_id to `FernetBackend` (AC: 6, 7, 12)
  - [ ] 2.1 Add `backend_id` property returning `BACKEND_FERNET` (`0x01`)
  - [ ] 2.2 Implement `sync_encrypt` on `FernetBackend` (delegates to `self._fernet.encrypt`)
  - [ ] 2.3 Implement `sync_decrypt` on `FernetBackend` (delegates to `self._fernet.decrypt`, catches `InvalidToken`)
  - [ ] 2.4 Verify existing `FernetBackend` tests still pass

- [ ] Task 3: Update `EncryptedSessionService` to use protocol methods (AC: 6, 7)
  - [ ] 3.1 Replace `backend._fernet.encrypt`/`.decrypt` with `backend.sync_encrypt`/`.sync_decrypt` in `encrypted_session.py:110-115`
  - [ ] 3.2 Replace hardcoded `backend_id=BACKEND_FERNET` with `backend.backend_id`
  - [ ] 3.3 Remove `type: ignore[attr-defined]` suppressions
  - [ ] 3.4 Remove the `TODO(epic-3)` comment
  - [ ] 3.5 Run `uv run pytest tests/ -v` -- confirm zero failures before proceeding to Task 4

> **Commit boundary**: Tasks 1-3 should be committed and verified as a standalone change before Tasks 4-6. This prevents sync extraction regressions from being masked by new backend code.

- [ ] Task 4: Implement `AesGcmBackend` (AC: 1, 2, 3, 4, 7, 8, 9, 10, 13)
  - [ ] 4.1 Create `src/adk_secure_sessions/backends/aes_gcm.py`
  - [ ] 4.2 Implement `__init__(self, key: bytes)` with 32-byte validation
  - [ ] 4.3 Implement `backend_id` property returning `BACKEND_AES_GCM` (`0x02`)
  - [ ] 4.4 Implement `sync_encrypt(self, plaintext: bytes) -> bytes` (nonce || AESGCM.encrypt with `associated_data=None`)
  - [ ] 4.5 Implement `sync_decrypt(self, ciphertext: bytes) -> bytes` (split nonce, AESGCM.decrypt with `associated_data=None`)
  - [ ] 4.6 Implement `async encrypt` and `async decrypt` wrapping sync methods in `asyncio.to_thread()`
  - [ ] 4.7 Add Google-style docstring with fenced code examples (include `AESGCM.generate_key(bit_length=256)` for key generation)
  - [ ] 4.8 Validate `isinstance(AesGcmBackend(...), EncryptionBackend)` at runtime

- [ ] Task 5: Register backend in serialization layer (AC: 5)
  - [ ] 5.1 Add `BACKEND_AES_GCM: int = 0x02` constant to `serialization.py`
  - [ ] 5.2 Add entry to `BACKEND_REGISTRY: {0x02: "AES-GCM"}`
  - [ ] 5.3 Export `BACKEND_AES_GCM` from `__init__.py`

- [ ] Task 6: Update public API exports (AC: 10)
  - [ ] 6.1 Export `AesGcmBackend` from `backends/__init__.py`
  - [ ] 6.2 Export `AesGcmBackend` and `BACKEND_AES_GCM` from `adk_secure_sessions/__init__.py`
  - [ ] 6.3 Update `__all__` (alphabetically sorted)

- [ ] Task 7: Write unit tests for `AesGcmBackend` (AC: 1-4, 7-10, 13)
  - [ ] 7.1 Create `tests/unit/test_aes_gcm_backend.py`
  - [ ] 7.2 Test: round-trip encrypt/decrypt (various payloads: empty bytes, small, 10KB)
  - [ ] 7.3 Test: protocol conformance (`isinstance` check)
  - [ ] 7.4 Test: `backend_id` property returns `0x02`
  - [ ] 7.5 Test: wrong-key decryption raises `DecryptionError`
  - [ ] 7.6 Test: tampered ciphertext raises `DecryptionError`
  - [ ] 7.7 Test: non-bytes input raises `TypeError`
  - [ ] 7.8 Test: invalid key size raises `ConfigurationError` (too short, too long, empty)
  - [ ] 7.9 Test: non-bytes key raises `ConfigurationError`
  - [ ] 7.10 Test: nonce uniqueness (100 encryptions of same plaintext produce distinct ciphertexts)
  - [ ] 7.11 Test: ciphertext format (first 12 bytes are nonce, remaining is ciphertext+tag)
  - [ ] 7.12 Test: empty plaintext round-trip -- encrypt `b""` produces 28-byte blob (12 nonce + 16 tag), decrypt returns `b""`
  - [ ] 7.13 Test: cross-backend confusion -- passing Fernet ciphertext to `AesGcmBackend.decrypt()` raises `DecryptionError` (not unhandled `InvalidTag`)
  - [ ] 7.14 Test: interoperability with raw `AESGCM` from `cryptography` library

- [ ] Task 8: Write sync primitive and backend_id tests (AC: 6, 7, 12)
  - [ ] 8.1 Add sync_encrypt/sync_decrypt and backend_id tests to `test_fernet_backend.py`
  - [ ] 8.2 Add sync_encrypt/sync_decrypt and backend_id tests to `test_aes_gcm_backend.py`
  - [ ] 8.3 Update `test_protocols.py` to verify sync methods and backend_id in protocol conformance

- [ ] Task 9: Write serialization integration tests (AC: 5)
  - [ ] 9.1 Test: AES-GCM envelope round-trip via `encrypt_session`/`decrypt_session`
  - [ ] 9.2 Test: envelope byte[1] == 0x02 for AES-GCM encrypted data
  - [ ] 9.3 Test: Fernet-encrypted envelope still decrypts correctly (backward compat)

### Cross-Cutting Test Maturity (Standing Task)

**Test Review Item**: Define module-level constants for repeated test strings
**Severity**: P2 (Medium)
**Location**: `tests/integration/test_adk_crud.py`, `test_adk_encryption.py`, `test_adk_conformance.py` (53 occurrences of `"my-agent"`, `"user-1"`, `"test-app"`)

Magic strings repeated throughout. `test_concurrent_writes.py` and `test_adk_runner.py` correctly define `APP_NAME` and `USER_ID` at module level. Apply same pattern to the 3 split integration files.

- [ ] Define `APP_NAME`, `USER_ID` (and other repeated strings) as module-level constants in `test_adk_crud.py`, `test_adk_encryption.py`, `test_adk_conformance.py`
- [ ] Replace all inline magic string occurrences with the constants
- [ ] Verify new/changed test(s) pass in CI
- [ ] Mark item as done in `_bmad-output/test-artifacts/test-review.md`

## AC-to-Test Mapping

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_aes_gcm_backend.py::test_protocol_conformance` | pending |
| 2    | `test_aes_gcm_backend.py::test_round_trip_*`, `test_interop_with_raw_aesgcm` | pending |
| 3    | `test_aes_gcm_backend.py::test_nonce_uniqueness`, `test_ciphertext_format` | pending |
| 4    | `test_aes_gcm_backend.py::test_ciphertext_format`, `test_empty_plaintext_round_trip` | pending |
| 5    | `test_serialization.py::test_aesgcm_envelope_round_trip`, `test_aesgcm_envelope_backend_id` | pending |
| 6    | `test_protocols.py::test_sync_methods`, `test_fernet_backend.py::test_sync_*`, `test_aes_gcm_backend.py::test_sync_*`, integration tests pass | pending |
| 7    | `test_protocols.py::test_backend_id_property`, `test_aes_gcm_backend.py::test_backend_id`, `test_fernet_backend.py::test_backend_id` | pending |
| 8    | `test_aes_gcm_backend.py::test_round_trip_*` (async tests via pytest-asyncio) | pending |
| 9    | `test_aes_gcm_backend.py::test_wrong_key`, `test_tampered_ciphertext`, `test_cross_backend_confusion` | pending |
| 10   | `test_aes_gcm_backend.py::test_invalid_key_size`, `test_non_bytes_key` | pending |
| 11   | `test_public_api.py` (existing test verifies `__all__` exports) | pending |
| 12   | All existing `test_fernet_backend.py` and integration tests pass | pending |
| 13   | Manual review of docstring; verify `AESGCM.generate_key()` in examples | pending |

## Dev Notes

### Architecture Patterns & Constraints

- **Protocol-based**: `EncryptionBackend` is a `@runtime_checkable` Protocol (PEP 544). No ABC, no inheritance. `AesGcmBackend` just needs matching method signatures.
- **Async-first**: Public `encrypt`/`decrypt` are `async def`. Wrap `cryptography` calls in `asyncio.to_thread()`. New sync primitives are synchronous (used by SQLAlchemy TypeDecorator which runs in sync context).
- **Envelope wire protocol**: `[version_byte][backend_id_byte][ciphertext]`. The backend only produces/consumes the ciphertext portion. Envelope construction/parsing is in `serialization.py`.
- **No custom crypto**: Use `cryptography.hazmat.primitives.ciphers.aead.AESGCM` exclusively. Never implement custom crypto primitives.
- **Exception discipline**: Raise `DecryptionError` (with `DontWrapMixin`) for decrypt failures. Raise `ConfigurationError` for init validation. Exception chaining with `from exc` or `from None`. Message in `msg` variable before `raise`.

### Sync Primitive Extraction (Critical Prerequisite)

The `EncryptedSessionService` at `services/encrypted_session.py:110-115` currently couples to FernetBackend internals:

```python
# Current (broken for multi-backend):
encrypt_fn = backend._fernet.encrypt  # type: ignore[attr-defined]
decrypt_fn = backend._fernet.decrypt  # type: ignore[attr-defined]
```

Must be replaced with protocol methods:

```python
# Target:
encrypt_fn = backend.sync_encrypt
decrypt_fn = backend.sync_decrypt
```

The `EncryptedJSON` TypeDecorator (`services/type_decorator.py`) takes sync callables (`encrypt_fn`, `decrypt_fn`) + `backend_id`. It runs in SQLAlchemy's sync context, so these MUST be synchronous.

### Reference Implementation Pattern (FernetBackend)

Mirror `backends/fernet.py` structure:
- Constructor validates key, stores crypto primitive
- `async encrypt/decrypt` wrap sync operations in `asyncio.to_thread()`
- `sync_encrypt/sync_decrypt` are the raw synchronous operations
- `TypeError` for non-bytes input, `DecryptionError` for crypto failures
- No sensitive data in error messages

### AES-256-GCM Specifics (NIST SP 800-38D)

- **Key**: Exactly 32 bytes (256 bits). Validated at construction.
- **Nonce**: 12 bytes (96 bits), generated via `os.urandom(12)` per encrypt call.
- **Tag**: 128 bits, appended automatically by `AESGCM.encrypt()`.
- **Ciphertext blob layout**: `nonce (12) || ciphertext + tag (variable)`. This is the backend's internal format, opaque to the envelope layer.
- **Minimum ciphertext length on decrypt**: 28 bytes (12 nonce + 16 tag, zero plaintext).
- **Error modes**: `InvalidTag` from `cryptography` library on wrong key or tampered data -> catch and raise `DecryptionError`.

### Key Differences from Fernet

| Aspect | Fernet | AES-GCM |
|--------|--------|---------|
| Key input | `str \| bytes`, auto-derives via PBKDF2 | `bytes` only, exactly 32 bytes, no derivation |
| Nonce/IV | Internal to Fernet (auto-managed) | Explicit: `os.urandom(12)` per encrypt |
| Auth | HMAC-SHA256 (separate) | AEAD tag (integrated) |
| Error type | `InvalidToken` | `InvalidTag` |
| Backend ID | `0x01` | `0x02` |

### backend_id as Protocol Property

The `EncryptionBackend` protocol gains a `backend_id: int` read-only property. Each backend exposes its own ID:
- `FernetBackend.backend_id` -> `BACKEND_FERNET` (`0x01`)
- `AesGcmBackend.backend_id` -> `BACKEND_AES_GCM` (`0x02`)

`EncryptedSessionService` reads `backend.backend_id` instead of accepting a separate parameter. This replaces the hardcoded `backend_id=BACKEND_FERNET` at `encrypted_session.py:120` and prevents caller mismatch bugs.

### Commit Strategy

Tasks 1-3 (protocol extension + sync primitives + service decoupling) form a distinct commit boundary. All tests must pass after Task 3 before proceeding to Tasks 4+ (new backend). This prevents sync extraction regressions from being masked by new backend code.

### Future Considerations (Out of Scope)

- **AAD binding**: AESGCM supports `associated_data` to cryptographically bind ciphertext to session metadata (session_id, app_name). Deferred -- changes the `EncryptionBackend` protocol signature for all backends. Candidate for Story 3.2 or a dedicated security hardening story.
- **AES-GCM-SIV**: Available in `cryptography>=46.0.0`. Survives nonce reuse (nonce-misuse resistant). Future Story 3.x candidate, not this story.

### Peripheral Config Impact

- **`pyproject.toml`**: No new dependencies (uses existing `cryptography>=44.0.0`).
- **`tests/conftest.py`**: May need `aes_gcm_backend` fixture alongside `fernet_backend`.
- **CI/docs/release configs**: No changes needed for this story.
- No peripheral config impact beyond source and test files.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/reference/` | Auto-generated by griffe -- `AesGcmBackend` picked up automatically from `__init__.py` export |
| `docs/ARCHITECTURE.md` | No change needed -- envelope protocol already documents multi-backend support |
| `README.md` | No change in this story -- Story 3.4 will add benchmark references |

### Project Structure Notes

- New backend file: `src/adk_secure_sessions/backends/aes_gcm.py` (mirrors `fernet.py`)
- New test file: `tests/unit/test_aes_gcm_backend.py` (mirrors `test_fernet_backend.py`)
- Modified files: `protocols.py`, `backends/fernet.py`, `backends/__init__.py`, `serialization.py`, `__init__.py`, `services/encrypted_session.py`
- Test modifications: `test_protocols.py`, `test_fernet_backend.py`, `test_serialization.py`, `test_public_api.py`

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` -- Epic 3, Story 3.1 lines 686-706]
- [Source: `_bmad-output/planning-artifacts/architecture.md` -- Phase 3 additions, envelope protocol, backend registration]
- [Source: `docs/adr/ADR-000-strategy-decorator-architecture.md` -- Envelope wire protocol]
- [Source: `docs/adr/ADR-001-protocol-based-interfaces.md` -- Protocol-based design]
- [Source: `docs/adr/ADR-002-async-first.md` -- asyncio.to_thread() wrapping]
- [Source: `docs/adr/ADR-005-exception-hierarchy.md` -- Exception patterns]
- [Source: `src/adk_secure_sessions/services/encrypted_session.py:110-115` -- TODO(epic-3) sync primitive extraction]
- [Source: `src/adk_secure_sessions/services/type_decorator.py` -- EncryptedJSON sync callable interface]
- [Source: Epic 7 retrospective -- DontWrapMixin pattern, code reduction learnings]
- [Source: Epic 1 retrospective -- AC-to-test traceability, blast radius analysis]

## Quality Gates

- [ ] `uv run ruff check .` -- zero lint violations
- [ ] `uv run ruff format --check .` -- zero format issues
- [ ] `uv run ty check` -- zero type errors (src/ only)
- [ ] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage
- [ ] `pre-commit run --all-files` -- all hooks pass

## Code Review

- **Reviewer:**
- **Outcome:**

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
|   |          |         |            |

### Verification

- [ ] All HIGH findings resolved
- [ ] All MEDIUM findings resolved or accepted
- [ ] Tests pass after review fixes
- [ ] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-06 | Story created by SM agent -- comprehensive context engine |
| 2026-03-06 | Party mode review: added backend_id property (AC 7), empty plaintext test (7.12), cross-backend confusion test (7.13), commit boundary note, AESGCM.generate_key() in docs (AC 13), deferred AAD and AES-GCM-SIV |

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
