# Implementation Plan: Implement FernetBackend

**Branch**: `003-fernet-backend` | **Date**: 2026-02-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-fernet-backend/spec.md`

## Summary

Implement `FernetBackend`, a symmetric-key encryption backend using `cryptography.fernet.Fernet` that conforms to the `EncryptionBackend` protocol. The backend accepts string or bytes keys, derives valid Fernet keys via PBKDF2, and provides async `encrypt`/`decrypt` methods. A `DecryptionError` exception is introduced under the project's minimal exception hierarchy.

## Technical Context

**Language/Version**: Python 3.12 (per `requires-python`)
**Primary Dependencies**: `cryptography>=44.0.0` (already in `pyproject.toml`)
**Storage**: N/A (in-memory encryption only)
**Testing**: pytest + pytest-asyncio + pytest-mock (async tests, auto mode)
**Target Platform**: Cross-platform Python library
**Project Type**: Single Python package
**Performance Goals**: N/A — Fernet is CPU-bound; correctness over speed
**Constraints**: Async interface required; no sync wrappers; key material must not leak into exceptions/logs
**Scale/Scope**: Single module + exception class + tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Protocol-Based Interfaces | ✅ PASS | FernetBackend structurally conforms to `EncryptionBackend` protocol; no inheritance required |
| II. Async-First | ✅ PASS | `encrypt`/`decrypt` are `async def`; Fernet CPU-bound ops wrapped with `asyncio.to_thread()` |
| III. Field-Level Encryption | ✅ PASS | Backend provides the encryption primitive; field-level usage is higher-layer concern |
| IV. ADK Interface Compatibility | ✅ PASS | No ADK interface changes; backend is used by session service layer |
| V. Minimal Exception Surface | ✅ PASS | Single `DecryptionError` inheriting from `SecureSessionError`; added only because callers need to catch decryption failures distinctly |
| VI. Simplicity & YAGNI | ✅ PASS | Minimal implementation: one class, one exception, key derivation via PBKDF2 |

**Security Constraints Check**:
- ✅ Key material excluded from exceptions and logs
- ⚠️ Self-describing ciphertext format (version byte + backend ID) — deferred to session service layer per constitution; FernetBackend returns raw Fernet tokens
- ✅ Fernet provides authenticated encryption (AES-128-CBC + HMAC-SHA256)

All gates pass. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-fernet-backend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── fernet-backend-api.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/adk_secure_sessions/
├── __init__.py              # Add FernetBackend + DecryptionError exports
├── protocols.py             # Existing EncryptionBackend protocol
├── exceptions.py            # NEW: SecureSessionError, DecryptionError
└── backends/
    ├── __init__.py          # NEW: Package init
    └── fernet.py            # NEW: FernetBackend implementation

tests/unit/
├── test_protocols.py        # Existing protocol tests
└── test_fernet_backend.py   # NEW: FernetBackend tests
```

**Structure Decision**: Backends live in `src/adk_secure_sessions/backends/` subpackage. Exceptions get their own module `exceptions.py` at package root since they'll be shared across all backends. This follows the existing flat structure while adding minimal nesting only where needed (backends).
