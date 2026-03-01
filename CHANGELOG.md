# Changelog

## [1.0.0](https://github.com/Alberto-Codes/adk-secure-sessions/releases/tag/v1.0.0) (2026-03-01)

### Features

* **session:** EncryptedSessionService — drop-in replacement for ADK's BaseSessionService with field-level encryption at rest
* **encryption:** Fernet symmetric encryption backend (AES-128-CBC + HMAC-SHA256) with async-first design
* **serialization:** Self-describing binary envelope format with version and backend metadata for future key rotation
* **persistence:** Async SQLite persistence via aiosqlite with own schema, independent of ADK internals
* **validation:** ConfigurationError with startup-time passphrase and backend validation
* **security:** Coordinated disclosure policy (SECURITY.md), Apache-2.0 license, zero-CVE dependency audit
* **ci:** Automated PyPI releases via OIDC trusted publishing — no stored tokens, changelog generation via release-please
