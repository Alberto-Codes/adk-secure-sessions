# ADR-001: Protocol-Based Interfaces

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

The encryption backend system needs a contract that backend implementations must satisfy. Python offers several ways to define interfaces:

1. Abstract Base Classes (`abc.ABC`)
2. Structural subtyping (`typing.Protocol`)
3. Duck typing (no formal contract)
4. Zope/interface-style interfaces

We need an approach that is:
- Easy for third-party developers to implement (low friction)
- Statically verifiable by type checkers
- Consistent with modern Python practices and the ADK ecosystem

## Decision

Use **`typing.Protocol`** (PEP 544) for all public interfaces.

### Core Protocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class EncryptionBackend(Protocol):
    """Contract for all encryption backends."""

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes."""
        ...

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes."""
        ...
```

### Design Principles

1. **Structural subtyping**: Implementors don't need to inherit from or register with our protocol. Any class with matching `encrypt` and `decrypt` methods satisfies the contract.

2. **`@runtime_checkable`**: Enables `isinstance()` checks for validation at service initialization, providing clear error messages when a backend doesn't conform.

3. **Minimal surface**: The protocol defines the absolute minimum — `encrypt` and `decrypt`. Optional capabilities (key rotation, metadata, batch operations) are separate protocols that backends can optionally implement.

### Optional Capability Protocols

```python
class SupportsKeyRotation(Protocol):
    """Backend that supports key rotation."""

    async def rotate_key(self, new_key: bytes) -> None: ...


class SupportsMetadata(Protocol):
    """Backend that provides encryption metadata."""

    def get_metadata(self) -> EncryptionMetadata: ...
```

The session service can check for optional capabilities:

```python
if isinstance(self.backend, SupportsKeyRotation):
    await self.backend.rotate_key(new_key)
```

## Consequences

### What becomes easier

- **Third-party backends**: Anyone can implement `encrypt`/`decrypt` without importing our package
- **Type checking**: `ty`, `mypy`, `pyright` all verify protocol conformance statically
- **Testing**: Create a mock with two methods — no base class or registration needed
- **Composition**: Backends can implement multiple protocols for optional features

### What becomes harder

- **Discovery**: No base class to `grep` for — implementors need to read the protocol docs
- **Runtime validation**: Structural typing checks method signatures, not semantics. A backend could implement `encrypt` that doesn't actually encrypt. Tests and integration validation cover this gap.

## Alternatives Considered

### Abstract Base Classes (`abc.ABC`)

**Rejected.** Requires inheritance (`class MyBackend(EncryptionBackend)`), which couples third-party code to our package at import time. Protocols allow structural ("duck type") conformance without inheritance.

### Duck Typing (No Contract)

**Rejected.** No static analysis support, no documentation of the expected interface, runtime `AttributeError` instead of clear error messages. Protocols give us duck typing's flexibility with static typing's safety.
