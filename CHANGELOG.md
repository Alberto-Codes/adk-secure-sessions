# Changelog

## [1.0.1](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v1.0.0...v1.0.1) (2026-03-02)


### Bug Fixes

* **ci:** fix broken badges and add Codecov integration ([ab36b45](https://github.com/Alberto-Codes/adk-secure-sessions/commit/ab36b45b3ca8b0cd8a0f019b59bca227877b4db4))
* **ci:** upgrade classifier to Beta and add check-url to PyPI publish ([fc4f389](https://github.com/Alberto-Codes/adk-secure-sessions/commit/fc4f3897dcb7ffd2a669a634b31b325f290e8b3e))

## [1.0.0](https://github.com/Alberto-Codes/adk-secure-sessions/releases/tag/v1.0.0) (2026-03-01)

### Features

* **session:** EncryptedSessionService — drop-in replacement for ADK's BaseSessionService with field-level encryption at rest
* **encryption:** Fernet symmetric encryption backend (AES-128-CBC + HMAC-SHA256) with async-first design
* **serialization:** Self-describing binary envelope format with version and backend metadata for future key rotation
* **persistence:** Async SQLite persistence via aiosqlite with own schema, independent of ADK internals
* **validation:** ConfigurationError with startup-time passphrase and backend validation
* **security:** Coordinated disclosure policy (SECURITY.md), Apache-2.0 license, zero-CVE dependency audit
* **ci:** Automated PyPI releases via OIDC trusted publishing — no stored tokens, changelog generation via release-please
