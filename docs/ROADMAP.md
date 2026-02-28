# Roadmap

## Vision

adk-secure-sessions provides the missing encryption layer for Google ADK's session storage. Any developer building ADK agents that handle sensitive data should be able to `pip install adk-secure-sessions`, swap one line, and have encrypted sessions — with the option to plug in enterprise key management when compliance demands it.

## Phases

### Phase 1: Core — Encryption Engine

Build the core encryption engine: `EncryptedSessionService` with Fernet encryption and SQLite storage.

**Status:** Complete

- [x] `EncryptionBackend` protocol (`protocols.py`) — structural subtyping via PEP 544
- [x] Unit tests for protocol conformance (`tests/unit/test_protocols.py`)
- [x] `FernetBackend` implementation (`backends/fernet.py`)
- [x] Exception hierarchy (`exceptions.py`)
- [x] Serialization layer — encrypt/decrypt at JSON boundary (`serialization.py`)
- [x] `EncryptedSessionService` implementing `BaseSessionService` (`services/encrypted_session.py`)
  - [x] `create_session` with encrypted state
  - [x] `get_session` with decrypted state
  - [x] `list_sessions` with decrypted state
  - [x] `delete_session`
  - [x] `append_event` with encrypted state delta + event data
- [x] Integration test: full round-trip (create → append events → get → verify decryption)
- [x] CI: GitHub Actions (lint, type check, test)
- [x] Connection pooling and cleanup (`close()`, `__aenter__`/`__aexit__`)

### Phase 2: Ship — PyPI Launch

The code is done; the product isn't. Ship the existing tested core as a credible, findable, documented package. The urgent work is market presence, not more features.

**Status:** In Progress

- [ ] Trunk-based migration to main (#35)
- [ ] PyPI/TestPyPI publish pipeline (#36)
- [ ] SECURITY.md with responsible disclosure policy
- [ ] README rewrite (compliance gateway positioning, quick-start, badges)
- [ ] py.typed marker + pyproject.toml extras skeleton
- [ ] Clean test suite output (zero warnings)
- [ ] Docstring Examples sections on public API
- [ ] MkDocs documentation site (API ref + ADRs + envelope spec + FAQ) (#11)
- [ ] Community announcement (GitHub Discussion post)

### Phase 3: Expand — Growth Features

Features that make the library competitive and enterprise-ready.

- [ ] AES-256-GCM encryption backend (#16)
- [ ] Per-key random salt replacing fixed PBKDF2 salt (#17)
- [ ] Key rotation support with envelope-based backend migration (#9)
- [ ] PostgreSQL persistence backend (#9)
- [ ] Performance benchmarks and optimization (#9)
- [ ] SQLAlchemy ORM migration (#20)
- [ ] Stale session detection with optimistic concurrency (#22)
- [ ] CI matrix: test against `google-adk` min + latest
- [ ] Backend authoring documentation and contribution guide
- [ ] Operations guide (key configuration, rotation runbook, monitoring)
- [ ] Test file refactoring (#38, #39)
- [ ] Python 3.13+ support (track google-adk version matrix)

### Phase 4: Enterprise — KMS Backends + Compliance

Enterprise-grade credibility for regulated industries.

- [ ] AWS KMS backend (#10)
- [ ] GCP Cloud KMS backend (#10)
- [ ] HashiCorp Vault integration (#10)
- [ ] SQLCipher full-database encryption option (#10)
- [ ] Audit logging and compliance reporting (#10)
- [ ] FIPS 140-2 deployment documentation
- [ ] Multiple backend examples and migration guides (#10)
