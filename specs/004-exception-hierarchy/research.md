# Research: Exception Hierarchy

**Feature**: 004-exception-hierarchy
**Date**: 2026-02-02

## R-001: Current State of Exception Module

**Decision**: Extend the existing `exceptions.py` rather than creating a new file.

**Rationale**: `exceptions.py` already exists with `SecureSessionError` (base) and `DecryptionError`. The only missing piece from the spec is `EncryptionError`. The existing code follows all project conventions (Google docstrings, no sensitive data in messages).

**Alternatives considered**:
- Rewrite from scratch: Unnecessary — existing code is well-structured and already in production use by `FernetBackend`.

## R-002: EncryptionError Usage

**Decision**: Add `EncryptionError` as a sibling to `DecryptionError`, both inheriting from `SecureSessionError`.

**Rationale**: The spec (FR-004) requires them as siblings. The Fernet backend currently doesn't raise `EncryptionError` (Fernet encryption rarely fails), but future backends (AES-256-GCM per issue #16) may need it. The constitution (Principle V: Minimal Exception Surface) supports adding it now since callers have a concrete need to distinguish encryption from decryption failures in control flow.

**Alternatives considered**:
- Defer `EncryptionError` until a backend needs it: Rejected — the issue explicitly requires it, and it's part of the MVP exception contract.

## R-003: Exception Message Safety

**Decision**: Maintain the existing pattern of generic failure messages without sensitive data.

**Rationale**: Constitution (Principle III, Security Constraints) and spec (FR-006) both require that exception messages never contain key material, ciphertext, or plaintext. The existing `DecryptionError` usage in `fernet.py` already follows this pattern: `"Decryption failed: invalid token or wrong key"`.

**Alternatives considered**: None — this is a hard constraint, not a choice.

## R-004: Public API Exports

**Decision**: Add `EncryptionError` to `__init__.py` `__all__` exports.

**Rationale**: Spec FR-007 requires all three exception classes to be importable from the public API. `SecureSessionError` and `DecryptionError` are already exported.

**Alternatives considered**: None — required by spec.

## R-005: Test Coverage

**Decision**: Add tests for the full hierarchy including `EncryptionError`, hierarchy relationships, and message safety.

**Rationale**: Existing tests in `test_fernet_backend.py` cover `DecryptionError` in context of Fernet operations. Dedicated exception hierarchy tests are needed for: inheritance chain, sibling independence (FR-004), exception chaining (FR-008), and message content safety (FR-006).

**Alternatives considered**: None — standard practice.
