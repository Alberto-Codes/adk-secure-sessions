# Roadmap

## Vision

adk-secure-sessions provides the missing encryption layer for Google ADK's session storage. Any developer building ADK agents that handle sensitive data should be able to `pip install adk-secure-sessions`, swap one line, and have encrypted sessions — with the option to plug in enterprise key management when compliance demands it.

## Phases

### Phase 1: Core Encryption + Fernet MVP

Ship a working `EncryptedSessionService` with Fernet encryption and SQLite storage. This is the minimum viable product — enough for developers to use in local development, demos, and small deployments.

- [ ] `EncryptionBackend` protocol (`protocols.py`)
- [ ] `FernetBackend` implementation (`backends/fernet.py`)
- [ ] Exception hierarchy (`exceptions.py`)
- [ ] Serialization layer — encrypt/decrypt at JSON boundary (`serialization.py`)
- [ ] `EncryptedSessionService` implementing `BaseSessionService` (`services/encrypted_session.py`)
  - [ ] `create_session` with encrypted state
  - [ ] `get_session` with decrypted state
  - [ ] `list_sessions` with decrypted state
  - [ ] `delete_session`
  - [ ] `append_event` with encrypted state delta + event data
- [ ] Unit tests for all components
- [ ] Integration test: full round-trip (create → append events → get → verify decryption)
- [ ] CI: GitHub Actions (lint, type check, test)

### Phase 2: Hardening + PostgreSQL

Production readiness. Key rotation, Postgres support, better error handling, performance validation.

- [ ] Key rotation support (decrypt with old key, re-encrypt with new key)
- [ ] PostgreSQL backend (async SQLAlchemy)
- [ ] Connection pooling and cleanup (`close()`, `__aenter__`/`__aexit__`)
- [ ] Stale session detection (match ADK's staleness check in `append_event`)
- [ ] Performance benchmarks (encryption overhead vs plaintext ADK services)
- [ ] CI matrix: test against `google-adk` min + latest

### Phase 3: KMS Backends + Compliance

Enterprise encryption backends for regulated industries.

- [ ] AWS KMS backend
- [ ] GCP KMS backend
- [ ] HashiCorp Vault backend
- [ ] SQLCipher full-database encryption backend
- [ ] Audit logging (which keys were used, when rotation occurred)
- [ ] Compliance documentation (HIPAA, SOC 2, PCI-DSS mapping)

### Phase 4: Documentation, Examples, PyPI Release

Polish and publish.

- [ ] MkDocs documentation site
- [ ] Quick start guide with ADK agent example
- [ ] Backend comparison guide (Fernet vs KMS vs SQLCipher)
- [ ] Migration guide (from plaintext ADK sessions to encrypted)
- [ ] Publish to PyPI
- [ ] Publish to TestPyPI for pre-release testing
