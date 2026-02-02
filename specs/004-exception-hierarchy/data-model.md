# Data Model: Exception Hierarchy

**Feature**: 004-exception-hierarchy
**Date**: 2026-02-02

## Entity Diagram

```text
Exception (stdlib)
└── SecureSessionError          [EXISTS]
    ├── EncryptionError          [NEW]
    └── DecryptionError          [EXISTS]
```

## Entities

### SecureSessionError (exists)

- **Purpose**: Base exception for all adk-secure-sessions errors
- **Parent**: `Exception`
- **Attributes**: `args` (inherited from `Exception`) — message string
- **Constraints**: Messages must not contain sensitive data

### EncryptionError (new)

- **Purpose**: Raised when an encryption operation fails
- **Parent**: `SecureSessionError`
- **Attributes**: `args` (inherited) — message string
- **Constraints**: Messages must not contain sensitive data (key material, plaintext)

### DecryptionError (exists)

- **Purpose**: Raised when decryption fails (wrong key, tampered data, malformed input)
- **Parent**: `SecureSessionError`
- **Attributes**: `args` (inherited) — message string
- **Constraints**: Messages must not contain sensitive data (key material, ciphertext, plaintext)

## Relationships

- `EncryptionError` and `DecryptionError` are **siblings** — neither inherits from the other
- Both are caught by `except SecureSessionError`
- Neither is caught by the other's `except` clause
