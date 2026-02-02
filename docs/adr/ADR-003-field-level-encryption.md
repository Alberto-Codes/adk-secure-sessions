# ADR-003: Field-Level Encryption by Default

> **Status**: Accepted
> **Date**: 2026-02-01
> **Deciders**: adk-secure-sessions maintainers

## Context

There are two fundamentally different approaches to encrypting session data:

1. **Full-database encryption** (SQLCipher): Encrypts the entire database file. Everything is opaque on disk. Transparent to the application layer.

2. **Field-level encryption** (Fernet, KMS): Encrypts individual values within the database. Session metadata (app_name, user_id, timestamps) can remain in plaintext for querying, while sensitive state values are encrypted.

Both are valid. The choice affects what users can query, how key management works, and which compliance frameworks are satisfied.

## Decision

**Field-level encryption is the default approach.** The default backend (Fernet) encrypts session **state values** and **event data** while leaving session metadata queryable.

### What Gets Encrypted

| Data | Encrypted | Rationale |
|------|-----------|-----------|
| `state` values (user_state, app_state) | Yes | Contains sensitive user/app data |
| `events` (conversation history) | Yes | Contains user messages, tool outputs, PII |
| `session_id` | No | Needed for lookups |
| `app_name` | No | Needed for filtering/routing |
| `user_id` | No | Needed for filtering/routing |
| `create_time`, `update_time` | No | Needed for expiration/cleanup queries |

### Encryption Boundary

```
┌──────────────────────────────────────────────┐
│              Database Row                     │
│                                               │
│  session_id:  "abc-123"          (plaintext)  │
│  app_name:    "my_agent"         (plaintext)  │
│  user_id:     "user_456"         (plaintext)  │
│  update_time: "2026-02-01T..."   (plaintext)  │
│  state:       "gAAAAA...Bx9k="   (encrypted)  │
│  events:      "gAAAAA...Mw2f="   (encrypted)  │
└──────────────────────────────────────────────┘
```

### Why Not Encrypt Everything

1. **Queryability**: ADK's `list_sessions` filters by `app_name` and `user_id`. Encrypting these would require loading and decrypting every session to filter — O(n) instead of O(1).
2. **Operational needs**: Timestamps are needed for session expiration, cleanup cron jobs, and monitoring dashboards.
3. **Compliance alignment**: HIPAA, SOC 2, and PCI-DSS require encryption of sensitive data (PHI, PII, cardholder data), not necessarily operational metadata. Encrypting everything often exceeds requirements while degrading usability.

### Full-Database Encryption as an Option

SQLCipher support is planned as an alternative backend for users who want everything encrypted regardless. This is additive — users choose based on their threat model:

- **Field-level (default)**: Protects sensitive data, preserves queryability
- **SQLCipher**: Protects everything, requires passphrase management, no query on encrypted fields

## Consequences

### What becomes easier

- **Session listing/filtering**: Metadata queries work without decryption
- **Monitoring**: Operational dashboards can count sessions, check timestamps
- **Migration**: Only state/event columns change; schema remains queryable
- **Debugging**: Session metadata visible for troubleshooting without decryption keys

### What becomes harder

- **Metadata leakage**: An attacker with database access can see who has sessions, when they were active, and which app they used. They cannot see conversation content or state values.
- **User ID sensitivity**: If `user_id` itself is PII (e.g., an email address), users should use opaque identifiers. This is a best practice regardless of encryption.

### Trade-offs

- Field-level encryption adds per-field overhead (Fernet prefix, HMAC, IV per value) vs SQLCipher's single-file overhead. For typical session sizes this is negligible.
- Key management is simpler with field-level (one key encrypts values) vs SQLCipher (passphrase must be provided at connection time).

## Alternatives Considered

### Full-Database Encryption Only

**Not chosen as default.** SQLCipher requires native library installation (`sqlcipher3`), has no async driver, and prevents querying encrypted fields. It's a better fit as an opt-in backend for maximum security requirements.

### Encrypt Everything Including Metadata

**Rejected.** Would break ADK's `list_sessions(app_name=..., user_id=...)` contract. We'd need to implement our own indexing layer, effectively building a custom encrypted database. Out of scope for a session encryption library.

### Let Users Choose Per-Field

**Considered for future.** A field selector (`encrypt_fields=["state", "events"]`) would give granular control. The current default covers the common case. This can be added as a non-breaking enhancement.
