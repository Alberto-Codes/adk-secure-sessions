# Implementation Plan: Exception Hierarchy

**Branch**: `004-exception-hierarchy` | **Date**: 2026-02-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-exception-hierarchy/spec.md`

## Summary

Complete the exception hierarchy by adding `EncryptionError` to the existing `exceptions.py` module (which already has `SecureSessionError` and `DecryptionError`), exporting it from the public API, and adding dedicated hierarchy tests. This is a small, focused change with no new dependencies.

## Technical Context

**Language/Version**: Python 3.12 (per `requires-python` in pyproject.toml)
**Primary Dependencies**: None — stdlib only (exceptions are plain Python classes)
**Storage**: N/A
**Testing**: pytest + pytest-asyncio (existing test infrastructure)
**Target Platform**: Library (any platform supporting Python 3.12+)
**Project Type**: Single Python package
**Performance Goals**: N/A (exception classes have no runtime overhead)
**Constraints**: No sensitive data in exception messages (constitution + spec)
**Scale/Scope**: 3 files modified/created, ~50 lines of new code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Protocol-Based Interfaces | N/A | Exceptions are not protocol interfaces |
| II. Async-First | N/A | Exception classes don't have methods |
| III. Field-Level Encryption | PASS | FR-006: messages exclude sensitive data |
| IV. ADK Interface Compatibility | N/A | Exceptions are internal to library |
| V. Minimal Exception Surface | PASS | Adding `EncryptionError` per concrete caller need (issue #4); three classes total |
| VI. Simplicity & YAGNI | PASS | Minimum viable: one new class, no abstractions |
| Security Constraints | PASS | No key material in messages (FR-006, FR-008) |
| Development Workflow | PASS | Will pass ruff, type check, pytest |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-exception-hierarchy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/adk_secure_sessions/
├── __init__.py          # MODIFY: add EncryptionError export
└── exceptions.py        # MODIFY: add EncryptionError class

tests/unit/
└── test_exceptions.py   # NEW: hierarchy + safety tests
```

**Structure Decision**: Extends existing single-package layout. No new directories needed.

## Implementation Notes

### What Already Exists

- `SecureSessionError` and `DecryptionError` in `exceptions.py` — well-structured, follows conventions
- `DecryptionError` already used by `FernetBackend.decrypt()` in `backends/fernet.py`
- Both classes exported from `__init__.py`

### What Needs to Be Done

1. Add `EncryptionError(SecureSessionError)` to `exceptions.py` with Google-style docstring
2. Add `EncryptionError` to `__init__.py` exports (both import and `__all__`)
3. Create `tests/unit/test_exceptions.py` covering:
   - Inheritance chain (`issubclass` checks)
   - Sibling independence (`EncryptionError` is not `DecryptionError`)
   - Catch-all via `SecureSessionError`
   - Exception chaining (`raise ... from ...`)
   - Message content (no sensitive data patterns)

### What Should NOT Be Done

- Do not modify `FernetBackend` — it doesn't need `EncryptionError` yet (Fernet encrypt rarely fails)
- Do not add structured metadata, error codes, or context dicts to exceptions
- Do not add convenience methods or properties to exception classes
