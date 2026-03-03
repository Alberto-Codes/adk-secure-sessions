# Frequently Asked Questions

## What algorithms does Fernet use?

Fernet combines AES-128-CBC for confidentiality with HMAC-SHA256 for integrity,
providing authenticated encryption. The 256-bit Fernet key is split into two
128-bit halves: one for HMAC signing and one for AES encryption. When you
provide an arbitrary passphrase instead of a pre-generated key, it is derived
via PBKDF2-HMAC-SHA256 (480,000 iterations). See the
[Algorithm Documentation](algorithms.md) for full details on parameters, NIST
compliance mapping, and known limitations.

## Is this HIPAA compliant?

Designed to support encryption-at-rest requirements for HIPAA, SOC 2, PCI-DSS,
and GDPR regulated environments. Certification belongs to the deploying
organization. The library provides the encryption primitives and field-level
protection that these frameworks require, but certification is a
whole-organization process that depends on your deployment, access controls, and
operational procedures. A FIPS 140-2 deployment guide is planned for Phase 4 —
see the [Roadmap](ROADMAP.md) for the timeline.

## Why Protocols not ABC?

adk-secure-sessions uses PEP 544 `typing.Protocol` for all public contracts
instead of abstract base classes. With structural subtyping, any class that
implements `encrypt` and `decrypt` methods automatically satisfies the
`EncryptionBackend` contract — no inheritance or registration required. The
`@runtime_checkable` decorator enables `isinstance()` validation at service
startup, so misconfigured backends fail fast with clear error messages. See
[ADR-001: Protocol-Based Interfaces](adr/ADR-001-protocol-based-interfaces.md)
for the full rationale.

## Can I use a different encryption backend?

Yes, and you can do it today. Any class that conforms to the `EncryptionBackend`
protocol (two async methods: `encrypt` and `decrypt`) works as a drop-in
backend. Phase 3 adds an AES-256-GCM backend, and Phase 4 adds AWS KMS, GCP
Cloud KMS, and HashiCorp Vault backends. The
[envelope protocol](envelope-protocol.md) tags every ciphertext with a backend
identifier, so existing Fernet data (backend ID `0x01`) coexists with data from
new backends — migration is zero-downtime with no re-encryption step. See the
[Roadmap](ROADMAP.md) for the full backend upgrade schedule.

## What happens if I use the wrong decryption key?

A `DecryptionError` is always raised. The library never returns garbage data or
silently corrupts session state — wrong-key decryption is treated as an
integrity failure. This is by design: Fernet's HMAC-SHA256 authentication tag
detects both wrong keys and tampered ciphertext before any plaintext is
returned. See the
[exceptions API reference](reference/adk_secure_sessions/exceptions.md) for the
full error hierarchy.

## Does this encrypt the entire database or just session data?

Field-level encryption, not full-database encryption. Session state values
(`user_state`, `app_state`) and event data (conversation history) are encrypted,
while session metadata (`session_id`, `app_name`, `user_id`, timestamps) remains
in plaintext for querying and filtering. This means `list_sessions` can filter
by `app_name` and `user_id` without decrypting every row. See
[ADR-003: Field-Level Encryption](adr/ADR-003-field-level-encryption.md) for the
encryption boundary diagram and trade-off analysis.

## Related

- [Algorithm Documentation](algorithms.md) — encryption algorithms, parameters, and NIST compliance mapping
- [Envelope Protocol](envelope-protocol.md) — binary envelope format and backend coexistence
- [Architecture Decisions](adr/index.md) — all ADRs for the project
- [Roadmap](ROADMAP.md) — planned backends, features, and timeline
