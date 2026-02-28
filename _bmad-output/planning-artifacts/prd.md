---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
lastStep: 'step-11-polish'
lastSaved: '2026-02-28'
lastEdited: '2026-02-28'
editHistory:
  - date: '2026-02-28'
    changes: 'Post-validation fixes: resolved 2 phase contradictions in journey table, strengthened FR15/FR33 measurability, added FR56 (published roadmap), improved 7 NFRs (NFR1/11/12/14/25/26/27), added audit & key compromise sections to domain requirements'
classification:
  projectType: 'developer_tool'
  domain: 'security_encryption'
  complexity: 'high'
  projectContext: 'brownfield'
  prdScope: 'full_product_vision_all_phases'
inputDocuments:
  - '_bmad-output/project-context.md'
  - 'docs/ARCHITECTURE.md'
  - 'docs/ROADMAP.md'
  - 'docs/project-overview.md'
  - 'docs/source-tree-analysis.md'
  - 'docs/development-guide.md'
  - 'docs/adr/ADR-000-strategy-decorator-architecture.md'
  - 'docs/adr/ADR-001-protocol-based-interfaces.md'
  - 'docs/adr/ADR-002-async-first.md'
  - 'docs/adr/ADR-003-field-level-encryption.md'
  - 'docs/adr/ADR-004-adk-schema-compatibility.md'
  - 'docs/adr/ADR-005-exception-hierarchy.md'
  - 'specs/002-encryption-backend-protocol/research.md'
  - 'specs/003-fernet-backend/research.md'
  - 'specs/004-exception-hierarchy/research.md'
  - 'specs/005-serialization-layer/research.md'
  - 'specs/006-encrypted-session-service/research.md'
  - '_bmad-output/test-artifacts/test-review.md'
  - 'GitHub Issues: #1, #9, #10, #11, #16, #17, #20, #22, #35, #36, #38, #39, #40'
documentCounts:
  briefs: 0
  research: 5
  projectDocs: 16
  projectContext: 1
  otherArtifacts: 2
  githubIssues: 13
workflowType: 'prd'
---

# Product Requirements Document - adk-secure-sessions

**Author:** Alberto-Codes
**Date:** 2026-02-28

## Executive Summary

This PRD covers the full product vision for adk-secure-sessions across four phases, targeting approval to begin Phase 2 (Ship) — publishing the existing tested core to PyPI with documentation and compliance positioning.

adk-secure-sessions is a compliance gateway for Google's Agent Development Kit (ADK), the open-source framework for building AI agents. It provides drop-in encrypted session storage that enables ADK adoption in regulated markets — healthcare, finance, government — where unencrypted session data is a non-starter. Developers replace one import (`EncryptedSessionService` for `BaseSessionService`) and gain field-level encryption at rest with zero rearchitecture.

The library targets two user segments along a single growth path: solo developers prototyping ADK agents with SQLite who need encryption without ceremony, and enterprise teams running Postgres with compliance mandates who need pluggable KMS backends and key rotation. Both segments use the same API surface — the backend system scales underneath.

OpenAI's Agents SDK already ships first-party `EncryptedSession` (Fernet, HKDF, wrapper pattern), validating that encrypted sessions are table-stakes infrastructure for agent frameworks. Google ADK has no equivalent. adk-secure-sessions is the first — and currently only — community solution filling this gap. The competitive window exists until Google adds native encryption support, and the project must establish market presence before that happens.

Phase 1 (core encryption engine) is code-complete and tested: Fernet backend, async-first design, self-describing binary envelope protocol, protocol-based pluggable interfaces, and a full `BaseSessionService` implementation with SQLite persistence. The urgent work is not more features — it is market presence. The project must ship to PyPI with documentation and positioning before the ecosystem window closes.

### What Makes This Special

**Compliance enabler, not encryption utility.** The value proposition isn't "we encrypt bytes" — it's "you can now say YES to the compliance checklist and ship ADK agents in regulated environments."

**Self-describing envelope protocol.** Every piece of encrypted data carries a `[version_byte][backend_id_byte][ciphertext]` header. This enables key rotation and backend migration without re-encrypting existing data — infrastructure that "50 lines of Fernet" can never provide.

**Protocol-based pluggability.** PEP 544 `@runtime_checkable` Protocols (not inheritance) define the backend contract. Third parties can plug in AWS KMS, HashiCorp Vault, or any encryption provider without touching library internals. This is the long-term moat — the Switzerland option while any future Google-native solution will likely be opinionated toward Cloud KMS/Tink.

**Complete core, day one.** Phase 1 ships as a tested encryption engine — 86 passing tests, 90/100 test quality score, full async coverage. This isn't a beta or proof of concept. Compliance-conscious teams evaluating the library find a production-grade foundation from the first release.

## Project Classification

| Dimension | Classification |
|-----------|---------------|
| **Project Type** | Developer Tool (Python library) |
| **Domain** | Security & Encryption |
| **Complexity** | High — cryptographic correctness, async concurrency, upstream compatibility matrix, protocol-based extension system |
| **Project Context** | Brownfield — Phase 1 core engine complete (8 source files, ~1400 LOC, 86 tests, 90/100 test quality score). Phases 2-4 planned. |
| **PRD Scope** | Full product vision, all phases |
| **Phases** | 4 (entering Phase 2 — Ship) |

### Document Map

| Section | Content |
|---------|---------|
| Success Criteria | User, business, and technical success metrics |
| Product Scope | MVP/Growth/Vision feature overview |
| User Journeys | 5 persona narratives with requirements mapping |
| Domain-Specific Requirements | Compliance, technical constraints, integration, security risks |
| Innovation & Novel Patterns | Market positioning, competitive landscape, validation |
| Developer Tool Specific Requirements | Platform matrix, API surface, documentation architecture |
| Project Scoping & Phased Development | Execution sequence, phase details, decision log, risk mitigation |
| Functional Requirements | 55 FRs across 9 capability areas |
| Non-Functional Requirements | 28 NFRs across 6 quality categories |

### Glossary

| Term | Definition |
|------|-----------|
| **ADK** | Google Agent Development Kit — open-source framework for building AI agents |
| **Backend** | An implementation of the EncryptionBackend protocol that performs encrypt/decrypt operations (e.g., FernetBackend, future AES-256-GCM backend) |
| **Backend ID** | Single-byte identifier in the envelope header that identifies which encryption backend produced the ciphertext |
| **BaseSessionService** | ADK's built-in session storage class; EncryptedSessionService extends this |
| **Compliance gateway** | Product positioning: the library enables organizations to satisfy encryption-at-rest compliance requirements for ADK agents |
| **Envelope protocol** | Self-describing binary format `[version_byte][backend_id_byte][ciphertext]` wrapping all encrypted data |
| **Field-level encryption** | Encrypting individual data fields (session state, events) before persistence, rather than encrypting the entire database |
| **Fernet** | Symmetric encryption scheme using AES-128-CBC + HMAC-SHA256 with PBKDF2 key derivation; provided by the `cryptography` library |
| **Protocol (PEP 544)** | Python structural typing mechanism; `@runtime_checkable` enables `isinstance()` checks without inheritance |
| **Wire protocol** | A defined binary format for data interchange; the envelope is treated as a stable wire protocol, not an implementation detail |

## Success Criteria

### User Success

- **5-minute integration**: A developer installs via `pip install adk-secure-sessions`, swaps `BaseSessionService` for `EncryptedSessionService`, runs their existing test suite, and confirms encryption is active — all within a single sitting, no rearchitecture required.
- **Compliance sign-off**: A security team reviews the library's architecture (ADRs, documented algorithms, envelope protocol) and approves its use in a regulated environment without requesting structural changes to the application.
- **"Aha!" moments**: First aha is "my tests still pass but sessions are now encrypted." Second aha is "my security reviewer signed off without pushback."

### Business Success

| Timeframe | Target |
|-----------|--------|
| **Launch** | Published on PyPI, MkDocs site live, README positions compliance gateway narrative |
| **3-month** | 50-200 weekly PyPI downloads, 50+ GitHub stars, presence in ADK community channels |
| **12-month** | 500+ weekly PyPI downloads, 200+ GitHub stars, listed in "awesome-adk" or equivalent curated lists, 1-2 conference/blog mentions |

**North star metric**: Inbound issues and pull requests from strangers — community members requesting new backends (AWS KMS, Vault) or contributing code. This signals the architecture resonated and the community is investing in the project's future.

### Technical Success

- **Test coverage**: ≥90% line coverage maintained across all phases. No regression from current baseline (86 tests, 90/100 quality score).
- **Zero critical security findings**: SonarQube clean on OWASP categories. Dependency CVEs patched within 48 hours.
- **ADK compatibility matrix**: Tests pass against google-adk 1.22.0 and latest on every release. Breaking on either end is a trust-destroying event for downstream users.
- **Encryption correctness**: Wrong-key decryption always raises `DecryptionError`, never returns garbage data. Round-trip integrity verified on every CI run.
- **Release cadence**: Minimum one release per quarter post-launch. A dormant security library signals abandonment to compliance-conscious evaluators.

### Measurable Outcomes

| Outcome | Metric | Target |
|---------|--------|--------|
| Integration speed | Time from `pip install` to encrypted sessions running | < 5 minutes |
| Adoption | Weekly PyPI downloads at 12 months | 500+ |
| Community health | External contributors or issue reporters | 5+ within 12 months |
| Quality | Test coverage | ≥ 90% line coverage |
| Security posture | Critical/high SonarQube findings | 0 |
| Compatibility | ADK version matrix | 1.22.0 through latest passing |

## Product Scope

This section provides a high-level overview of each phase. See the Project Scoping & Phased Development section below for the detailed execution sequence, decision log, and risk mitigation strategy.

### MVP — Minimum Viable Product (Phase 1: Core + Phase 2: Ship)

Phase 1 core engine is code-complete. MVP is the existing engine plus the go-to-market work to make it publicly available and credible:

- **Already done**: EncryptionBackend protocol, FernetBackend, exception hierarchy, serialization layer with envelope protocol, EncryptedSessionService with SQLite, 86 passing tests
- **Ship work**: PyPI/TestPyPI publish pipeline (#36), trunk-based migration to main (#35), MkDocs documentation site (#11), SECURITY.md with responsible disclosure policy, README rewrite with compliance gateway positioning
- **Compliance minimum**: Document encryption algorithms explicitly (Fernet = AES-128-CBC + HMAC-SHA256, PBKDF2 key derivation), ship ADR trail as part of docs, use "designed to support encryption-at-rest requirements for HIPAA, SOC 2, and PCI-DSS regulated environments" positioning — no certification claims

### Growth Features (Post-MVP — Phase 3: Expand)

Features that make the library competitive and enterprise-ready:

- AES-256-GCM encryption backend (#16)
- Per-key random salt replacing fixed PBKDF2 salt (#17)
- Key rotation support with envelope-based backend migration (#9 partial)
- PostgreSQL persistence backend (#9 partial)
- Performance benchmarks and optimization (#9 partial)
- SQLAlchemy ORM migration (#20)
- Stale session detection with optimistic concurrency (#22)

### Vision (Future — Phase 4: Enterprise)

Enterprise-grade credibility:

- AWS KMS and GCP Cloud KMS backends (#10)
- HashiCorp Vault integration (#10)
- SQLCipher full-database encryption option (#10)
- Audit logging and compliance reporting (#10)
- Multiple backend examples and migration guides (#10)

## User Journeys

The following five personas represent the full adoption lifecycle — from discovery through compliance approval to operations. Each journey reveals specific requirements that feed the functional requirements in later sections.

### Journey 1: Priya — Solo ADK Developer (Success Path)

**Situation:** Priya is a machine learning engineer building an ADK-based customer support agent for a fintech startup. She's prototyping with SQLite locally. Her CTO casually mentions: "Make sure session data is encrypted at rest — we'll need that for SOC 2 eventually." She groans internally — she's an ML person, not a crypto person.

**Opening Scene:** Priya searches PyPI for "adk encrypted sessions." She finds adk-secure-sessions, reads the README, and sees "Compliance Gateway for Google ADK" with a code example showing a one-import swap. She thinks: "That can't be real."

**Rising Action:** She runs `pip install adk-secure-sessions`, opens her agent's entry point, and changes `BaseSessionService()` to `EncryptedSessionService(db_url="sessions.db", encryption_key="her-secret-key")`. She runs her test suite. Everything passes. She opens the SQLite file with a hex editor — the session state is unreadable ciphertext. She checks the docs and sees the envelope format explained with a Mermaid diagram.

**Climax:** Priya drops into her CTO's Slack DM: "Sessions are encrypted at rest. Fernet with AES-128-CBC + HMAC-SHA256, PBKDF2 key derivation. Here's the architecture doc." Elapsed time from search to done: 12 minutes.

**Resolution:** The CTO forwards the architecture docs to their compliance consultant. No follow-up questions. Priya goes back to tuning her agent's prompts — the thing she actually cares about. When the startup grows into SOC 2 compliance, the library's pluggable backend system means she can swap to AES-256-GCM or a managed KMS without rearchitecting.

**Reveals requirements for:** PyPI discoverability, README with quick-start code example, one-import integration API, documentation with architecture diagrams, encryption algorithm documentation for compliance forwarding.

**Phase:** MVP (works today with Phase 2: Ship deliverables)

### Journey 2: Marcus — Enterprise Developer (Compliance-Mandated Path)

**Situation:** Marcus is a senior backend engineer at a healthcare company building ADK agents for patient intake automation. His team has a hard compliance requirement: all data at rest must be encrypted with approved algorithms, and the security team must sign off on any third-party library before it enters the dependency tree. He's been told to evaluate ADK's session layer.

**Opening Scene:** Marcus reads ADK's session docs and realizes `DatabaseSessionService` stores session state in plaintext. He opens a Jira ticket: "ADK session storage does not meet HIPAA encryption-at-rest requirements." His tech lead responds: "Find a solution or we can't use ADK."

**Rising Action:** Marcus finds adk-secure-sessions through a Google search. He reads the full documentation site — architecture decision records, the envelope protocol spec, the EncryptionBackend protocol definition. He clones the repo, reads the source code (8 files, ~1400 LOC — auditable in an afternoon), and runs the test suite against his team's ADK version. All 86 tests pass. He writes an internal evaluation document citing the ADRs.

**Climax:** Marcus presents to the security team. They ask three questions: "What algorithm?", "How are keys managed?", and "Can we swap to our KMS later?" He answers all three from the documentation. The security team approves with one condition: migrate to AES-256-GCM when the backend is available. Marcus notes that the envelope protocol supports backend migration without re-encryption of existing data.

**Resolution:** The team integrates adk-secure-sessions into their patient intake agent. Marcus configures it with a team-managed encryption key from their secrets vault. Six months later, when Phase 3 ships the AES-256-GCM backend, he swaps the backend config in one line — existing session data continues to decrypt via the envelope header's backend ID byte.

**Reveals requirements for:** Full documentation site (MkDocs), ADR trail published as docs, source code auditability (small codebase), test suite runnable against multiple ADK versions, clear algorithm documentation, envelope protocol spec, backend migration path documentation.

**Phase:** MVP for evaluation and integration; backend migration beat requires Phase 3: Expand

### Journey 3: Diane — Security/Compliance Reviewer (Evaluation Path)

**Situation:** Diane is an application security engineer at a financial services firm. Marcus's equivalent at her company has proposed adding adk-secure-sessions to their approved dependency list. Her job is to decide: approve, reject, or approve-with-conditions.

**Opening Scene:** Diane opens the GitHub repository. First check: license (MIT — acceptable). Second check: SECURITY.md (responsible disclosure policy present — good sign). Third check: dependency tree (`cryptography` — the standard Python crypto library, not a homebrew solution — acceptable).

**Rising Action:** She reads ADR-003 (Field-Level Encryption) to understand the encryption boundary. She reads the envelope protocol spec and confirms the wire format is self-describing. She runs the test suite and checks coverage — 90%+ with explicit wrong-key decryption tests. She scans the codebase with her internal SAST tools. She reviews the SonarQube findings (zero critical/high).

**Moment of doubt:** Diane pauses at the algorithm choice. Fernet uses AES-128-CBC — her firm's security policy prefers AES-256 for new systems. She's about to write "rejected — insufficient key length" when she reads the architecture docs on the pluggable backend system. The EncryptionBackend protocol means AES-256-GCM is on the published roadmap and the envelope protocol supports running both backends simultaneously during migration. This isn't a locked-in choice — it's a starting point with a documented upgrade path.

**Climax:** Diane writes her assessment: "Approved with conditions. Current Fernet backend uses AES-128-CBC which meets our minimum bar but falls below our preferred AES-256 standard. The protocol-based architecture supports migration to AES-256-GCM without application changes — this is on the published roadmap. No custom cryptographic primitives — all operations delegate to the `cryptography` library. ADR trail demonstrates security-conscious design decisions. Condition: migrate to AES-256-GCM backend within 6 months of its release."

**Resolution:** The library enters the approved dependency list. Diane adds a calendar reminder to re-evaluate when the AES-256-GCM backend ships. She bookmarks the GitHub releases page. The conditional approval — rather than a flat rejection — was possible only because the architecture documentation made the upgrade path credible.

**Reveals requirements for:** SECURITY.md, MIT license, minimal dependency tree, published ADR trail, SonarQube-clean codebase, explicit wrong-key test coverage, no custom crypto primitives (delegate to `cryptography`), release cadence visibility, CI pipeline transparency, published roadmap with backend upgrade timeline.

**Phase:** MVP (evaluation works today with Phase 2: Ship deliverables)

### Journey 4: Tomás — Backend Plugin Author (Extension Path)

**Situation:** Tomás is a cloud infrastructure engineer at a company that mandates AWS KMS for all encryption operations. He needs ADK session encryption but can't use Fernet — his security team requires KMS-managed keys. He finds adk-secure-sessions and sees the `EncryptionBackend` protocol.

**Opening Scene:** Tomás reads the `protocols.py` source — a single `@runtime_checkable` Protocol with two methods: `async encrypt(data: bytes) -> bytes` and `async decrypt(data: bytes) -> bytes`, plus a `backend_id` property. He thinks: "I can implement that in 50 lines wrapping `boto3.kms`."

**Rising Action:** He creates `KMSBackend` implementing the protocol. He assigns it a unique `backend_id` integer following the registry documentation. He writes tests using the existing test patterns as a template. He runs `isinstance(KMSBackend(), EncryptionBackend)` — returns `True` at runtime. He passes his backend to `EncryptedSessionService` and it works. The envelope protocol tags all new ciphertext with his backend ID.

**Climax:** Tomás braces himself for the migration script — every encryption migration he's done before required a maintenance window and a prayer. Then he realizes there's no migration needed. The envelope header dispatches automatically. His team's existing Fernet-encrypted sessions continue to decrypt via backend ID `1`, while new sessions encrypt via KMS with his backend ID. No downtime. No migration script. No prayer.

**Resolution:** His company runs both backends in parallel during the transition. Old sessions decrypt via Fernet, new sessions encrypt via KMS. Eventually all sessions rotate to KMS naturally through TTL expiration. Tomás's PR starts a conversation about the Phase 4 enterprise backends roadmap.

**Reveals requirements for:** Clean protocol definition with minimal surface area, backend ID assignment registry/documentation, runtime checkability (`isinstance` works), example backend implementations in docs, contribution guide for new backends, envelope protocol's multi-backend dispatch explained.

**Phase:** Phase 3: Expand / Phase 4: Enterprise (protocol exists today, but backend authoring docs and KMS integration are future work)

### Journey 5: Kenji — DevOps/Platform Engineer (Operations & Recovery Path)

**Situation:** Kenji manages the infrastructure for Marcus's healthcare team. The ADK agents are deployed as containerized services. His responsibilities: key management, database operations, monitoring, and incident response for the encryption layer.

**Opening Scene:** Kenji receives the deployment spec: "EncryptedSessionService needs an encryption key and a database URL." He provisions a secret in the team's vault, configures it as an environment variable in the container spec, and points the database URL to the team's managed SQLite instance.

**Rising Action:** During a routine key rotation exercise, Kenji needs to rotate the encryption key. He reads the operations guide and learns that the envelope protocol supports key rotation by running both old and new keys simultaneously — decrypt with old, encrypt with new. He deploys the rotation with zero downtime. He also sets up monitoring for `DecryptionError` exceptions in the application logs as an early warning for key misconfiguration.

**Crisis:** Three months later, an alert fires: `DecryptionError` rate spikes to 100% on one container. Kenji investigates. A deployment rollback accidentally reverted the encryption key environment variable to an expired key. In past systems, this kind of error returned garbage data silently — corrupted records discovered days later during an audit. Here, the library raises `DecryptionError` immediately on every affected request. No silent corruption. No garbage data written back to the database.

**Recovery:** The error message includes the envelope header metadata — Kenji can see which backend ID produced the ciphertext and confirm the key mismatch is the root cause (not data corruption or a code bug). He fixes the environment variable, redeploys the container, and the error rate drops to zero within seconds. He writes a post-incident report: "Impact: 4 minutes of failed session reads on one container. Data loss: zero. Root cause: key misconfiguration during rollback. Detection: immediate via DecryptionError monitoring. Resolution: environment variable correction."

**Resolution:** Kenji documents the key rotation runbook and the monitoring setup for his team's operations wiki. He adds the `DecryptionError` monitoring pattern to the team's standard deployment checklist. He appreciates that the library fails loudly and explicitly — the worst thing an encryption library can do is fail silently.

**Reveals requirements for:** Environment variable-based key configuration, key rotation documentation, zero-downtime rotation support, explicit `DecryptionError` on wrong key (never silent corruption), envelope metadata in error context for operational debugging, operations/deployment guide, monitoring guidance for encryption errors, clear error messages that distinguish key mismatch from data corruption.

**Phase:** Key configuration and DecryptionError behavior are MVP; key rotation operations are Phase 3: Expand

### Journey Requirements Summary

| Capability Area | Revealed By | Priority | Phase |
|----------------|-------------|----------|-------|
| PyPI package with clear metadata and discoverability | Priya, Marcus | Critical | MVP |
| README with quick-start code example | Priya | Critical | MVP |
| MkDocs documentation site with architecture diagrams | Priya, Marcus, Diane | Critical | MVP |
| SECURITY.md with responsible disclosure policy | Diane | Critical | MVP |
| Published ADR trail as part of docs | Marcus, Diane | Critical | MVP |
| Encryption algorithm documentation | Priya, Marcus, Diane | Critical | MVP |
| Envelope protocol specification in docs | Marcus, Tomás, Kenji | Critical | MVP |
| Published roadmap with backend upgrade timeline | Diane | High | MVP |
| Operations/deployment guide | Kenji | High | Growth |
| Monitoring guidance for encryption errors | Kenji | High | Growth |
| Error message design (key mismatch vs. data corruption) | Kenji | High | MVP |
| Contribution guide for new backends | Tomás | Medium | Growth |
| Example backend implementations | Tomás | Medium | Growth |
| Backend ID assignment registry/documentation | Tomás | Medium | Growth |
| Key rotation documentation and support | Kenji, Marcus | Medium | Growth |
| Multi-backend dispatch documentation | Tomás, Kenji | Medium | Growth |
| Backend migration path documentation | Marcus, Tomás | Medium | Growth |

## Domain-Specific Requirements

The user journeys above reveal that compliance is a first-class adoption driver, not an afterthought. This section defines the regulatory, technical, and integration constraints that the functional requirements must satisfy.

### Compliance & Regulatory

**Encryption-at-rest standards:** The library must satisfy encryption-at-rest requirements referenced by major compliance frameworks. It does not seek certification itself — it enables organizations to check the encryption box in their own compliance audits.

| Framework | Relevant Requirement | How Library Addresses It |
|-----------|---------------------|-------------------------|
| **HIPAA** | Technical safeguard: encryption of ePHI at rest (§164.312(a)(2)(iv)) | Field-level encryption of all session state before SQLite/Postgres persistence |
| **SOC 2** | CC6.1: Encryption of data at rest | Configurable encryption backend with documented algorithm choices |
| **PCI-DSS** | Req 3.4: Render PAN unreadable anywhere it is stored | Session state containing cardholder data encrypted with approved algorithms |
| **GDPR** | Art. 32: Appropriate technical measures including encryption | Encryption at the serialization boundary; data residency is the deployer's responsibility. Note: Art. 32 references both encryption and pseudonymization as distinct technical measures — this library addresses encryption only, not pseudonymization. |

**Positioning language:** "Designed to support encryption-at-rest requirements for HIPAA, SOC 2, PCI-DSS, and GDPR regulated environments." Never claim certification — that belongs to the deploying organization.

**Algorithm documentation:** Every encryption backend must document: algorithm name, key size, mode of operation, key derivation function, and relevant NIST/FIPS references. This documentation is a compliance requirement, not optional.

**Fernet backend NIST references:**
- AES-128-CBC: NIST SP 800-38A (Recommendation for Block Cipher Modes of Operation)
- HMAC-SHA256: FIPS 198-1 (The Keyed-Hash Message Authentication Code)
- PBKDF2: NIST SP 800-132 (Recommendation for Password-Based Key Derivation)

### Technical Constraints

**No custom cryptographic primitives.** All encryption, decryption, key derivation, and HMAC operations must delegate to the `cryptography` library (pyca/cryptography). This is a permanent architectural constraint, not a Phase 1 shortcut. Custom crypto is a security anti-pattern — the `cryptography` library is audited, maintained by professional cryptographers, and trusted by the Python ecosystem. See ADR-003.

**Encryption keys must never be logged, serialized to persistence, or included in error context.** This is a first-class security constraint. No key material — raw keys, derived keys, or key identifiers that could enable key recovery — may appear in log output, exception messages, database records, or any observable channel. This applies to all phases, all backends, all error paths. Violation of this constraint is a security defect of the highest severity.

**Key management boundary.** The library accepts encryption keys — it does not store, rotate, or manage key lifecycle. Key provisioning, rotation scheduling, and secure storage are the deploying team's responsibility. The library's contract is: "give me a key, I'll encrypt with it." Phase 3 may provide key rotation *utilities* (decrypt-with-old, encrypt-with-new), but key *management* (where keys live, who has access, rotation policy) remains external. This boundary is deliberate — a library that manages keys becomes a key management system, which is a fundamentally different product with different threat models. Key compromise response (revocation, re-encryption of existing sessions) is the deployer's responsibility — the library provides the rotation utilities, the deployer provides the incident response process.

**Envelope protocol integrity.** The `[version_byte][backend_id_byte][ciphertext]` envelope is a wire protocol, not an implementation detail. It must never be stripped, shortcutted, or optional — even for "simple" cases. The envelope enables key rotation, backend migration, and operational debugging. See ADR-000.

**Async-first enforcement.** All public APIs must be `async def`. CPU-bound cryptographic operations (Fernet encrypt/decrypt, PBKDF2 key derivation) must be wrapped in `asyncio.to_thread()` to avoid blocking the event loop. This is a concurrency safety requirement, not a style preference. See ADR-002.

**Fail loud, never silent.** Wrong-key decryption must raise `DecryptionError`, never return garbage data. Malformed envelopes must raise `SerializationError`, never silently truncate. Truncated or corrupted ciphertext (from partial writes due to power loss, disk full, or killed processes) must be caught by envelope header validation before decryption is attempted, raising `SerializationError` with context about what was expected vs. received. Silent failures in encryption libraries lead to data corruption discovered days or weeks later — this is unacceptable in a compliance context.

**Audit & Observability.** MVP provides error-level observability: `DecryptionError` and `SerializationError` exceptions surface encryption failures for operator monitoring (Kenji's journey). Structured audit logging of encryption operations (who encrypted what, when, with which backend) is planned for Phase 4 (FR55). MVP audit capability is limited to exception monitoring and envelope metadata inspection — sufficient for initial compliance reviews but not for formal audit trail requirements.

### Integration Requirements

**ADK upstream compatibility.** The library extends `BaseSessionService` using only documented public methods (`create_session`, `get_session`, `list_sessions`, `delete_session`). It must not monkey-patch, override private methods, or redefine `Session` or `Event` types. Compatibility must be tested against the ADK version matrix (1.22.0 through latest) on every release. See ADR-004.

**Own schema, no coupling.** The library manages its own SQLite tables (`sessions`, `events`), independent of ADK's internal schema. All database access uses raw parameterized SQL via aiosqlite. This gives full control over encryption, indexing, and migration without coupling to ADK's internal database decisions. See ADR-004.

**Dependency minimalism.** Runtime dependencies must remain minimal: `google-adk`, `cryptography`, `aiosqlite`. Each additional dependency expands the attack surface and complicates security audits (Diane's journey). New persistence backends (Postgres) add their driver as an optional dependency, not a required one.

### Security & Technical Risks

This table covers security and technical risks. Market and resource risks are addressed in the Risk Mitigation Strategy subsection under Project Scoping & Phased Development below.

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Cryptographic vulnerability in `cryptography` library** | High | Pin minimum version, monitor CVEs, document patching SLA (48 hours for critical). Library delegates all crypto — no custom code to audit. |
| **Key leakage through error messages or logs** | Critical | Encryption keys must never be logged, serialized to persistence, or included in error context. Exception hierarchy (ADR-005) enforces this. Logging uses lazy %-formatting, never f-strings with sensitive data. |
| **Silent data corruption from encryption bugs** | Critical | Wrong-key always raises `DecryptionError`. Round-trip integrity tests on every CI run. Envelope header validation before decryption attempt. |
| **Truncated/corrupted data from partial writes** | High | Envelope header validation catches truncation before decryption is attempted, raising `SerializationError` with context about expected vs. received structure. No silent corruption from incomplete records. |
| **ADK breaking change in session interface** | Medium | CI matrix tests against 1.22.0 + latest. Envelope protocol and own schema insulate from internal ADK changes. Only documented public methods used. |
| **Supply chain attack via dependency** | Medium | Minimal dependency tree (≤5 runtime deps). Pin versions in CI. Monitor with GitHub Dependabot. |
| **FIPS 140-2 requirement from enterprise evaluators** | Low (Phase 4) | The `cryptography` library supports FIPS mode when linked against a FIPS-validated OpenSSL. Acknowledged on the roadmap as Phase 4 consideration. Evaluators see a planned path, not a gap. |

## Innovation & Novel Patterns

Three innovations differentiate adk-secure-sessions from the wrapper approach used by competitors. These drive the competitive moat and inform Phase 3-4 prioritization.

### Detected Innovation Areas

**1. Compliance Gateway Positioning (Market Innovation)**

The product category "encryption library" describes what the code does. "Compliance gateway" describes what the user achieves. This reframing is the primary innovation — it redefines the value conversation from "do you need encryption?" (technical) to "can you ship ADK agents in regulated markets?" (business). The buyer shifts from the individual developer to the compliance team evaluating ADK for production adoption. This market innovation creates the category; the technical innovations below make it defensible.

**2. Self-Describing Encryption Envelope Protocol (Technical Moat)**

The dominant pattern for session encryption in agent frameworks is the wrapper approach: encrypt the whole blob, store it, decrypt on read. OpenAI's `EncryptedSession` follows this pattern — Fernet encryption, HKDF key derivation, no metadata in the ciphertext.

adk-secure-sessions introduces a self-describing binary envelope: `[version_byte][backend_id_byte][ciphertext]`. This is a wire protocol, not just an encryption wrapper. Every piece of encrypted data carries metadata about how it was produced. This enables capabilities no simple wrapper can provide:

- **Zero-downtime backend migration**: Old data decrypts via backend ID 1 (Fernet), new data encrypts via backend ID 2 (AES-256-GCM). No migration script, no maintenance window.
- **Multi-backend coexistence**: Different sessions can use different backends simultaneously. The service dispatches based on the header, not configuration.
- **Operational debugging**: When a `DecryptionError` occurs, the envelope header tells operations *which backend* produced the ciphertext, narrowing root cause immediately.

This is a genuine architectural innovation — it trades 2 bytes of overhead per record for a fundamentally more capable encryption layer.

**3. Protocol-Based Plugin Boundary (Ecosystem Play)**

The innovation is not "we used PEP 544 Protocols" — Protocols are increasingly standard in modern Python. The innovation is applying `@runtime_checkable` Protocols to the *encryption backend contract*, which means third-party backends can live in separate packages with zero dependency on adk-secure-sessions itself. Structural typing at the plugin boundary means a KMS backend author implements two async methods and a property — no imports from our library, no inheritance chain, no coupling. This lowers the contribution barrier and enables an ecosystem of backends that the core library doesn't need to maintain, review, or release. The moat widens with every external backend.

### Market Context & Competitive Landscape

| Solution | Approach | Envelope Protocol | Multi-Backend | Self-Hosted | Time to Compliance Approval |
|----------|----------|-------------------|---------------|-------------|---------------------------|
| **adk-secure-sessions** | Field-level encryption at serialization boundary | Yes (self-describing) | Yes (protocol-based) | Yes (SQLite, Postgres) | Minutes (Priya: 12 min) to one meeting (Marcus) |
| **OpenAI EncryptedSession** | Wrapper over any session type | No | No | Yes (SQLite, SQLAlchemy) | N/A (wrong framework) |
| **Google ADK native** | No current solution; likely future: GCP-native, Cloud KMS-only | N/A | N/A | GCP-hosted only (probable) | Does not exist |
| **adk-ext (PyPI)** | General ADK extensions package | No | No | Unknown | No encryption feature today |
| **DIY (cryptography + ADK)** | Manual Fernet wrapping | No | No | Varies | Weeks (custom code + documentation + security review) |

### Validation Approach

- **Envelope protocol validation**: Phase 1 already tests round-trip encrypt/decrypt with envelope integrity. Phase 3 will validate multi-backend dispatch with real backend ID switching — the core technical moat claim.
- **Compliance gateway validation**: Track whether early adopters cite compliance as the adoption reason (GitHub issues, discussions, PyPI download context). If adoption is compliance-driven, the market positioning is validated.
- **Protocol extension validation**: The first external `EncryptionBackend` implementation (contributed or internal KMS backend) validates that the Protocol-based approach works for real third-party extensions.
- **Complete core at launch validation**: Track first impressions and evaluator feedback. OSS security libraries typically launch with partial implementations and iterate publicly. Launching with a complete, tested core (86 tests, 90/100 quality score) is an unusual credibility signal. If compliance evaluators cite the test suite and quality score in their approval justifications, this go-to-market strategy is validated.

### Innovation Risk Mitigation

| Innovation Risk | Mitigation |
|----------------|------------|
| Compliance gateway positioning doesn't resonate | Fall back to developer tool positioning. The technical product works regardless of how it's marketed. |
| Envelope overhead questioned by performance-sensitive users | 2 bytes per record is negligible. Benchmark and document overhead explicitly in Phase 3. |
| Protocol approach confuses developers expecting ABC | Document the pattern with examples. Include "Why Protocols, not ABC?" FAQ in docs. Clarify: the innovation is the application to the plugin boundary, not Protocols themselves. |
| Multi-backend dispatch adds complexity without demand | Envelope protocol costs nothing when using a single backend. Complexity only activates when a second backend is registered. |
| Google ships native encryption faster than expected | Our multi-cloud and self-hosted positioning serves the developers Google won't prioritize. First-mover community trust is durable even after a native solution exists. |

## Developer Tool Specific Requirements

This section defines the platform-specific requirements that shape how developers discover, install, and integrate the library.

### Project-Type Overview

adk-secure-sessions is a Python library distributed via PyPI, consumed by developers building Google ADK agents. The primary interface is a Python API (not CLI, not GUI). Developer experience is defined by: installation speed, API discoverability, documentation quality, and type system support.

### Language & Platform Matrix

| Dimension | MVP (Phase 2: Ship) | Growth (Phase 3+) |
|-----------|---------------------|-------------------|
| **Python** | 3.12 (`>=3.12,<3.13`) | 3.13+ when google-adk updates its matrix |
| **OS** | Linux, macOS, Windows (via `cryptography` + `aiosqlite` cross-platform support) | No change |
| **Architecture** | x86_64, ARM64 (via `cryptography` wheel availability) | No change |

Python 3.12 pin matches current test matrix. Broadening to 3.13+ is a Growth feature — do not block the PyPI launch for it.

### Installation Methods

```bash
# Standard install
pip install adk-secure-sessions

# With uv
uv add adk-secure-sessions

# With optional extras (Phase 3+)
pip install adk-secure-sessions[postgres]
```

**Extras strategy**: Define `[postgres]` and `[dev]` extras in `pyproject.toml` from v0.1.0, even if empty at launch. This establishes the package structure for clean Phase 3 expansion without retrofitting.

```toml
[project.optional-dependencies]
postgres = []  # Phase 3: asyncpg or psycopg
dev = ["pytest", "pytest-asyncio", "pytest-mock", "pytest-cov", "ruff"]
```

### API Surface

The public API is the 13 symbols exported from `src/adk_secure_sessions/__init__.py`:

**Core service:**
- `EncryptedSessionService` — drop-in `BaseSessionService` replacement

**Protocols:**
- `EncryptionBackend` — `@runtime_checkable` Protocol for backend contract

**Backends:**
- `FernetBackend` — Fernet symmetric encryption implementation

**Serialization:**
- `encrypt_session`, `decrypt_session` — session-level encrypt/decrypt
- `encrypt_json`, `decrypt_json` — JSON-level encrypt/decrypt

**Exceptions:**
- `SecureSessionError` — base exception
- `EncryptionError` — encryption failures
- `DecryptionError` — decryption failures (including wrong-key)
- `SerializationError` — envelope/serialization failures

**Constants/Types:**
- Remaining public symbols as defined in `__init__.py`

### Versioning & Stability Promise

Semantic versioning. Pre-1.0 minor versions may change internals, but the public API surface (13 symbols exported from `__init__.py`) is stable. Breaking changes to the public API require a minor version bump with migration notes. Internal modules (`serialization.py` internals, database schema details) are not covered by the stability promise.

### Documentation Architecture

| Artifact | Purpose | Phase |
|----------|---------|-------|
| **README.md** | Quick-start (30s to encrypted sessions), install command, one code example, compliance gateway tagline, badges (PyPI, Python, tests, coverage) | MVP |
| **MkDocs site** | Getting Started guide, API Reference (auto-generated via mkdocstrings), Architecture (ADRs), Envelope Protocol spec, FAQ | MVP |
| **py.typed** | PEP 561 marker file in package — enables IDE autocomplete and type checking for downstream users | MVP |
| **SECURITY.md** | Responsible disclosure policy, supported versions, vulnerability reporting process | MVP |
| **Changelog** | Auto-generated via release-please from conventional commits | MVP |
| **Docstring Examples** | `Examples:` sections with fenced code blocks in all public API docstrings — feeds IDE tooltips and API reference pages | MVP |
| **Contribution guide** | Backend authoring guide, "Why Protocols not ABC?" explainer | Growth |
| **Operations guide** | Key configuration, rotation runbook, monitoring setup | Growth |

### Code Examples Strategy

Minimum code examples for MVP launch:

1. **Quick-start** (README): 5-line swap from `BaseSessionService` to `EncryptedSessionService`
2. **Getting Started** (docs): Full working agent with encrypted sessions
3. **API Reference** (docstrings): `Examples:` section on every public function/class
4. **FAQ**: "What algorithms does Fernet use?", "Is this HIPAA compliant?", "Why Protocols not ABC?"

### Implementation Considerations

- **Package metadata**: PyPI classifiers must include `Framework :: Google ADK` (if available), `Topic :: Security :: Cryptography`, `Intended Audience :: Developers`, `License :: OSI Approved :: MIT License`
- **Wheel distribution**: Pure Python — no compiled extensions, universal wheel builds
- **CI publish pipeline**: GitHub Actions workflow triggered on release tags, publishes to TestPyPI then PyPI (#36)
- **Dependency pins**: Runtime dependencies use minimum version pins (`>=`). Dev dependencies use compatible release pins (`~=`).

## Project Scoping & Phased Development

This section provides the detailed execution plan. For a high-level phase overview, see the Product Scope section above.

### MVP Strategy & Philosophy

**MVP Approach:** Platform MVP — the code is done; the product isn't. Ship the existing tested core as a credible, findable, documented package. The MVP work is go-to-market: PyPI presence, documentation, and compliance positioning.

**Target:** PyPI v0.1.0 published within 4 weeks of PRD approval.

**Resource Reality:** Solo developer with a day job. Every feature competes for the same bandwidth:
- Ruthless prioritization — if it doesn't serve "findable, credible, and installable," it waits
- Automation over manual process — CI/CD publish pipeline pays for itself immediately
- Documentation is the product — for a library, docs are the UX
- No features that require ongoing maintenance burden at launch

### Phase 2: Ship (MVP) — Launch Execution Sequence

Dependency-ordered. Items must be completed in this sequence:

| # | Work Item | Depends On | Effort | Issue |
|---|-----------|------------|--------|-------|
| 1 | Trunk-based migration to main | — | 1-2 hours | #35 |
| 2 | PyPI/TestPyPI publish pipeline | #1 complete | 4-6 hours | #36 |
| 3 | SECURITY.md | — | 1 hour | — |
| 4 | README rewrite (compliance gateway positioning, quick-start, badges) | — | 2-3 hours | — |
| 5 | py.typed marker + pyproject.toml extras skeleton | — | 30 min | — |
| 6 | Clean test suite output (zero warnings, no confusing output on `uv run pytest`) | — | 1-2 hours | — |
| 7 | Docstring Examples sections on public API | — | 3-4 hours | — |
| 8 | MkDocs documentation site (API ref + ADRs + envelope spec + FAQ) | — | 6-8 hours | #11 |
| 9 | Community announcement (GitHub Discussion post) | #2 complete (package installable) | 30 min | — |

Items 3-7 are parallelizable. Item 8 can follow the initial publish as a fast-follow. Item 9 happens the day the package is installable.

**Absolute minimum launch (if bandwidth collapses):** Items 1, 2, 3, 4, 6. Package is installable, findable, and credible. MkDocs site and docstring examples follow within days.

**Core User Journeys Supported:**
- Priya (solo dev): Full happy path — search, install, swap, encrypt, done
- Marcus (enterprise dev): Full evaluation path — docs, source audit, test suite, security review
- Diane (compliance reviewer): Full evaluation path — SECURITY.md, ADRs, algorithm docs, license check

**Must-Have Capabilities:**

| Capability | Rationale | Issue |
|-----------|-----------|-------|
| Trunk-based migration to main | Blocks publish pipeline — must be first | #35 |
| PyPI/TestPyPI publish pipeline | Without this, the product doesn't exist publicly | #36 |
| README rewrite | First impression — compliance gateway positioning, quick-start, badges | — |
| MkDocs documentation site | Priya needs diagrams, Marcus needs ADRs, Diane needs algorithm docs | #11 |
| SECURITY.md | Diane's first check — missing = instant disqualification | — |
| py.typed marker | IDE autocomplete for downstream developers | — |
| Docstring Examples sections | Feeds API reference and IDE tooltips | — |
| Clean test suite output | Marcus runs `uv run pytest` — warnings or confusing output kills credibility | — |
| PyPI classifiers and metadata | Discoverability in PyPI search | — |
| Optional dependency extras skeleton | `[postgres]`, `[dev]` in pyproject.toml — empty but ready for Phase 3 | — |
| Community announcement | GitHub Discussion post — the launch *is* the product; first "how to encrypt ADK sessions" post defines SEO | — |

**Explicitly NOT in MVP** (see Scoping Decision Log below for rationale):
- AES-256-GCM encryption backend (Phase 3)
- PostgreSQL persistence backend (Phase 3)
- Key rotation utilities (Phase 3)
- Python 3.13+ support (Growth)
- Contribution guide / backend authoring docs (Growth)
- Operations/deployment guide (Growth)
- Blog posts or tutorials (post-launch)

### Phase 3: Expand — Post-MVP Growth

**Additional User Journeys Supported:**
- Tomás (backend plugin author): Partial — protocol exists, but needs backend authoring docs, registry, and examples
- Kenji (DevOps): Partial — key rotation utilities, operations guide, monitoring guidance

**Planned Capabilities:**

| Capability | Rationale | Issue |
|-----------|-----------|-------|
| AES-256-GCM encryption backend | Diane's conditional approval requires it; enterprise standard | #16 |
| Per-key random salt (PBKDF2) | Security hardening — current fixed salt is a known weakness | #17 |
| Key rotation utilities | Kenji's journey — decrypt-with-old, encrypt-with-new | #9 |
| PostgreSQL persistence backend | Enterprise teams need managed databases, not SQLite files | #9 |
| Performance benchmarks | Validate envelope overhead claim, establish baseline | #9 |
| SQLAlchemy ORM migration | Technical debt — cleaner persistence layer | #20 |
| Stale session detection | Optimistic concurrency for multi-instance deployments | #22 |
| Backend authoring documentation | Tomás's journey — contribution guide, examples, registry | — |
| Operations guide | Kenji's journey — key config, rotation runbook, monitoring | — |
| Test file refactoring | TEA findings — split oversized test files | #38, #39 |
| Python 3.13+ support | Track google-adk version matrix updates | — |
| Blog post / dev.to article | Proper tutorial with package URL, after package is live | — |

### Phase 4: Enterprise — Vision

**Additional User Journeys Supported:**
- Tomás (full): AWS KMS backend available as contributed or first-party package
- Kenji (full): Audit logging, compliance reporting, FIPS mode documentation

**Planned Capabilities:**

| Capability | Issue |
|-----------|-------|
| AWS KMS backend | #10 |
| GCP Cloud KMS backend | #10 |
| HashiCorp Vault integration | #10 |
| SQLCipher full-database encryption | #10 |
| Audit logging and compliance reporting | #10 |
| FIPS 140-2 documentation and guidance | — |
| Multiple backend migration guides | #10 |

### Scoping Decision Log

| Decision | Rationale |
|----------|-----------|
| Ship Phase 1 code as-is to PyPI | Core is tested and complete. Delaying for more features loses the competitive window. |
| Trunk migration before publish pipeline | Publish workflows need main branch. Getting this order wrong wastes a weekend. |
| Target 4-week launch | Creates accountability without hard commitment. Solo dev, day job — realistic for the scoped work. |
| README rewrite before PyPI publish | First impression. A library with a bad README doesn't get a second look. |
| SECURITY.md before PyPI publish | Compliance reviewers check this first. Missing = instant disqualification. |
| Clean test suite before publish | Marcus clones and runs pytest. Warnings or confusing output kills credibility. |
| Community announcement as MVP item | The first "how to encrypt ADK sessions" post defines SEO for years. Must ship same day as PyPI. |
| Defer blog posts to post-launch | Solo dev bandwidth. README + GitHub Discussion is the launch. Blog follows when there's a real URL to link to. |
| Defer AES-256-GCM to Phase 3 | Fernet meets minimum compliance bar. AES-256 is a conditional requirement, not a blocker. |
| Defer Postgres to Phase 3 | SQLite serves solo devs and small teams. Enterprise Postgres users can wait one phase. |
| Defer key rotation to Phase 3 | Key rotation requires multi-key support infrastructure. Ship single-key first, iterate. |
| Defer test refactoring to Phase 3 | TEA findings are real but don't block the release. Internal quality, not user-facing. |
| Empty extras in pyproject.toml now | 2-minute setup cost saves hours of retrofitting when Postgres lands. |

### Risk Mitigation Strategy

Security and technical risks (key leakage, data corruption, dependency vulnerabilities, FIPS requirements) are covered in the Security & Technical Risks subsection under Domain-Specific Requirements above.

**Technical Risks:**
- *Most technically challenging aspect:* The envelope protocol is already built and tested — the hard part is done. Phase 2 (Ship) is documentation and CI/CD, low technical risk.
- *Simplification opportunity:* MkDocs site can launch with auto-generated API reference + existing ADRs. Custom content (Getting Started guide, FAQ) can ship incrementally.
- *Riskiest assumption:* The google-adk API surface (`BaseSessionService`) won't change significantly. Mitigated by CI matrix testing against 1.22.0 + latest.

**Market Risks:**
- *Google ships native encrypted sessions:* Target PyPI publish within 4 weeks. Google-native solution would likely serve only GCP-hosted deployments, leaving self-hosted, AWS, and Azure developers underserved — our primary growth segment.
- *MVP validation:* The MVP validates one question: "Will ADK developers find and install this?" If downloads are near zero after 3 months, pivot positioning.
- *De-risking:* GitHub Discussion announcement same day as PyPI publish. First post defining "how to encrypt ADK sessions" establishes SEO.
- *Abandoned project perception:* Minimum quarterly release cadence. Public roadmap. Responsive to issues within 1 week.

**Resource Risks:**
- *Solo developer reality:* One person, day job. If bandwidth drops, prioritize execution sequence items 1-4 and 6. That's the absolute minimum launch — a weekend of focused work.
- *Absolute minimum launch:* PyPI package + README + SECURITY.md + clean test output. MkDocs site follows in a fast-follow release.
- *Contingency:* If Phase 3 stalls, the Phase 2 MVP is still a complete, useful product. Fernet+SQLite serves the majority of ADK developers. Growth features are additive, not corrective.

## Functional Requirements

55 capabilities across 9 areas. Each FR specifies what the system must do, phase-tagged `[MVP]`, `[Phase 3]`, or `[Phase 4]`. These are the capability contract — downstream architecture, epics, and stories trace back to these.

### Session Encryption

- **FR1** `[MVP]`: Developer can encrypt all session state fields at rest before database persistence using a configured encryption backend
- **FR2** `[MVP]`: Developer can decrypt previously encrypted session state on retrieval, restoring the original data structure
- **FR3** `[MVP]`: Developer can encrypt and decrypt arbitrary JSON-serializable data independently of session lifecycle
- **FR4** `[MVP]`: System wraps all encrypted data in a self-describing binary envelope containing version and backend identifier metadata
- **FR5** `[MVP]`: Developer can use Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) as the default encryption backend

### Session Persistence

- **FR6** `[MVP]`: Developer can create encrypted sessions with an app name, user ID, and optional initial state
- **FR7** `[MVP]`: Developer can retrieve a previously created session by its ID, receiving decrypted state
- **FR8** `[MVP]`: Developer can list all sessions for a given app name and user ID combination
- **FR9** `[MVP]`: Developer can delete a session by its ID, removing all persisted data
- **FR10** `[MVP]`: Developer can append events to an existing session
- **FR11** `[MVP]`: System persists encrypted session data to SQLite via async database operations
- **FR12** `[MVP]`: System creates and migrates its own database tables without depending on or modifying ADK's internal schema

### Configuration & Initialization

- **FR13** `[MVP]`: Developer can configure the session service with an encryption key and database URL
- **FR14** `[MVP]`: System initializes the database schema on first service instantiation
- **FR15** `[MVP]`: System validates configuration at startup and raises `ConfigurationError` for invalid key format (specifying expected format) or `DatabaseConnectionError` for unreachable database (including file path and OS error)
- **FR16** `[MVP]`: Developer can gracefully close database connections via the service's close method

### Backend Extensibility

- **FR17** `[MVP]`: Developer can implement a custom encryption backend by conforming to the EncryptionBackend protocol (two async methods + backend ID property)
- **FR18** `[MVP]`: System validates backend conformance at runtime via isinstance checks against the protocol
- **FR19** `[MVP]`: Developer can register a custom backend with the session service without modifying library internals
- **FR20** `[MVP]`: System identifies and dispatches decryption to the correct backend based on the envelope header's backend ID
- **FR21** `[Phase 3]`: System supports multiple encryption backends simultaneously, with different sessions using different backends

### Error Handling & Safety

- **FR22** `[MVP]`: System raises DecryptionError when decryption fails due to wrong key, never returning garbage data
- **FR23** `[MVP]`: System raises SerializationError when envelope structure is malformed or truncated
- **FR24** `[MVP]`: System raises EncryptionError when encryption operations fail
- **FR25** `[MVP]`: System never includes encryption keys, ciphertext, or plaintext in error messages or log output — verifiable by inspection of all exception classes and log statements
- **FR26** `[MVP]`: System provides envelope header metadata in error context to support operational debugging

### Developer Integration

- **FR27** `[MVP]`: Developer can install the library via `pip install adk-secure-sessions` from PyPI
- **FR28** `[MVP]`: Developer can instantiate EncryptedSessionService as a drop-in implementation of BaseSessionService
- **FR29** `[MVP]`: EncryptedSessionService exposes the same public method signatures as BaseSessionService
- **FR30** `[MVP]`: Developer can use the library with full IDE autocomplete and type checking support (py.typed, type hints on all public APIs)
- **FR31** `[MVP]`: System maintains compatibility with google-adk versions 1.22.0 through latest
- **FR32** `[MVP]`: Developer can run the test suite and receive passing results with zero warnings

### Documentation & Discoverability

- **FR33** `[MVP]`: Developer can find the library on the first page of PyPI search results for the terms "adk encryption", "adk encrypted sessions", and "google adk security" — achieved through PyPI classifiers, keywords in pyproject.toml, and package description
- **FR34** `[MVP]`: Developer can read a quick-start code example in the README that demonstrates the integration swap
- **FR35** `[MVP]`: Developer can access auto-generated API reference documentation for all public symbols
- **FR36** `[MVP]`: Developer can read architecture decision records explaining design choices
- **FR37** `[MVP]`: Developer can read the envelope protocol specification
- **FR38** `[MVP]`: Developer can read encryption algorithm documentation with NIST/FIPS references
- **FR39** `[MVP]`: Compliance reviewer can read a SECURITY.md with responsible disclosure policy and supported versions
- **FR40** `[MVP]`: Compliance reviewer can verify the library's license, dependency tree, and test coverage
- **FR41** `[MVP]`: Developer can read docstring examples with fenced code blocks for all public API functions and classes
- **FR56** `[MVP]`: Developer can read a published roadmap on the documentation site with phase timeline, planned capabilities per phase, and backend upgrade schedule

### Release & Distribution

- **FR42** `[MVP]`: Maintainer can publish new releases to PyPI via an automated CI/CD pipeline triggered by release tags
- **FR43** `[MVP]`: Maintainer can publish pre-release versions to TestPyPI for validation before production release
- **FR44** `[MVP]`: System generates changelogs automatically from conventional commit messages
- **FR45** `[MVP]`: Developer can install optional dependency extras for future persistence backends (`[postgres]`)

### Future Capabilities

- **FR46** `[Phase 3]`: Developer can use AES-256-GCM as an alternative encryption backend
- **FR47** `[Phase 3]`: Developer can derive encryption keys with per-key random salt instead of fixed salt
- **FR48** `[Phase 3]`: Operator can rotate encryption keys with zero downtime (decrypt-with-old, encrypt-with-new)
- **FR49** `[Phase 3]`: Developer can persist encrypted sessions to PostgreSQL as an alternative to SQLite
- **FR50** `[Phase 3]`: Developer can read backend authoring documentation with examples to create custom backends
- **FR51** `[Phase 3]`: Operator can read an operations guide covering key configuration, rotation, and monitoring
- **FR52** `[Phase 4]`: Developer can use AWS KMS as an encryption backend
- **FR53** `[Phase 4]`: Developer can use GCP Cloud KMS as an encryption backend
- **FR54** `[Phase 4]`: Developer can use HashiCorp Vault as an encryption backend
- **FR55** `[Phase 4]`: Operator can access audit logs of encryption operations for compliance reporting

## Non-Functional Requirements

28 quality attributes across 6 categories. NFRs define how well the system performs, not what it does. Each is measurable and phase-tagged.

### Performance

- **NFR1** `[MVP]`: Encryption/decryption overhead is less than 20% of the total session operation time for typical session sizes (state dict ≤ 10KB serialized), verified by a benchmark test under single-threaded sequential operation on localhost comparing encrypted vs. unencrypted round-trip
- **NFR2** `[MVP]`: All cryptography library operations execute via `asyncio.to_thread()` — zero direct blocking of the event loop
- **NFR3** `[MVP]`: Database operations use async I/O exclusively (aiosqlite) — no synchronous SQLite calls in any code path
- **NFR4** `[Phase 3]`: Published benchmarks document actual overhead per operation (encrypt, decrypt, round-trip) across representative payload sizes (1KB, 10KB, 100KB, 1MB)

### Security

- **NFR5** `[MVP]`: All session state and event data is encrypted at rest before touching the database — no plaintext data paths exist
- **NFR6** `[MVP]`: Encryption keys never appear in log output, error messages, exception tracebacks, or serialized error context
- **NFR7** `[MVP]`: Wrong-key decryption always raises `DecryptionError` — never returns corrupted or partial plaintext
- **NFR8** `[MVP]`: The library has zero known unpatched CVEs in its direct dependency tree at time of each release (verified via `pip-audit` or equivalent)
- **NFR9** `[MVP]`: All cryptographic operations use well-established, peer-reviewed algorithms (Fernet: AES-128-CBC + HMAC-SHA256, per NIST SP 800-38A and FIPS 198-1)
- **NFR10** `[MVP]`: The library never persists, caches, or logs encryption keys; key lifecycle management (generation, storage, rotation scheduling) is the operator's responsibility
- **NFR11** `[Phase 3]`: Each key derivation uses a unique cryptographically random salt of ≥16 bytes — verified by test asserting no two derived keys share the same salt across 100 derivations
- **NFR12** `[Phase 4]`: Documentation includes a FIPS 140-2 deployment guide covering: OpenSSL FIPS module configuration, backend selection for FIPS mode, and verification steps to confirm FIPS-validated operation

### Reliability

- **NFR13** `[MVP]`: Corrupted or truncated ciphertext raises `SerializationError` or `DecryptionError` — never silent data loss
- **NFR14** `[MVP]`: Database connection failures raise exceptions that include the database file path, OS error code, and suggested remediation — not generic errors
- **NFR15** `[MVP]`: The library handles empty session state (`{}`) and empty event lists (`[]`) without error — round-trip preservation verified
- **NFR16** `[MVP]`: Test suite passes with zero warnings on `uv run pytest`
- **NFR17** `[MVP]`: No flaky tests across 5 consecutive CI runs on the same commit
- **NFR18** `[MVP]`: Code coverage ≥90% line coverage, enforced by CI gate
- **NFR19** `[MVP]`: All async fixtures properly close database connections on teardown — zero leaked connections after test runs

### Integration

- **NFR20** `[MVP]`: An ADK Runner can accept `EncryptedSessionService` where it expects `BaseSessionService` and execute a complete agent turn — verified by integration test, not just `isinstance` check
- **NFR21** `[MVP]`: Library operates as a pure Python package with no compiled extensions — installs on any platform where `cryptography` and `aiosqlite` wheels are available
- **NFR22** `[MVP]`: Downstream developers get full IDE support: `py.typed` marker, type hints on all public APIs, no `Any` escape hatches in public signatures
- **NFR23** `[MVP]`: The library has ≤5 direct runtime dependencies — dependency footprint ceiling to limit attack surface and version conflict risk
- **NFR24** `[Phase 3]`: Library tracks google-adk's Python version matrix — when ADK supports 3.13+, the library follows within one minor release

### Scalability

- **NFR25** `[MVP]`: Concurrent async session operations on the same database do not corrupt data — verified by test with 50 coroutines performing simultaneous writes to different sessions, all data recoverable with correct values after completion
- **NFR26** `[Phase 3]`: PostgreSQL backend supports ≥10 concurrent writer instances without data loss — verified by integration test with parallel session writes from separate connections, all sessions recoverable with correct state
- **NFR27** `[Phase 3]`: Stale session updates are detected and rejected — when two instances read the same session and both write back, the second write raises a concurrency conflict error rather than silently overwriting the first

### Developer Experience

- **NFR28** `[MVP]`: A developer with an existing ADK agent can add encrypted sessions in under 5 minutes — measured from `pip install` to first encrypted session persisted, using only README and docstring examples

---

## Closing Statement

The measure of success for adk-secure-sessions is simple: a developer with an existing ADK agent adds encrypted sessions in under 5 minutes, and their compliance reviewer approves without follow-up questions. Everything in this document — 55 functional requirements, 28 non-functional requirements, 5 user journeys, and a 4-phase roadmap — serves that outcome. The core encryption engine is built and tested. The competitive window is open. The next step is shipping.
