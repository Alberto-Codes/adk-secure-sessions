# Implementation Plan: Serialization Layer

**Branch**: `005-serialization-layer` | **Date**: 2026-02-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-serialization-layer/spec.md`

## Summary

Implement a serialization layer that sits between the session service and encryption backends. It converts Python dicts and JSON strings into self-describing encrypted envelopes (`[version][backend_id][ciphertext]`) using any `EncryptionBackend`-conformant backend. The layer is stateless — four async module-level functions, no classes. A new `SerializationError` exception is added for JSON encoding failures.

## Technical Context

**Language/Version**: Python 3.12 (per `requires-python`)
**Primary Dependencies**: stdlib only (`json`, `asyncio`); uses `EncryptionBackend` protocol from this package
**Storage**: N/A (serialization is in-memory; storage is the session service's responsibility)
**Testing**: pytest + pytest-asyncio + pytest-mock
**Target Platform**: Linux server (async Python runtime)
**Project Type**: Single library package
**Performance Goals**: No blocking of async event loop; overhead limited to 2 bytes per envelope
**Constraints**: No sensitive data in error messages; async-only public API
**Scale/Scope**: 1 new module (~100 LOC), 1 exception class addition, ~150 LOC tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Protocol-Based Interfaces | PASS | Serializer accepts any `EncryptionBackend` conformant object; no new protocol needed (functions, not a class) |
| II. Async-First | PASS | All four public functions are `async def` |
| III. Field-Level Encryption | PASS | Encrypts at the JSON boundary per ADR-003; metadata stays plaintext |
| IV. ADK Interface Compatibility | PASS | No ADK imports; works with `model_dump_json()` output as opaque strings |
| V. Minimal Exception Surface | PASS | One new exception (`SerializationError`) with concrete control-flow justification: distinguishes "bad input" from "crypto failure" |
| VI. Simplicity & YAGNI | PASS | Module-level functions, no class, no registry auto-detection, backend_id passed by caller |

**Security Constraints**:
- No key material in errors: PASS (serializer never touches keys)
- Self-describing format: PASS (2-byte envelope header per ADR-004)
- Authenticated encryption: N/A (delegated to backend)

## Project Structure

### Documentation (this feature)

```text
specs/005-serialization-layer/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research decisions
├── data-model.md        # Envelope format and data flow
├── quickstart.md        # Usage examples
├── contracts/
│   └── serialization.py # Function signatures
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/adk_secure_sessions/
├── __init__.py              # Add SerializationError + serialization re-exports
├── exceptions.py            # Add SerializationError class
└── serialization.py         # NEW: encrypt_session, decrypt_session, encrypt_json, decrypt_json

tests/unit/
├── test_serialization.py    # NEW: round-trip, envelope format, error cases
└── test_exceptions.py       # Update: add SerializationError tests
```

**Structure Decision**: Single module `serialization.py` at the package root (not a sub-package). The serialization layer is a thin coordination layer between JSON and encryption — it doesn't warrant its own directory.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
