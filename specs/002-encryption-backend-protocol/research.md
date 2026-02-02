# Research: EncryptionBackend Protocol

**Feature**: 002-encryption-backend-protocol
**Date**: 2026-02-01

## R1: typing.Protocol with @runtime_checkable

**Decision**: Use `typing.Protocol` with `@runtime_checkable` for the
`EncryptionBackend` contract.

**Rationale**: PEP 544 structural subtyping allows third-party
implementations without inheritance or import-time coupling. The
`@runtime_checkable` decorator enables `isinstance()` checks for
fail-fast validation at service initialization. This is the approach
documented in ADR-001.

**Alternatives considered**:
- `abc.ABC`: Requires inheritance, coupling third-party code to our
  package. Rejected per ADR-001.
- Duck typing (no contract): No static analysis, runtime
  `AttributeError` instead of clear errors. Rejected per ADR-001.

## R2: @runtime_checkable limitations

**Decision**: Document known limitations rather than work around them.

**Rationale**: Python's `@runtime_checkable` only checks that methods
exist on the class — it does not verify:
- Parameter types (a method accepting `str` instead of `bytes` passes)
- Return types
- Whether methods are coroutines (`async def`) vs regular functions

These are fundamental Python limitations, not bugs in our design.
Static type checkers (mypy, pyright) catch all of these at analysis
time. Attempting runtime workarounds (e.g., `inspect.iscoroutinefunction`
checks) would add complexity for minimal benefit since the real
validation happens at the type-checker level.

**Alternatives considered**:
- Custom `__init_subclass__` validation: Over-engineering for a
  protocol class. Violates Simplicity & YAGNI principle.
- Runtime signature inspection: Fragile and not part of the Protocol
  contract. Would break structural subtyping guarantees.

## R3: Module placement

**Decision**: `src/adk_secure_sessions/protocols.py`

**Rationale**: Matches the file location specified in GitHub Issue #2
and follows standard Python package conventions. A single `protocols`
module is sufficient for the core `EncryptionBackend` protocol. Future
optional capability protocols (`SupportsKeyRotation`,
`SupportsMetadata`) can be added to the same module since they are
conceptually related and the file will remain small.

**Alternatives considered**:
- `src/adk_secure_sessions/interfaces.py`: "Interfaces" is Java
  terminology; "protocols" is the Python-native term.
- `src/adk_secure_sessions/types.py`: Ambiguous — could be confused
  with type aliases or custom types.

## R4: Docstring content

**Decision**: Include a module-level docstring and a class-level
docstring that explicitly documents the contract, usage example,
and known `@runtime_checkable` limitations.

**Rationale**: SC-001 requires a developer to implement a conforming
backend in under 5 minutes from reading the protocol definition alone.
The docstring is the primary documentation surface for this.
