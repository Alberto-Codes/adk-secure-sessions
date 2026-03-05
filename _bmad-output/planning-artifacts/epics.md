---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-02-design-epics-v2', 'step-03-create-stories-v2', 'step-04-final-validation-v2']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# adk-secure-sessions - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for adk-secure-sessions, decomposing the requirements from the PRD and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1 [MVP]: Developer can encrypt all session state fields at rest before database persistence using a configured encryption backend
FR2 [MVP]: Developer can decrypt previously encrypted session state on retrieval, restoring the original data structure
FR3 [MVP]: Developer can encrypt and decrypt arbitrary JSON-serializable data independently of session lifecycle
FR4 [MVP]: System wraps all encrypted data in a self-describing binary envelope containing version and backend identifier metadata
FR5 [MVP]: Developer can use Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) as the default encryption backend
FR6 [MVP]: Developer can create encrypted sessions with an app name, user ID, and optional initial state
FR7 [MVP]: Developer can retrieve a previously created session by its ID, receiving decrypted state
FR8 [MVP]: Developer can list all sessions for a given app name and user ID combination
FR9 [MVP]: Developer can delete a session by its ID, removing all persisted data
FR10 [MVP]: Developer can append events to an existing session
FR11 [MVP]: System persists encrypted session data to SQLite via async database operations
FR12 [MVP]: System creates and migrates its own database tables without depending on or modifying ADK's internal schema
FR13 [MVP]: Developer can configure the session service with an encryption key and database URL
FR14 [MVP]: System initializes the database schema on first service instantiation
FR15 [MVP]: System validates configuration at startup and raises ConfigurationError for invalid key format or DatabaseConnectionError for unreachable database
FR16 [MVP]: Developer can gracefully close database connections via the service's close method
FR17 [MVP]: Developer can implement a custom encryption backend by conforming to the EncryptionBackend protocol (two async methods + backend ID property)
FR18 [MVP]: System validates backend conformance at runtime via isinstance checks against the protocol
FR19 [MVP]: Developer can register a custom backend with the session service without modifying library internals
FR20 [MVP]: System identifies and dispatches decryption to the correct backend based on the envelope header's backend ID
FR21 [Phase 3]: System supports multiple encryption backends simultaneously, with different sessions using different backends
FR22 [MVP]: System raises DecryptionError when decryption fails due to wrong key, never returning garbage data
FR23 [MVP]: System raises SerializationError when envelope structure is malformed or truncated
FR24 [MVP]: System raises EncryptionError when encryption operations fail
FR25 [MVP]: System never includes encryption keys, ciphertext, or plaintext in error messages or log output
FR26 [MVP]: System provides envelope header metadata in error context to support operational debugging
FR27 [MVP]: Developer can install the library via pip install adk-secure-sessions from PyPI
FR28 [MVP]: Developer can instantiate EncryptedSessionService as a drop-in implementation of BaseSessionService
FR29 [MVP]: EncryptedSessionService exposes the same public method signatures as BaseSessionService
FR30 [MVP]: Developer can use the library with full IDE autocomplete and type checking support (py.typed, type hints on all public APIs)
FR31 [MVP]: System maintains compatibility with google-adk versions 1.22.0 through latest
FR32 [MVP]: Developer can run the test suite and receive passing results with zero warnings
FR33 [MVP]: Developer can discover the library through PyPI search — package metadata includes relevant classifiers, keywords, and description optimized for discoverability
FR34 [MVP]: Developer can read a quick-start code example in the README that demonstrates the integration swap
FR35 [MVP]: Developer can access auto-generated API reference documentation for all public symbols
FR36 [MVP]: Developer can read architecture decision records explaining design choices
FR37 [MVP]: Developer can read the envelope protocol specification
FR38 [MVP]: Developer can read encryption algorithm documentation with NIST/FIPS references
FR39 [MVP]: Compliance reviewer can read a SECURITY.md with responsible disclosure policy and supported versions
FR40 [MVP]: Compliance reviewer can verify the library's license, dependency tree, and test coverage
FR41 [MVP]: Developer can read docstring examples with fenced code blocks for all public API functions and classes
FR42 [MVP]: Maintainer can publish new releases to PyPI via an automated CI/CD pipeline triggered by release tags
FR43 [MVP]: Maintainer can publish pre-release versions to TestPyPI for validation before production release
FR44 [MVP]: System generates changelogs automatically from conventional commit messages
FR45 [MVP]: Developer can install optional dependency extras for future persistence backends ([postgres])
FR46 [Phase 3]: Developer can use AES-256-GCM as an alternative encryption backend
FR47 [Phase 3]: Developer can derive encryption keys with per-key random salt instead of fixed salt
FR48 [Phase 3]: Operator can rotate encryption keys with zero downtime (decrypt-with-old, encrypt-with-new)
FR49 [Phase 3]: Developer can persist encrypted sessions to PostgreSQL as an alternative to SQLite
FR50 [Phase 3]: Developer can read backend authoring documentation with examples to create custom backends
FR51 [Phase 3]: Operator can read an operations guide covering key configuration, rotation, and monitoring
FR52 [Phase 4]: Developer can use AWS KMS as an encryption backend
FR53 [Phase 4]: Developer can use GCP Cloud KMS as an encryption backend
FR54 [Phase 4]: Developer can use HashiCorp Vault as an encryption backend
FR55 [Phase 4]: Operator can access audit logs of encryption operations for compliance reporting
FR56 [MVP]: Developer can read a published roadmap on the documentation site with phase timeline, planned capabilities per phase, and backend upgrade schedule
FR-NEW-1 [Now]: All user-facing descriptions accurately characterize the library as an "encrypted session persistence service implementing BaseSessionService," not a "drop-in replacement for DatabaseSessionService" or "encryption layer"
FR-NEW-2 [Now]: All schema references list all 4 tables (sessions, events, app_states, user_states) and describe the schema relationship as "mirroring ADK V1 structure with encrypted column types"
FR-NEW-3 [Now]: Planning artifacts that contain superseded architectural claims carry revision markers without rewriting history
FR-NEW-4 [Phase 3]: EncryptedSessionService wraps DatabaseSessionService via SQLAlchemy TypeDecorator for transparent encrypt/decrypt at the ORM boundary
FR-NEW-5 [Phase 3]: Multi-database support (SQLite, PostgreSQL, MySQL, MariaDB) via DatabaseSessionService's existing dialect handling
FR-NEW-6 [Phase 3]: New ADR documents the architecture migration decision, references ADR-000 V1 changes, and explains why wrapping is now viable

### NonFunctional Requirements

NFR1 [MVP]: Encryption/decryption overhead is less than 20% of the total session operation time for typical session sizes (state dict <= 10KB serialized), verified by a benchmark test under single-threaded sequential operation on localhost
NFR2 [MVP]: All cryptography library operations execute via asyncio.to_thread() — zero direct blocking of the event loop
NFR3 [MVP]: Database operations use async I/O exclusively (aiosqlite) — no synchronous SQLite calls in any code path
NFR4 [Phase 3]: Published benchmarks document actual overhead per operation (encrypt, decrypt, round-trip) across representative payload sizes
NFR5 [MVP]: All session state and event data is encrypted at rest before touching the database — no plaintext data paths exist
NFR6 [MVP]: Encryption keys never appear in log output, error messages, exception tracebacks, or serialized error context
NFR7 [MVP]: Wrong-key decryption always raises DecryptionError — never returns corrupted or partial plaintext
NFR8 [MVP]: The library has zero known unpatched CVEs in its direct dependency tree at time of each release (verified via pip-audit)
NFR9 [MVP]: All cryptographic operations use well-established, peer-reviewed algorithms (Fernet: AES-128-CBC + HMAC-SHA256)
NFR10 [MVP]: The library never persists, caches, or logs encryption keys; key lifecycle management is the operator's responsibility
NFR11 [Phase 3]: Each key derivation uses a unique cryptographically random salt of >= 16 bytes
NFR12 [Phase 4]: Documentation includes a FIPS 140-2 deployment guide
NFR13 [MVP]: Corrupted or truncated ciphertext raises SerializationError or DecryptionError — never silent data loss
NFR14 [MVP]: Database connection failures raise exceptions that include the database file path, OS error code, and suggested remediation
NFR15 [MVP]: The library handles empty session state ({}) and empty event lists ([]) without error — round-trip preservation verified
NFR16 [MVP]: Test suite passes with zero warnings on uv run pytest
NFR17 [MVP]: No flaky tests across 5 consecutive CI runs on the same commit
NFR18 [MVP]: Code coverage >= 90% line coverage, enforced by CI gate
NFR19 [MVP]: All async fixtures properly close database connections on teardown — zero leaked connections after test runs
NFR20 [MVP]: An ADK Runner can accept EncryptedSessionService where it expects BaseSessionService and execute a complete agent turn
NFR21 [MVP]: Library operates as a pure Python package with no compiled extensions
NFR22 [MVP]: Downstream developers get full IDE support: py.typed marker, type hints on all public APIs, no Any escape hatches
NFR23 [MVP]: The library has <= 5 direct runtime dependencies
NFR24 [Phase 3]: Library tracks google-adk's Python version matrix — when ADK supports 3.13+, the library follows within one minor release
NFR25 [MVP]: Concurrent async session operations on the same database do not corrupt data — verified by test with 50 coroutines
NFR26 [Phase 3]: PostgreSQL backend supports >= 10 concurrent writer instances without data loss
NFR27 [Phase 3]: Stale session updates are detected and rejected via optimistic concurrency
NFR28 [MVP]: A developer with an existing ADK agent can add encrypted sessions in under 5 minutes

### Additional Requirements

**From Architecture — Decide Now (affects v0.1.0):**

- Schema Reservation: Reserve `version INTEGER DEFAULT 1` on `sessions`, `app_states`, and `user_states` tables in v0.1.0 schema. Events table excluded (append-only). Column inert in Phase 2, activated in Phase 3. (Architecture Decision 1)
- Exception Hierarchy Evolution: Add `ConfigurationError` as a `SecureSessionError` subclass before v0.1.0 for startup validation — bad key format, empty key, invalid backend_id, missing backend. Defer `DatabaseConnectionError` to Phase 3. (Architecture Decision 2)
- ADR-006 must be created when ConfigurationError is implemented
- Constructor validation in `EncryptedSessionService` raising `ConfigurationError` for bad config

**From Architecture — Phase 2 Structural Action Items:**

- Create `tests/conftest.py`, `tests/unit/conftest.py`, `tests/integration/conftest.py` (shared fixtures)
- Register `benchmark` and `integration` pytest markers in `pyproject.toml`
- Add `py.typed` marker to `src/adk_secure_sessions/`
- Create `SECURITY.md` with responsible disclosure policy
- Add `pip-audit` check to publish workflow
- Add `interrogate` to CI for docstring coverage alignment
- Publish pipeline must run its own test suite independently (security library requirement)
- FR20 (SQLAlchemy ORM migration) superseded by persistence protocol approach (Architecture Deferred Decision 3)

**From Architecture — Phase 2 Technology Additions:**

- No new runtime dependencies in Phase 2
- PyPI publish workflow triggered on release tags
- TestPyPI pre-release validation step
- NFR1 benchmark test using `time.perf_counter()` (no new dependency; pytest-benchmark deferred to Phase 3)

**From Architecture — Extras Group Strategy:**

- Define `[postgres]` and `[dev]` extras in pyproject.toml from v0.1.0, even if empty
- No `[all]` extras group (deliberate security decision — minimize installed surface)

**From Architecture — Deferred Design Direction (Phase 3+):**

- Service decomposition: persistence layer + encryption coordinator + service orchestrator
- Key rotation design surface: key provider abstraction, migration strategy, backend registry
- API surface growth strategy: flat namespace vs. submodule imports
- Backend ecosystem architecture: backend ID registry, entry-point discovery, packaging strategy
- PostgreSQL driver decision deferred (asyncpg vs. psycopg3)

### FR Coverage Map

**Phase 1 Complete (no new stories needed):**

FR1: Phase 1 Complete — Encrypt session state at rest
FR2: Phase 1 Complete — Decrypt session state on retrieval
FR3: Phase 1 Complete — Encrypt/decrypt arbitrary JSON data
FR4: Phase 1 Complete — Self-describing binary envelope
FR5: Phase 1 Complete — Fernet backend (AES-128-CBC + HMAC-SHA256)
FR6: Phase 1 Complete — Create encrypted sessions
FR7: Phase 1 Complete — Retrieve session by ID
FR8: Phase 1 Complete — List sessions by app + user
FR9: Phase 1 Complete — Delete session by ID
FR10: Phase 1 Complete — Append events to session
FR11: Phase 1 Complete — SQLite persistence via async ops
FR12: Phase 1 Complete — Own database schema
FR13: Phase 1 Complete — Configure with key + database URL
FR14: Phase 1 Complete — Auto-initialize schema
FR16: Phase 1 Complete — Graceful connection close
FR17: Phase 1 Complete — Custom backend via protocol
FR18: Phase 1 Complete — Runtime conformance validation
FR19: Phase 1 Complete — Register custom backend
FR20: Phase 1 Complete — Dispatch by envelope backend ID
FR22: Phase 1 Complete — DecryptionError on wrong key
FR23: Phase 1 Complete — SerializationError on malformed envelope
FR24: Phase 1 Complete — EncryptionError on encrypt failure
FR25: Phase 1 Complete — No keys in error messages
FR26: Phase 1 Complete — Envelope metadata in error context
FR28: Phase 1 Complete — Drop-in BaseSessionService impl
FR29: Phase 1 Complete — Same public method signatures
FR31: Phase 1 Complete — ADK 1.22.0–latest compatibility

**Epic 1: Ship to PyPI**

FR15: Epic 1 — ConfigurationError for startup validation
FR27: Epic 1 — pip install from PyPI
FR30: Epic 1 — py.typed + IDE autocomplete support
FR32: Epic 1 — Zero-warning test suite
FR33: Epic 1 — PyPI discoverability metadata
FR34: Epic 1 — README quick-start example
FR39: Epic 1 — SECURITY.md with responsible disclosure
FR40: Epic 1 — License, deps, coverage verifiable (badges)
FR42: Epic 1 — CI/CD publish to PyPI
FR43: Epic 1 — TestPyPI pre-release
FR44: Epic 1 — Auto-generated changelog
FR45: Epic 1 — Optional dependency extras skeleton

**Epic 2: Documentation & Compliance Credibility**

FR35: Epic 2 — Auto-generated API reference
FR36: Epic 2 — Published ADRs
FR37: Epic 2 — Envelope protocol specification
FR38: Epic 2 — Algorithm docs with NIST/FIPS refs
FR41: Epic 2 — Docstring examples on all public APIs
FR56: Epic 2 — Published roadmap on docs site

**Epic 3: AES-256-GCM Backend & Security Hardening (Phase 3)**

FR21: Epic 3 — Multiple simultaneous backends
FR46: Epic 3 — AES-256-GCM encryption backend
FR47: Epic 3 — Per-key random salt

**Epic 4: PostgreSQL Persistence & Key Rotation (Phase 3)**

FR48: Epic 4 — Zero-downtime key rotation
FR49: Epic 4 — PostgreSQL persistence backend
FR50: Epic 4 — Backend authoring documentation
FR51: Epic 4 — Operations guide

**Epic 5: Enterprise KMS Backends & Audit (Phase 4)**

FR52: Epic 5 — AWS KMS backend
FR53: Epic 5 — GCP Cloud KMS backend
FR54: Epic 5 — HashiCorp Vault backend
FR55: Epic 5 — Audit logging

**Epic 6: Documentation Honesty (Now)**

FR-NEW-1: Epic 6 — Accurate library characterization across all user-facing docs
FR-NEW-2: Epic 6 — Correct schema descriptions (4 tables, mirrored structure)
FR-NEW-3: Epic 6 — Superseded markers on stale planning artifacts
FR12: Epic 6 — Language correction (schema claim); Epic 7 — Implementation change
FR28: Epic 6 — Language correction (drop-in claim)

**Epic 7: Architecture Migration — DatabaseSessionService Wrapper (Phase 3, spike-gated)**

FR-NEW-4: Epic 7 — DatabaseSessionService wrapper via TypeDecorator
FR-NEW-5: Epic 7 — Multi-database support via DatabaseSessionService
FR-NEW-6: Epic 7 — New ADR documenting migration decision
FR11: Epic 7 — Reworded: "System persists encrypted session data via async database operations" (drop SQLite-specific)
FR12: Epic 7 — Superseded: wrapping replaces own schema
FR49: Epic 7 — PostgreSQL comes for free (remapped from Epic 4)

## Epic List

### Epic 1: Ship to PyPI

A developer discovers adk-secure-sessions on PyPI, installs in one command, gets IDE autocomplete, and finds the library credible (SECURITY.md, clean README, zero-warning tests). The maintainer publishes releases reliably via CI/CD. Configuration errors are caught at startup, not runtime.

**FRs covered:** FR15, FR27, FR30, FR32, FR33, FR34, FR39, FR40, FR42, FR43, FR44, FR45
**Architecture items:** Schema reservation (Decision 1), ConfigurationError (Decision 2), ADR-006, conftest files, pytest markers, trunk migration, pip-audit, interrogate in CI, publish pipeline independence
**NFRs served:** NFR1, NFR8, NFR16, NFR17, NFR18, NFR19, NFR20, NFR21, NFR22, NFR23, NFR25, NFR28

### Epic 2: Documentation & Compliance Credibility

Marcus (enterprise dev) evaluates via full documentation site. Diane (compliance reviewer) approves from ADR trail, algorithm docs with NIST references, and envelope protocol spec. Developers get IDE tooltips from docstring examples.

**FRs covered:** FR35, FR36, FR37, FR38, FR41, FR56
**NFRs served:** NFR28

### Epic 3: AES-256-GCM Backend & Security Hardening (Phase 3)

Enterprise security teams approve unconditionally with AES-256-GCM. Per-key random salt hardens key derivation. Multiple backends coexist via envelope protocol for seamless migration.

**FRs covered:** FR21, FR46, FR47
**NFRs served:** NFR4, NFR11

### Epic 4: PostgreSQL Persistence & Key Rotation (Phase 3)

Teams run encrypted sessions on managed PostgreSQL. Operators rotate keys with zero downtime. Backend authors and operators get dedicated documentation.

**FRs covered:** FR48, ~~FR49~~ _(remapped to Epic 7)_, FR50, FR51
**NFRs served:** NFR24, NFR26, NFR27
**Note:** Stories 4.1 (Persistence Protocol), 4.2 (Encryption Coordinator), 4.3 (PostgreSQL Backend) are **[SUPERSEDED by Epic 7]**. Remaining stories: 4.4 (Key Rotation), 4.5 (Backend Docs), 4.6 (Ops Guide), 4.7 (Python Version Tracking).

### Epic 5: Enterprise KMS Backends & Audit (Phase 4)

Enterprise teams use managed KMS providers (AWS, GCP, Vault) with organization-mandated key management, and produce audit trails of encryption operations for compliance reporting.

**FRs covered:** FR52, FR53, FR54, FR55
**NFRs served:** NFR12

### Epic 6: Documentation Honesty (Now)

A developer reading the README, docs site, or PyPI description gets an accurate understanding of what adk-secure-sessions is: an encrypted session persistence service implementing BaseSessionService — not a "drop-in replacement for DatabaseSessionService" or an "encryption layer." A contributor reading CLAUDE.md, conventions, or planning artifacts encounters no false claims about schema independence or table counts. Superseded planning artifacts carry revision markers preserving history.

**FRs covered:** FR-NEW-1, FR-NEW-2, FR-NEW-3
**Existing FRs corrected:** FR12 (schema language), FR28 (drop-in language)
**NFRs served:** NFR28
**Scope:** 15 audit findings (8 HIGH, 7 MEDIUM) across ~12 files. Zero code changes.
**Dependencies:** None — standalone.

### Epic 7: Architecture Migration — DatabaseSessionService Wrapper (Phase 3, spike-gated)

Encrypted sessions work with any database ADK supports — SQLite, PostgreSQL, MySQL, MariaDB — with zero additional configuration beyond what ADK already provides. The ~800-line raw aiosqlite implementation is replaced by a thin wrapper around DatabaseSessionService via SQLAlchemy TypeDecorator, focused solely on encryption — the project's actual value-add. The encryption core (EncryptionBackend protocol, FernetBackend, serialization envelope) is untouched. aiosqlite is removed as a direct dependency.

**FRs covered:** FR-NEW-4, FR-NEW-5, FR-NEW-6
**Existing FRs superseded:** FR11 (reworded: multi-DB), FR12 (obsoleted by wrapping)
**Existing FRs remapped:** FR49 (PostgreSQL — collapses from Epic 4 to Epic 7)
**NFRs served:** NFR5, NFR20, NFR25, NFR26
**Scope:** Spike-gated. Code rewrite + tests + new ADR + docs.
**Dependencies:** Epic 6 (soft — fix narrative before changing architecture). Story 7.1 spike gates all subsequent stories.
**Impact on existing epics:**
- Epic 3: Unaffected (encryption backends decoupled from persistence)
- Epic 4 Stories 4.1, 4.2, 4.3: [SUPERSEDED by Epic 7]
- Epic 4 Stories 4.4-4.7: Unchanged
- Epic 5: Unaffected (protocol-based backends)

---

## Epic 1: Ship to PyPI

A developer discovers adk-secure-sessions on PyPI, installs in one command, gets IDE autocomplete, and finds the library credible (SECURITY.md, clean README, zero-warning tests). The maintainer publishes releases reliably via CI/CD. Configuration errors are caught at startup, not runtime.

### Story 1.1: Test Infrastructure Foundation

As a **library maintainer**,
I want **shared test fixtures, conftest files at each test level, and registered pytest markers**,
So that **subsequent test stories have proper infrastructure and the test suite is organized for unit, integration, and benchmark tests**.

**Acceptance Criteria:**

**Given** the test directory structure exists with `tests/unit/` and `tests/integration/`
**When** I create `tests/conftest.py`, `tests/unit/conftest.py`, and `tests/integration/conftest.py`
**Then** shared fixtures are available at the appropriate scope, including at minimum: `fernet_backend` fixture, `encryption_key` fixture, `db_path` fixture (temp file), and `encrypted_service` async generator fixture with cleanup
**And** `pyproject.toml` registers `benchmark` and `integration` markers in `[tool.pytest.ini_options]`
**And** running `uv run pytest` discovers all existing tests without errors
**And** async generator fixtures use `yield svc; await svc.close()` pattern for database cleanup (NFR19)

### Story 1.2: Schema Reservation for Optimistic Concurrency

As a **library maintainer**,
I want **a `version INTEGER DEFAULT 1` column on `sessions`, `app_states`, and `user_states` tables**,
So that **early adopters won't face a breaking schema migration when Phase 3 optimistic concurrency ships**.

**Acceptance Criteria:**

**Given** the `_init_db` method in `EncryptedSessionService` creates the database schema
**When** the schema is initialized on a fresh database
**Then** the `sessions` table has a `version` column with `INTEGER DEFAULT 1`
**And** the `app_states` table has a `version` column with `INTEGER DEFAULT 1`
**And** the `user_states` table has a `version` column with `INTEGER DEFAULT 1`
**And** the `events` table does NOT have a `version` column (append-only, excluded per Architecture Decision 1)
**And** a test verifies column existence via `PRAGMA table_info` and asserts default value is 1
**And** no existing INSERT, UPDATE, or SELECT statements reference the `version` column (column is purely reserved and inert)
**And** existing CRUD operations continue to work unchanged
**And** all existing tests pass

### Story 1.3: ConfigurationError & Startup Validation

As a **developer using the library**,
I want **clear error messages when I misconfigure EncryptedSessionService**,
So that **I catch bad encryption keys or invalid backends at startup, not as cryptic runtime failures**.

**Acceptance Criteria:**

**Given** `ConfigurationError` does not exist in the exception hierarchy
**When** I add `ConfigurationError` as a subclass of `SecureSessionError` to `exceptions.py`
**Then** `ConfigurationError` is exported from `__init__.py` and appears in `__all__`
**And** `ConfigurationError` has a Google-style docstring with an Examples section

**Given** an `EncryptedSessionService` is instantiated with an empty encryption key
**When** the constructor validates the configuration
**Then** a `ConfigurationError` is raised with a message specifying the expected key format

**Given** an `EncryptedSessionService` is instantiated with a backend that does not satisfy `EncryptionBackend` protocol
**When** the constructor validates the backend
**Then** a `ConfigurationError` is raised indicating the backend does not conform to the protocol

**Given** a valid encryption key and backend are provided
**When** the constructor validates the configuration
**Then** no error is raised and the service initializes normally

**And** ADR-006 is created documenting the ConfigurationError decision, following ADR-005's format, citing the "add when code demands" principle, and including: context, decision, rationale, consequences, and alternatives considered
**And** the error message never includes the encryption key value (FR25/NFR6)
**And** database connection failures raise exceptions that include the database file path, OS error code, and suggested remediation (NFR14)
**And** all existing tests pass

### Story 1.4: Zero-Warning Test Suite

As a **developer evaluating the library**,
I want **`uv run pytest` to produce zero warnings and clean output**,
So that **running the test suite doesn't undermine confidence in the library's quality**.

**Acceptance Criteria:**

**Given** the current test suite may produce pytest warnings
**When** I run `uv run pytest`
**Then** the output shows zero warnings (FR32, NFR16)
**And** no deprecation warnings from dependencies appear
**And** no `PytestUnraisableExceptionWarning` or async cleanup warnings appear
**And** code coverage remains >= 90% (NFR18)
**And** the test suite is run 5 times sequentially on the same commit with all 5 runs passing to verify no flaky tests (NFR17), with results documented — this is a one-time pre-release gate, not an ongoing CI requirement

### Story 1.5: Encryption Overhead Benchmark

As a **library maintainer**,
I want **an automated benchmark test verifying encryption overhead is less than 20% of total session operation time**,
So that **I have continuous proof that encryption doesn't degrade performance unacceptably**.

**Acceptance Criteria:**

**Given** a typical session state dictionary of <= 10KB serialized
**When** the benchmark test measures encrypted vs. unencrypted round-trip time using `time.perf_counter()`
**Then** encryption overhead is less than 20% of the total operation time (NFR1)
**And** the baseline measurement is an unencrypted session round-trip using the same database path and payload
**And** the test is marked with `@pytest.mark.benchmark`
**And** the assertion uses relative overhead (`< 1.20x` baseline), not absolute timing
**And** in CI, the benchmark test emits a warning on threshold breach rather than failing the build (CI runners have variable hardware performance)
**And** locally, the test fails on threshold breach for developer feedback
**And** the CI-vs-local behavior switch uses an environment variable (e.g., `CI=true`) or pytest marker to select assertion mode

### Story 1.6a: ADK Runner Integration Test

As a **library maintainer**,
I want **an integration test proving EncryptedSessionService works as an ADK drop-in**,
So that **I can ship with confidence that the library satisfies the BaseSessionService contract in a real ADK pipeline**.

**Acceptance Criteria:**

**Given** an `EncryptedSessionService` instance configured with a FernetBackend
**When** an ADK Runner (or equivalent test harness) accepts it where it expects `BaseSessionService`
**Then** a complete session lifecycle (create, append event, get, delete) executes successfully (NFR20)
**And** the test verifies this via actual execution, not just `isinstance` check
**And** the test is marked with `@pytest.mark.integration`
**And** integration conftest fixtures properly close database connections on teardown

### Story 1.6b: Concurrent Write Safety Verification

As a **library maintainer**,
I want **a test proving 50 simultaneous async coroutines writing different sessions don't corrupt data**,
So that **I can ship with confidence that the library handles concurrent access safely**.

**Acceptance Criteria:**

**Given** an `EncryptedSessionService` instance with a shared database
**When** 50 async coroutines simultaneously create and write different sessions
**Then** all 50 sessions are recoverable with correct values after all coroutines complete (NFR25)
**And** no data corruption or silent data loss occurs
**And** no `DecryptionError` is raised when reading back the sessions
**And** the test is marked with `@pytest.mark.integration`

### Story 1.7: Package Metadata & Type Safety

As a **developer searching PyPI**,
I want **the library to appear in relevant searches with proper classifiers, and provide full IDE autocomplete**,
So that **I can discover it easily and get type hints when coding against it**.

**Acceptance Criteria:**

**Given** `pyproject.toml` defines the package metadata
**When** the package is built
**Then** `py.typed` marker file exists in `src/adk_secure_sessions/` (FR30, NFR22)
**And** PyPI classifiers include `Topic :: Security :: Cryptography`, `Intended Audience :: Developers`, `License :: OSI Approved :: MIT License` (FR33)
**And** keywords include `adk`, `encryption`, `encrypted sessions`, `google adk security` (FR33)
**And** package description is optimized for discoverability (FR33)
**And** `[project.optional-dependencies]` defines `postgres = []` and `dev = [...]` extras (FR45)
**And** runtime dependencies remain <= 5 (NFR23)
**And** the package installs as a pure Python wheel with no compiled extensions (NFR21)
**And** no `[all]` extras group exists — this is a deliberate security decision to minimize installed surface

### Story 1.8: SECURITY.md

As a **compliance reviewer evaluating the library**,
I want **a SECURITY.md with responsible disclosure policy and supported versions**,
So that **I can verify the project takes security seriously — missing this is an instant disqualification**.

**Acceptance Criteria:**

**Given** no SECURITY.md exists in the repository root
**When** I create SECURITY.md
**Then** it includes a Supported Versions table listing currently supported versions (FR39)
**And** it includes a Reporting a Vulnerability section with clear email/process for disclosure
**And** it includes a Response Timeline section specifying 48-hour acknowledgment SLA for critical vulnerabilities
**And** it references the project's use of the `cryptography` library (no custom primitives)
**And** it does NOT include any encryption keys, tokens, or sensitive configuration
**And** the format follows standard GitHub SECURITY.md conventions

### Story 1.9: README Rewrite

As a **developer discovering the library for the first time**,
I want **a README with compliance gateway positioning, a quick-start code example, and status badges**,
So that **I understand the value proposition in 30 seconds and can add encrypted sessions in 5 minutes**.

**Acceptance Criteria:**

**Given** the current README exists
**When** it is rewritten with compliance gateway positioning
**Then** the tagline communicates "Compliance Gateway for Google ADK" (not "encryption library")
**And** the section hierarchy is: badges at top, one-liner description, install command, quick-start code block, then links to docs/SECURITY/contributing
**And** the quick-start code example is 5 lines or fewer showing the exact swap from `BaseSessionService` to `EncryptedSessionService` — real code, not pseudocode (FR34)
**And** badges display PyPI version, Python version, test status, and coverage (FR40)
**And** the license (MIT), dependency tree, and test coverage are verifiable from the README (FR40)
**And** the README links to the documentation site (when available) and SECURITY.md
**And** NFR28 is supported: a developer can go from `pip install` to encrypted sessions in under 5 minutes using only the README

### Story 1.10: Trunk-Based Migration to Main

As a **library maintainer**,
I want **the repository migrated from develop-based branching to main as the default branch**,
So that **the publish pipeline can trigger on release tags from main, following standard open-source conventions**.

**Acceptance Criteria:**

**Given** the repository uses `develop` as the primary branch
**When** I migrate to trunk-based development with `main` as default
**Then** `main` exists and contains the current `develop` content
**And** CI workflows (tests.yml, docs.yml, release-please.yml) are updated to reference `main` instead of `develop`
**And** branch protection rules are applied to `main`
**And** the publish pipeline can be configured to trigger on release tags (enables Story 1.11)

### Story 1.11: CI/CD Publish Pipeline

As a **library maintainer**,
I want **a GitHub Actions workflow that publishes to TestPyPI and PyPI on release tags, with its own test suite and security audit**,
So that **I can release reliably knowing the published artifact is tested and dependency-audited**.

**Acceptance Criteria:**

**Given** a release tag is pushed (e.g., `v0.1.0`)
**When** the publish workflow triggers
**Then** it runs the full test suite independently (not trusting branch protection) — security library requirement
**And** it runs `pip-audit` to verify zero known CVEs in dependencies (NFR8)
**And** it runs `interrogate` to verify docstring coverage alignment (closing the CI/local gap identified in Architecture)
**And** it publishes to TestPyPI first for validation (FR43)
**And** it publishes to PyPI after TestPyPI succeeds (FR42)
**And** the changelog is auto-generated from conventional commits via release-please (FR44)
**And** the workflow does NOT contain hardcoded tokens (uses GitHub secrets)
**And** the workflow is validated by a dry run against TestPyPI before the first real release

### Story 1.12: v0.1.0 Release & Community Announcement

As a **developer searching for ADK session encryption**,
I want **the library published on PyPI and announced in the community**,
So that **the first "how to encrypt ADK sessions" post defines SEO and I can find and install it**.

**Acceptance Criteria:**

**Given** all previous Epic 1 stories are complete
**When** v0.1.0 is released to PyPI
**Then** `pip install adk-secure-sessions` succeeds from a clean virtual environment (FR27)
**And** the installed package provides IDE autocomplete and type checking (FR30)
**And** the PyPI package page displays correct metadata, classifiers, and description (FR33)
**And** a GitHub Discussion post is published within 24 hours of the PyPI release
**And** the Discussion post includes install instructions, key features, and the keyword phrase "encrypt ADK sessions" for SEO positioning

---

## Epic 2: Documentation & Compliance Credibility

Marcus (enterprise dev) evaluates via full documentation site. Diane (compliance reviewer) approves from ADR trail, algorithm docs with NIST references, and envelope protocol spec. Developers get IDE tooltips from docstring examples.

### Story 2.1: Docstring Examples on All Public APIs

As a **developer reading API documentation or IDE tooltips**,
I want **every public function and class to have an `Examples:` section with fenced code blocks**,
So that **I can see real usage patterns without leaving my editor or the API reference page**.

**Acceptance Criteria:**

**Given** 13 public symbols are exported from `__init__.py`
**When** I add `Examples:` sections with fenced code blocks to all public API docstrings
**Then** every public class and function has at least one working code example in its docstring (FR41)
**And** examples use Google-style docstring format with fenced code blocks (not `>>>` doctest style)
**And** example depth matches the symbol type:
  - `EncryptedSessionService`: full lifecycle example (instantiate, create session, get session, close)
  - `FernetBackend`: standalone instantiation example
  - `encrypt_session` / `decrypt_session`: round-trip example
  - Exception classes: try/except example showing when raised
  - `EncryptionBackend` protocol: custom backend implementation example
**And** any inconsistencies between docstrings and actual signatures discovered during example writing are fixed
**And** `interrogate` reports >= 95% docstring coverage
**And** `griffe` parses all docstrings without errors
**And** `bash scripts/code_quality_check.sh --all --verbose` passes after all examples are written
**And** docvet pre-commit hook passes on all modified files

### Story 2.2: MkDocs Documentation Site Setup

As a **developer evaluating the library**,
I want **a documentation site with auto-generated API reference and published ADRs**,
So that **I can browse comprehensive documentation without reading raw source files**.

**Acceptance Criteria:**

**Given** `mkdocs.yml` exists and MkDocs Material is configured
**When** the documentation site is built with `uv run mkdocs build --strict`
**Then** the site builds without errors or warnings (strict mode — warnings are errors)
**And** auto-generated API reference pages render correctly for all public symbols via mkdocstrings (FR35)
**And** `gen_ref_pages.py` is verified to use dynamic module discovery (walk `src/` tree), not hardcoded paths — updated if necessary
**And** all ADRs (ADR-000 through ADR-006) are accessible in the navigation (FR36)
**And** the site navigation accommodates all documentation pages created in this epic (Getting Started, API Reference, Architecture Decisions, Roadmap, Envelope Protocol Spec, Algorithm Documentation, FAQ) with a structure extensible for future pages
**And** the docs CI workflow (`docs.yml`) verifies the build with `--strict` on PRs
**And** docvet pre-commit hook passes on all new/modified documentation files

### Story 2.3: Envelope Protocol & Algorithm Specification Pages

As a **compliance reviewer or enterprise developer**,
I want **dedicated documentation pages for the envelope protocol specification and encryption algorithm details with NIST/FIPS references**,
So that **I can verify the cryptographic approach meets my organization's security requirements**.

**Acceptance Criteria:**

**Given** the envelope protocol format `[version_byte][backend_id_byte][ciphertext]` is documented in ADR-000
**When** a dedicated Envelope Protocol Specification page is created in the docs site
**Then** it describes the binary layout with exact byte positions (FR37):
  - Version byte: `0x01`, position 0 — role in future protocol evolution
  - Backend ID byte: position 1 — maps to registered backend (Fernet = `0x01`), role in multi-backend dispatch
  - Ciphertext: position 2 onwards — produced by the backend's `encrypt()` method
  - Total envelope size: `len(ciphertext) + 2` bytes
**And** it explains how backend dispatch works based on the backend ID byte
**And** it includes a Mermaid diagram showing the envelope structure

**Given** the Fernet backend uses AES-128-CBC + HMAC-SHA256 + PBKDF2
**When** an Algorithm Documentation page is created
**Then** it lists the algorithm name, key size, mode of operation, and key derivation function (FR38)
**And** it includes a Compliance Mapping table mapping each component to its NIST/FIPS reference:
  - AES-128-CBC → NIST SP 800-38A
  - HMAC-SHA256 → FIPS 198-1
  - PBKDF2 → NIST SP 800-132
**And** it documents the `cryptography` library delegation — no custom primitives
**And** docvet pre-commit hook passes on all new documentation files

### Story 2.4: Published Roadmap on Documentation Site

As a **developer or compliance reviewer**,
I want **a published roadmap on the docs site showing phase timeline and planned capabilities**,
So that **I can evaluate the project's trajectory and plan my adoption timing (e.g., waiting for AES-256-GCM)**.

**Acceptance Criteria:**

**Given** `docs/ROADMAP.md` exists with phase definitions
**When** the roadmap is included in the MkDocs site navigation
**Then** it displays the 4-phase timeline (Core, Ship, Expand, Enterprise) (FR56)
**And** it lists planned capabilities per phase
**And** it includes the backend upgrade schedule (Fernet now, AES-256-GCM in Phase 3, KMS in Phase 4)
**And** the content is verified against the PRD's phase definitions for consistency
**And** docvet pre-commit hook passes on any modified roadmap files

### Story 2.5: FAQ Page

As a **developer with common questions about the library**,
I want **a FAQ page answering key questions about algorithms, compliance, and architecture**,
So that **I don't need to read the full ADR trail to understand basic decisions**.

**Acceptance Criteria:**

**Given** the PRD and user journeys identify common evaluator questions
**When** a FAQ page is created in the docs site
**Then** it answers at minimum these 6 questions:
  1. "What algorithms does Fernet use?"
  2. "Is this HIPAA compliant?" — answer MUST use exact PRD positioning language: "Designed to support encryption-at-rest requirements for HIPAA, SOC 2, PCI-DSS, and GDPR regulated environments. Certification belongs to the deploying organization." Never claim certification.
  3. "Why Protocols not ABC?"
  4. "Can I use a different encryption backend?"
  5. "What happens if I use the wrong decryption key?" — explains DecryptionError, never silent corruption
  6. "Does this encrypt the entire database or just session data?" — explains field-level vs. full-DB
**And** answers are concise (3-5 sentences each) with links to detailed docs where applicable
**And** the FAQ is accessible from the docs site navigation
**And** docvet pre-commit hook passes on all new documentation files

### Story 2.6: Getting Started Guide

As a **developer adding encrypted sessions to an existing ADK agent**,
I want **a Getting Started guide with a full working example and verification steps**,
So that **I can go from install to encrypted sessions in under 5 minutes with confidence that it's working**.

**Acceptance Criteria:**

**Given** the README provides a 5-line quick-start swap
**When** a Getting Started guide page is created in the docs site
**Then** it includes:
  1. Install command (`pip install adk-secure-sessions`)
  2. Full working agent example with encrypted sessions (complete runnable code, not just the swap)
  3. Verification step: how to confirm sessions are encrypted (e.g., inspect SQLite file)
  4. "What's next?" links to API Reference, Architecture Decisions, and FAQ
**And** the guide supports NFR28: a developer can go from install to encrypted sessions in under 5 minutes
**And** the example uses realistic session state (not empty dict or trivial placeholder)
**And** docvet pre-commit hook passes on all new documentation files

---

## Epic 3: AES-256-GCM Backend & Security Hardening (Phase 3)

Enterprise security teams approve unconditionally with AES-256-GCM. Per-key random salt hardens key derivation. Multiple backends coexist via envelope protocol for seamless migration.

### Story 3.1: AES-256-GCM Encryption Backend

As a **security-conscious developer**,
I want **an AES-256-GCM encryption backend as an alternative to Fernet**,
So that **I can meet enterprise security requirements that mandate AES-256-GCM or authenticated encryption with associated data (AEAD)**.

**Acceptance Criteria:**

**Given** the `EncryptionBackend` protocol defines `encrypt`, `decrypt`, and `backend_id`
**When** I implement `AesGcmBackend` conforming to the protocol
**Then** it uses AES-256-GCM (256-bit key, 96-bit nonce, 128-bit tag) via the `cryptography` library (FR46)
**And** the backend generates a cryptographically random nonce per encryption operation (never reused)
**And** `backend_id` returns a unique byte value (e.g., `0x02`) distinct from Fernet's `0x01`
**And** the backend is registered in the envelope protocol's backend dispatch map
**And** encrypted data is wrapped in the standard envelope format `[version_byte][backend_id_byte][ciphertext]` — envelope compatibility verified by round-trip test (FR4)
**And** `isinstance(AesGcmBackend(), EncryptionBackend)` returns `True` at runtime (FR18)
**And** all cryptography operations are wrapped in `asyncio.to_thread()` (NFR2)
**And** wrong-key decryption raises `DecryptionError`, never returns garbage data (FR22, NFR7)
**And** the backend is exported from `__init__.py` and appears in `__all__`
**And** Google-style docstring with `Examples:` section using fenced code blocks
**And** existing Fernet tests continue to pass unchanged

### Story 3.2: Per-Key Random Salt Key Derivation

As a **security engineer**,
I want **each key derivation to use a unique cryptographically random salt**,
So that **identical passphrases produce different derived keys, hardening against precomputation attacks**.

**Acceptance Criteria:**

**Given** the current key derivation may use a fixed or no salt
**When** I implement per-key random salt derivation
**Then** each key derivation generates a unique salt of >= 16 bytes using `os.urandom()` (NFR11, FR47)
**And** the salt is stored alongside the ciphertext in a self-describing format that enables decryption to locate and extract the salt
**And** a salt detection mechanism exists: during decryption, the system determines whether the ciphertext was produced with salt or without salt (for backward compatibility with pre-salt data)
**And** backward compatibility is maintained: data encrypted without salt (pre-Phase 3) can still be decrypted
**And** new encryptions always use per-key random salt
**And** a round-trip test verifies: encrypt with salt → decrypt → original data matches
**And** a test verifies that two encryptions of the same plaintext with the same passphrase produce different ciphertexts (salt uniqueness)
**And** the salt is never logged, included in error messages, or exposed in exception context (NFR6)
**And** an ADR is created documenting where the salt is stored relative to the envelope format (inside the backend-specific ciphertext blob vs. extending the envelope header) — this is a wire protocol decision that affects backward compatibility and multi-backend dispatch

### Story 3.3: Multi-Backend Coexistence & Dispatch

As an **operator migrating from Fernet to AES-256-GCM**,
I want **the system to support multiple encryption backends simultaneously, dispatching decryption based on the envelope header**,
So that **I can migrate incrementally without re-encrypting all existing sessions at once**.

**Acceptance Criteria:**

**Given** the envelope protocol contains a backend ID byte at position 1
**When** the system is configured with multiple backends (e.g., Fernet + AES-256-GCM)
**Then** new sessions are encrypted with the configured primary backend (FR21)
**And** existing sessions are decrypted by the backend matching the envelope's backend ID byte (FR20)
**And** a session encrypted with Fernet (`0x01`) is correctly decrypted even when AES-256-GCM (`0x02`) is the primary backend
**And** a session encrypted with AES-256-GCM is correctly decrypted even when Fernet is the primary backend
**And** attempting to decrypt with a backend that doesn't match the envelope's backend ID dispatches to the correct backend, not the configured primary
**And** a negative test verifies: if the envelope references an unregistered backend ID, the system raises a clear error (not silent corruption or fallback to wrong backend)
**And** the backend registry supports dynamic registration without modifying library internals (FR19)
**And** an integration test verifies a mixed-backend scenario: create sessions with different backends, list all, verify all decrypt correctly

### Story 3.4: Published Performance Benchmarks

As a **developer evaluating the library**,
I want **published benchmark results documenting actual overhead per operation across representative payload sizes**,
So that **I can make an informed decision about which backend to use based on real performance data**.

**Acceptance Criteria:**

**Given** both Fernet and AES-256-GCM backends are available
**When** benchmark tests are run across representative payload sizes (empty dict, 1KB, 10KB, 100KB)
**Then** results document actual overhead per operation: encrypt, decrypt, and full round-trip (NFR4)
**And** results are published in the documentation site as a Benchmarks page
**And** benchmark tests are marked with `@pytest.mark.benchmark`
**And** the benchmarks page includes methodology (hardware-independent relative comparisons, not absolute times)
**And** the page documents the performance characteristics of each backend with a comparison table
**And** docvet pre-commit hook passes on all new documentation files

---

## Epic 4: PostgreSQL Persistence & Key Rotation (Phase 3)

Teams run encrypted sessions on managed PostgreSQL. Operators rotate keys with zero downtime. Backend authors and operators get dedicated documentation. The service architecture is decomposed for extensibility.

> **Revision Note (2026-03-04):** Epic 4's scope has been reduced. Stories 4.1 (Persistence Protocol & SQLite Extraction), 4.2 (Encryption Coordinator Extraction), and 4.3 (PostgreSQL Persistence Backend) are superseded by Epic 7 (Architecture Migration). ADK V1 changed state merging from SQL-side `json_patch` to Python-side `dict | delta`, making `DatabaseSessionService` wrapping viable and collapsing the persistence extraction work into the architecture migration. Epic 4 retains Stories 4.4 (Key Rotation), 4.5 (Backend Docs), 4.6 (Ops Guide), and 4.7 (Python Version Tracking). See Issue #118 and Epic 7 for the architectural evolution path.

### Story 4.1: Persistence Protocol & SQLite Extraction [SUPERSEDED by Epic 7]

As a **library maintainer**,
I want **the persistence layer extracted behind a Protocol interface with SQLite as the first implementation**,
So that **adding PostgreSQL (and future backends) doesn't require modifying the core service logic**.

**Acceptance Criteria:**

**Given** `EncryptedSessionService` currently contains SQLite-specific database operations inline
**When** I extract the persistence layer
**Then** a `PersistenceBackend` Protocol (PEP 544, `@runtime_checkable`) is defined with async methods for: create session, get session, list sessions, delete session, append events, initialize schema, close connection
**And** `SqlitePersistenceBackend` implements the protocol using existing aiosqlite logic (extracted, not rewritten)
**And** `isinstance(SqlitePersistenceBackend(), PersistenceBackend)` returns `True` at runtime
**And** `EncryptedSessionService` depends on the `PersistenceBackend` protocol, not the SQLite implementation directly
**And** all existing tests pass without modification (behavior unchanged, only structure refactored)
**And** the protocol is exported from `__init__.py` and appears in `__all__`
**And** Google-style docstring with `Examples:` section on the protocol and implementation
**And** the `version` column (reserved in Story 1.2) is preserved in the extracted schema

### Story 4.2: Encryption Coordinator Extraction [SUPERSEDED by Epic 7]

As a **library maintainer**,
I want **the encryption orchestration logic extracted into a dedicated coordinator**,
So that **the service orchestrator has clear separation of concerns: persistence, encryption, and coordination**.

**Acceptance Criteria:**

**Given** `EncryptedSessionService` currently handles both persistence and encryption orchestration
**When** I extract the encryption coordinator
**Then** an `EncryptionCoordinator` class encapsulates: backend selection, envelope creation, encrypt/decrypt dispatch, and backend registry management
**And** `EncryptedSessionService` composes `PersistenceBackend` + `EncryptionCoordinator` (from Story 4.1 and this story)
**And** the coordinator is responsible for: selecting the correct backend for encryption, dispatching decryption based on envelope header, managing the backend registry
**And** all existing tests pass without modification (behavior unchanged, only structure refactored)
**And** the coordinator is exported from `__init__.py` and appears in `__all__`
**And** Google-style docstring with `Examples:` section
**And** the refactoring does not change any public API signatures (NFR20 — drop-in compatibility preserved)

### Story 4.3: PostgreSQL Persistence Backend [SUPERSEDED by Epic 7]

As a **team running ADK agents in production**,
I want **encrypted session persistence to PostgreSQL as an alternative to SQLite**,
So that **I can use managed PostgreSQL for high-availability, multi-instance deployments**.

**Acceptance Criteria:**

**Given** the `PersistenceBackend` protocol exists (from Story 4.1)
**When** I implement `PostgresPersistenceBackend`
**Then** it conforms to the `PersistenceBackend` protocol (FR49)
**And** `isinstance(PostgresPersistenceBackend(), PersistenceBackend)` returns `True` at runtime
**And** it uses the async PostgreSQL driver chosen for Phase 3 (asyncpg or psycopg3 — driver decision resolved before implementation)
**And** the schema mirrors the SQLite schema (same table structure, same `version` column reservation)
**And** all session CRUD operations work identically to SQLite (create, get, list, delete, append events)
**And** all data passes through the encryption path — no plaintext touches PostgreSQL (NFR5)
**And** concurrent writer test: >= 10 concurrent instances writing without data loss (NFR26)
**And** the backend is installed via the `[postgres]` extras group (`pip install adk-secure-sessions[postgres]`)
**And** integration tests use a PostgreSQL test instance (e.g., testcontainers or CI-provided PostgreSQL service) — the test infrastructure approach is documented in the story's implementation plan
**And** Google-style docstring with `Examples:` section

### Story 4.4: Zero-Downtime Key Rotation

As an **operator managing encryption keys in production**,
I want **to rotate encryption keys with zero downtime using a decrypt-with-old, encrypt-with-new strategy**,
So that **I can meet key rotation compliance requirements without disrupting active sessions**.

**Acceptance Criteria:**

**Given** the system supports multiple backends via the backend registry
**When** key rotation is initiated
**Then** the operator configures both old and new keys, specifying which is the active encryption key (FR48)
**And** new sessions and updates are encrypted with the new key
**And** existing sessions encrypted with the old key are decrypted successfully (using envelope header to identify the key)
**And** a migration utility or strategy exists to re-encrypt existing sessions with the new key (batch or on-access — the chosen strategy is documented)
**And** the rotation strategy is clearly documented: whether rotation is batch (re-encrypt all at once), lazy (re-encrypt on next access), or configurable — with trade-offs explained
**And** stale session updates during rotation are detected and rejected via optimistic concurrency using the `version` column (NFR27)
**And** key rotation never exposes old or new keys in logs or error messages (NFR6)
**And** an integration test verifies the full rotation lifecycle: create with old key → rotate → read with old key succeeds → write with new key → read with new key succeeds

### Story 4.5: Backend Authoring Documentation

As a **developer creating a custom encryption backend**,
I want **comprehensive documentation with examples and a starter template for authoring backends**,
So that **I can implement a conformant backend without reading the library's source code**.

**Acceptance Criteria:**

**Given** the `EncryptionBackend` protocol defines the backend contract
**When** a Backend Authoring Guide page is created in the docs site
**Then** it includes (FR50):
  1. The protocol contract with each method explained (encrypt, decrypt, backend_id)
  2. A complete working example of a custom backend implementation
  3. Testing guidance: how to verify protocol conformance, round-trip correctness, and envelope compatibility
  4. Registration instructions: how to register a custom backend with the service
  5. A starter template (cookiecutter or copy-paste ready) that a backend author can use as a starting point
**And** the guide explains backend ID assignment: how to choose a unique backend ID, the reserved range (0x01-0x0F for official backends), and the community range (0x10-0xFF)
**And** the guide includes common pitfalls and anti-patterns (e.g., nonce reuse, blocking the event loop)
**And** docvet pre-commit hook passes on all new documentation files

### Story 4.6: Operations Guide

As an **operator deploying and maintaining encrypted sessions**,
I want **an operations guide covering key configuration, rotation procedures, monitoring, and troubleshooting**,
So that **I can run encrypted sessions in production confidently and respond to incidents quickly**.

**Acceptance Criteria:**

**Given** operators need guidance beyond the developer-focused API docs
**When** an Operations Guide page is created in the docs site
**Then** it includes (FR51):
  1. Key management: how to generate, configure, and store encryption keys securely
  2. Key rotation: step-by-step procedure referencing Story 4.4's rotation strategy
  3. Database setup: SQLite configuration for development, PostgreSQL configuration for production
  4. Monitoring guidance: what metrics/signals to watch (decryption error rates, session operation latency, database connection pool health), and how to integrate with common observability stacks
  5. Troubleshooting: common error scenarios (wrong key, corrupted envelope, database connection failures) with resolution steps
  6. Backup and recovery: considerations for backing up encrypted session data
**And** the guide includes an upgrade/migration section for users moving from Phase 2 (Fernet + SQLite) to Phase 3 (AES-256-GCM + PostgreSQL), covering data migration steps and backward compatibility guarantees
**And** the guide is written for operators, not developers (focuses on deployment, not API usage)
**And** docvet pre-commit hook passes on all new documentation files

### Story 4.7: Python Version Matrix Tracking

As a **library maintainer**,
I want **a documented process and CI configuration for tracking google-adk's Python version support matrix**,
So that **when ADK supports Python 3.13+, the library follows within one minor release**.

**Acceptance Criteria:**

**Given** google-adk currently supports Python 3.12 and may add 3.13+ support
**When** a Python version tracking process is established
**Then** the CI matrix tests against all Python versions supported by google-adk (NFR24)
**And** a documented process exists for adding new Python versions: check ADK's `requires-python`, update `pyproject.toml`, update CI matrix, run full test suite
**And** the process targets following ADK's Python version additions within one minor release
**And** the CI workflow (e.g., `tests.yml`) is parameterized to make Python version additions a single-line change
**And** the docs site Roadmap page mentions Python version tracking as an ongoing commitment

---

## Epic 5: Enterprise KMS Backends & Audit (Phase 4)

Enterprise teams use managed KMS providers (AWS, GCP, Vault) with organization-mandated key management, and produce audit trails of encryption operations for compliance reporting.

### Story 5.1: Backend Ecosystem Architecture

As a **library maintainer**,
I want **a backend ecosystem architecture with a registry, entry-point discovery, and packaging strategy**,
So that **third-party backends can be distributed as separate packages and discovered automatically**.

**Acceptance Criteria:**

**Given** backends are currently registered manually with the service
**When** the backend ecosystem architecture is implemented
**Then** a backend registry exists with entry-point based discovery (e.g., `setuptools` entry points or `importlib.metadata`)
**And** third-party backends can register via their package's entry points without modifying library internals
**And** the registry validates backend conformance at discovery time via `isinstance` check against `EncryptionBackend` protocol
**And** a backend packaging strategy is documented: naming convention (e.g., `adk-secure-sessions-backend-{name}`), required entry points, versioning expectations
**And** the API surface follows the flat namespace strategy (decided in Phase 3) or submodule imports — whichever was chosen
**And** existing manual registration continues to work (backward compatible)
**And** CONTRIBUTING.md is updated with backend contribution guidelines: how to propose a new backend, required conformance tests, packaging conventions, and the review process

### Story 5.2: AWS KMS Backend

As an **enterprise developer using AWS**,
I want **an AWS KMS encryption backend for adk-secure-sessions**,
So that **I can use my organization's AWS KMS keys for session encryption, meeting AWS-centric compliance requirements**.

**Acceptance Criteria:**

**Given** the backend ecosystem architecture exists (from Story 5.1)
**When** an AWS KMS backend is implemented
**Then** it conforms to the `EncryptionBackend` protocol (FR52)
**And** it uses AWS KMS `Encrypt` and `Decrypt` API calls via `boto3` (async wrapped)
**And** the backend accepts a KMS key ARN or alias as configuration
**And** it is distributed as a separate package (e.g., `adk-secure-sessions-backend-aws-kms`) or as an extras group
**And** it registers via entry-point discovery
**And** encrypted data uses the standard envelope format with a unique backend ID
**And** integration tests verify round-trip encryption/decryption against AWS KMS (using localstack or mocked AWS APIs in CI)
**And** wrong-key decryption raises `DecryptionError` (NFR7)
**And** this backend serves as the **official reference implementation** for KMS-style backends — demonstrating the integration pattern, test strategy, and packaging conventions that community-contributed backends (GCP, Azure, etc.) should follow

### Story 5.3: GCP Cloud KMS Backend

As an **enterprise developer using GCP**,
I want **a GCP Cloud KMS encryption backend for adk-secure-sessions**,
So that **I can use my organization's GCP KMS keys for session encryption, meeting GCP-centric compliance requirements**.

**Acceptance Criteria:**

**Given** the backend ecosystem architecture exists (from Story 5.1)
**When** a GCP Cloud KMS backend is implemented
**Then** it conforms to the `EncryptionBackend` protocol (FR53)
**And** it uses GCP Cloud KMS `encrypt` and `decrypt` API calls via `google-cloud-kms` (async wrapped)
**And** the backend accepts a KMS key resource name as configuration
**And** it is distributed as a separate package or extras group
**And** it registers via entry-point discovery
**And** encrypted data uses the standard envelope format with a unique backend ID
**And** integration tests verify round-trip encryption/decryption against GCP KMS (using emulator or mocked APIs in CI)
**And** wrong-key decryption raises `DecryptionError` (NFR7)
**And** the backend is marked as a candidate for community contribution — the library may provide the reference implementation or accept it as a community-contributed backend

### Story 5.4: HashiCorp Vault Backend

As an **enterprise developer using HashiCorp Vault**,
I want **a Vault Transit secrets engine backend for adk-secure-sessions**,
So that **I can leverage Vault's centralized key management and audit logging for session encryption**.

**Acceptance Criteria:**

**Given** the backend ecosystem architecture exists (from Story 5.1)
**When** a HashiCorp Vault backend is implemented
**Then** it conforms to the `EncryptionBackend` protocol (FR54)
**And** it uses the Vault Transit secrets engine `encrypt` and `decrypt` endpoints via `hvac` (async wrapped)
**And** the backend accepts Vault address, token/auth method, and transit key name as configuration
**And** it is distributed as a separate package or extras group
**And** it registers via entry-point discovery
**And** encrypted data uses the standard envelope format with a unique backend ID
**And** integration tests verify round-trip encryption/decryption against Vault (using Vault dev server in CI)
**And** wrong-key decryption raises `DecryptionError` (NFR7)

### Story 5.5: Audit Logging & Compliance Reporting

As a **compliance officer**,
I want **audit logs of all encryption operations with timestamps, backend used, and operation type**,
So that **I can produce compliance reports showing encryption activity for regulatory audits**.

**Acceptance Criteria:**

**Given** the system performs encryption and decryption operations
**When** audit logging is enabled
**Then** each encryption operation emits a structured audit event containing: timestamp, operation type (encrypt/decrypt), backend ID, session ID (not the session state), success/failure status (FR55)
**And** audit events are emitted via Python's `logging` module to a dedicated logger (`adk_secure_sessions.audit`)
**And** the audit logger NEVER includes: encryption keys, plaintext data, ciphertext content, or any PII from session state (NFR6)
**And** audit logging is opt-in (disabled by default) to minimize performance impact
**And** the compliance reporting section in the Operations Guide documents: how to enable audit logging, how to route audit logs to SIEM systems, what fields are available for querying
**And** documentation includes a FIPS 140-2 deployment guide section with honest limitations: the library uses NIST-approved algorithms via the `cryptography` library, but FIPS 140-2 certification applies to the cryptographic module (OpenSSL), not the library itself — the deploying organization is responsible for certification (NFR12)
**And** an integration test verifies audit events are emitted for a complete session lifecycle (create, get, update, delete)

---

## Epic 6: Documentation Honesty

A developer reading the README, docs site, or PyPI description gets an accurate understanding of what adk-secure-sessions is: an encrypted session persistence service implementing BaseSessionService — not a "drop-in replacement for DatabaseSessionService" or an "encryption layer." A contributor reading CLAUDE.md, conventions, or planning artifacts encounters no false claims about schema independence or table counts. Superseded planning artifacts carry revision markers preserving history.

### Story 6.1: Fix User-Facing "Drop-In Replacement" Claims

As a **developer evaluating the library**,
I want **accurate descriptions of what adk-secure-sessions is on PyPI, README, docs site, and API reference**,
So that **I understand exactly what I'm installing — an encrypted session service implementing BaseSessionService — without false expectations about DatabaseSessionService compatibility**.

**Acceptance Criteria:**

**Given** `pyproject.toml:4` says "drop-in replacement for DatabaseSessionService"
**When** the description is corrected
**Then** it reads "Encrypted session persistence for Google ADK agents" (FR-NEW-1)
**And** the description is concise and appropriate for PyPI package metadata context

**Given** `README.md:13` says "drop-in replacement for DatabaseSessionService"
**When** the description is corrected
**Then** it accurately describes the library as implementing BaseSessionService with encryption (FR-NEW-1)
**And** the language is appropriate for a README audience (medium detail)

**Given** `docs/index.md:13` says "drop-in replacement for ADK's DatabaseSessionService and SqliteSessionService"
**When** the description is corrected
**Then** it accurately describes the library as an encrypted session persistence service (FR-NEW-1)
**And** the docs site landing page provides enough context for a first-time visitor

**Given** `src/adk_secure_sessions/__init__.py:10-11` says "Drop-in replacement for DatabaseSessionService"
**When** the module docstring is corrected
**Then** it accurately references BaseSessionService, not DatabaseSessionService (FR-NEW-1, FR28)

**Given** `src/adk_secure_sessions/services/encrypted_session.py:3,123` says "drop-in replacement for ADK's DatabaseSessionService"
**When** the module and class docstrings are corrected
**Then** they accurately reference BaseSessionService with field-level encryption at rest (FR-NEW-1, FR28)
**And** the docstring is appropriate for API reference context (technical detail)

**Given** `CHANGELOG.md:39` correctly says "drop-in replacement for ADK's BaseSessionService"
**When** reviewing changelog entries
**Then** this entry is NOT modified — it is already accurate

**And** all replacement language is contextually appropriate per the target audience (PyPI short, README medium, docstrings technical, docs site explanatory)
**And** no code logic is changed — only docstrings, descriptions, and documentation text

### Story 6.2: Fix Schema Independence & Architecture Characterization Claims

As a **contributor reading project conventions or planning docs**,
I want **accurate descriptions of the schema relationship with ADK and what the library actually is**,
So that **I don't build on false assumptions about schema independence, table counts, or the library being "just an encryption layer"**.

**Acceptance Criteria:**

**Given** `CLAUDE.md:11` says "own schema independent of ADK"
**When** the description is corrected
**Then** it accurately describes the schema as mirroring ADK V1 structure with encrypted column types, managed via raw aiosqlite (FR-NEW-2)

**Given** `.claude/rules/conventions.md:35-39` "Own Our Schema" section lists only 2 tables and says "independent of ADK's internal schema"
**When** the section is corrected
**Then** it lists all 4 tables (`sessions`, `events`, `app_states`, `user_states`) (FR-NEW-2)
**And** it describes the schema relationship honestly — operationally independent (own tables, own migrations) but structurally mirroring ADK V1
**And** the "raw parametrized SQL via aiosqlite" convention is preserved as accurate-today but noted as an implementation detail that may evolve

**Given** `_bmad-output/project-context.md:73` lists only `(sessions, events)`
**When** the table list is corrected
**Then** it lists all 4 tables: `sessions`, `events`, `app_states`, `user_states` (FR-NEW-2)

**Given** `_bmad-output/planning-artifacts/prd.md:334` lists only 2 tables and says "independent of ADK's internal schema"
**When** the description is corrected
**Then** it lists all 4 tables and uses honest framing about the schema relationship (FR-NEW-2)

**Given** `docs/ROADMAP.md:5` says "missing encryption layer"
**When** the description is corrected
**Then** it uses "encrypted session persistence" or equivalent accurate characterization (FR-NEW-1)

**Given** `_bmad-output/planning-artifacts/prd.md:372` says "encryption layer"
**When** the description is corrected
**Then** it uses accurate characterization consistent with the library being a full session service (FR-NEW-1)

**Given** `docs/project-overview.md:28` exposes "raw SQL via aiosqlite" as implementation detail
**When** the dependency table is reviewed
**Then** the implementation detail is either removed or clearly marked as internal (not user-facing contract)

**Given** `docs/project-overview.md:62-68` frames schema as "independent of ADK internals"
**When** the framing is corrected
**Then** it accurately describes the schema as operationally independent but structurally mirroring ADK V1

**Given** `docs/contributing/docstring-templates.md:51` uses "drop-in replacement for ADK's DatabaseSessionService" as a template
**When** the template is corrected
**Then** it uses accurate language consistent with Story 6.1's corrections

**And** no code logic is changed — only documentation, conventions, and planning artifact text

### Story 6.3: Add Superseded Markers to Planning Artifacts & ADRs

As a **future contributor or AI agent reading planning artifacts**,
I want **revision markers on documents that contain superseded architectural claims**,
So that **I don't build on stale assumptions while still understanding the historical context and reasoning**.

**Acceptance Criteria:**

**Given** `_bmad-output/planning-artifacts/prd.md` contains multiple stale claims corrected in Story 6.2
**When** a revision marker is added
**Then** the marker follows the format: `> **Revision Note (2026-03-04):** [What changed] that makes [specific claim] stale. See Issue #118 and Epic 7 for the architectural evolution path.` (FR-NEW-3)
**And** the original text is preserved (not rewritten) — the marker annotates, not replaces

**Given** `_bmad-output/planning-artifacts/architecture.md` describes the direct implementation architecture
**When** a revision marker is added
**Then** it notes that ADK V1 changed the wrapping viability (Python-side state merging, no more `json_patch` SQL) and references Epic 7 as the evolution path (FR-NEW-3)
**And** the original architecture description is preserved as historical context

**Given** `_bmad-output/project-context.md` contains stale schema claims
**When** a revision marker is added
**Then** it follows the same consistent format and references Issue #118 (FR-NEW-3)

**Given** `docs/adr/ADR-000-strategy-decorator-architecture.md` rejects wrapping based on V0-era `json_patch` reasoning
**When** a revision note is added to the "Why not wrap DatabaseSessionService" section
**Then** it acknowledges that ADK V1 changed this — `DatabaseSessionService` now merges state in Python (`dict | delta`), not SQL (FR-NEW-3)
**And** it references Epic 7 as the path to re-evaluate wrapping
**And** the original rejection reasoning is preserved (it was correct for V0)

**Given** `docs/adr/ADR-004-adk-schema-compatibility.md` describes the "own schema" strategy
**When** a revision note is added
**Then** it clarifies the schema mirrors ADK V1 structure with encrypted column types, not a truly independent design (FR-NEW-3)
**And** it references Issue #118's finding about table name collision risk

**And** all revision markers use the consistent format: `> **Revision Note (YYYY-MM-DD):** ...`
**And** all markers reference Issue #118 as the source finding
**And** no original content is deleted — markers annotate history, they don't rewrite it

---

## Epic 7: Architecture Migration — DatabaseSessionService Wrapper

Encrypted sessions work with any database ADK supports — SQLite, PostgreSQL, MySQL, MariaDB — with zero additional configuration beyond what ADK already provides. The ~800-line raw aiosqlite implementation is replaced by a thin wrapper around DatabaseSessionService via SQLAlchemy TypeDecorator, focused solely on encryption — the project's actual value-add. The encryption core (EncryptionBackend protocol, FernetBackend, serialization envelope) is untouched. aiosqlite is removed as a direct dependency.

### Story 7.1: TypeDecorator Wrapping Spike

As a **library maintainer**,
I want **a validated proof-of-concept that wraps DatabaseSessionService via SQLAlchemy TypeDecorator for transparent encrypt/decrypt at the ORM boundary**,
So that **I have evidence-based confidence (or a clear no-go) before committing to the architecture migration**.

**Acceptance Criteria:**

**Given** ADK V1's `DatabaseSessionService` merges state in Python (`dict | delta`), not via SQL `json_patch`
**When** a prototype `TypeDecorator` is implemented that encrypts on `process_bind_param` and decrypts on `process_result_value`
**Then** a round-trip test demonstrates: create session with state → retrieve session → state matches original (FR-NEW-4)
**And** the prototype uses the existing `FernetBackend` and serialization envelope for encryption

**Given** the prototype wraps `DatabaseSessionService`
**When** the same inputs are provided to both the wrapped and unwrapped service
**Then** the resulting `Session` and `Event` objects are structurally identical (same fields, same types, same values) — conformance verified

**Given** the current schema reserves a `version INTEGER DEFAULT 1` column on `sessions`, `app_states`, and `user_states` (Story 1.2)
**When** wrapping `DatabaseSessionService` inherits ADK's schema
**Then** the spike assesses whether the `version` column reservation is preserved, lost, or can be added via schema extension
**And** the impact on Story 4.4 (optimistic concurrency / key rotation) is documented

**Given** existing users have SQLite databases with encrypted data under the current raw-aiosqlite schema
**When** they upgrade to the wrapped version
**Then** the spike assesses the migration path: is data migration required? Can the wrapped service read existing databases? Is a migration utility needed?
**And** the migration assessment is documented with a recommendation

**Given** the prototype exists
**When** test feasibility is assessed
**Then** the spike documents whether the new architecture can be tested cleanly — conformance tests, round-trip tests, and runner integration tests are all feasible
**And** any testing challenges or limitations are documented

**Given** all assessments are complete
**When** the spike produces a findings document
**Then** it contains a clear **go/no-go recommendation** with evidence
**And** the findings document is saved to `_bmad-output/implementation-artifacts/`
**And** if no-go, the document explains what blocked the approach and proposes alternatives

**This story gates all subsequent Epic 7 stories. Stories 7.2-7.6 proceed only on a "go" decision.**

### Story 7.2: ADR — Architecture Migration Decision

As a **future contributor reading the ADR trail**,
I want **a formal ADR documenting the decision to migrate from direct BaseSessionService implementation to DatabaseSessionService wrapping**,
So that **I understand why the architecture changed, what evidence supported the decision, and what trade-offs were accepted**.

**Acceptance Criteria:**

**Given** the spike (Story 7.1) produced a go decision with evidence
**When** a new ADR is created (e.g., `docs/adr/ADR-007-architecture-migration.md`)
**Then** it follows the existing ADR format established by ADR-000 through ADR-006
**And** the Context section explains: ADR-000's original rejection was based on V0-era `json_patch` SQL operations; ADK V1 changed state merging to Python-side `dict | delta`, making wrapping viable (FR-NEW-6)
**And** the Decision section states: wrap `DatabaseSessionService` via SQLAlchemy `TypeDecorator` for transparent encrypt/decrypt at the ORM boundary
**And** the Rationale section documents: multi-database support for free, connection pooling for free, row-level locking for free, schema migration for free, focus on encryption as sole value-add
**And** the Consequences section documents: aiosqlite removed as direct dependency, Epic 4 Stories 4.1-4.3 superseded, existing user migration path required
**And** the ADR references the spike findings document and Issue #118 as evidence
**And** the ADR status is "Accepted"

### Story 7.3: Rewrite EncryptedSessionService as DatabaseSessionService Wrapper

As a **developer using the library**,
I want **EncryptedSessionService to wrap DatabaseSessionService via TypeDecorator**,
So that **I get encrypted sessions with any database ADK supports — SQLite, PostgreSQL, MySQL, MariaDB — without the library reimplementing persistence logic**.

**Acceptance Criteria:**

**Given** `EncryptedSessionService` currently implements ~800 lines of raw aiosqlite SQL
**When** it is rewritten to wrap `DatabaseSessionService`
**Then** a SQLAlchemy `TypeDecorator` handles transparent encrypt/decrypt at the ORM boundary (FR-NEW-4)
**And** `EncryptedSessionService` still extends `BaseSessionService` (NFR20 — Runner compatibility preserved)
**And** the public API signatures remain unchanged — `create_session`, `get_session`, `list_sessions`, `delete_session` (FR29)

**Given** the rewrite uses `DatabaseSessionService` for persistence
**When** the library is configured with a SQLite database URL
**Then** encrypted sessions work identically to the previous implementation
**And** when configured with a PostgreSQL, MySQL, or MariaDB URL, encrypted sessions work via DatabaseSessionService's dialect handling (FR-NEW-5, FR49)

**Given** `aiosqlite` is currently a direct dependency in `pyproject.toml`
**When** the rewrite is complete
**Then** a grep of `src/adk_secure_sessions/` confirms no module imports `aiosqlite` directly
**And** `aiosqlite` is removed from the direct dependency list in `pyproject.toml`
**And** the direct runtime dependency count remains <= 5 (NFR23)

**Given** the encryption core (EncryptionBackend protocol, FernetBackend, serialization envelope)
**When** the rewrite is complete
**Then** `protocols.py`, `backends/fernet.py`, `serialization.py`, and `exceptions.py` are untouched — zero changes to the encryption layer
**And** the `TypeDecorator` uses the existing `encrypt_session`/`decrypt_session` functions from `serialization.py`

**And** all session state and event data is encrypted at rest — no plaintext data paths exist (NFR5)
**And** encryption keys never appear in log output, error messages, or exception tracebacks (NFR6)
**And** the rewritten service handles the existing user migration path as determined by the spike (Story 7.1)

### Story 7.4: Test Migration & Conformance Verification

As a **library maintainer**,
I want **a test suite that verifies the wrapped EncryptedSessionService is behaviorally equivalent to the previous implementation and to an unencrypted DatabaseSessionService**,
So that **I have confidence the architecture migration introduced no regressions**.

**Acceptance Criteria:**

**Given** the rewritten `EncryptedSessionService` wraps `DatabaseSessionService`
**When** conformance tests are run
**Then** for identical inputs, the wrapped service produces the same `Session` and `Event` objects (same fields, types, values) as a raw `DatabaseSessionService` — except that persisted data is encrypted at rest
**And** conformance tests cover: create, get, list, delete, and append_event operations

**Given** the `TypeDecorator` encrypts on write and decrypts on read
**When** round-trip encryption tests are run
**Then** data verified at each boundary: plaintext → TypeDecorator encrypts → DB stores ciphertext → TypeDecorator decrypts → plaintext matches original
**And** wrong-key decryption raises `DecryptionError`, never returns garbage data (NFR7)
**And** empty state (`{}`) and empty event lists (`[]`) round-trip without error (NFR15)

**Given** Story 1.6a verified ADK Runner accepts `EncryptedSessionService`
**When** the runner integration test is re-run against the rewritten service
**Then** the test passes — an ADK Runner can execute a complete agent turn using the wrapped service (NFR20)

**Given** a database containing unencrypted `DatabaseSessionService` data (no encryption)
**When** the wrapped `EncryptedSessionService` attempts to read that data
**Then** it detects the unencrypted data and raises a clear error (not silent corruption or garbage data)
**And** the error message indicates the data was not encrypted, not that decryption failed with wrong key

**And** concurrent async session operations on the same database do not corrupt data (NFR25)
**And** all async fixtures properly close database connections on teardown (NFR19)
**And** code coverage remains >= 90% (NFR18)
**And** the test suite passes with zero warnings (NFR16)

### Story 7.5: Documentation & MkDocs Site Updates

As a **developer reading the docs site after the architecture migration**,
I want **documentation that accurately reflects the new wrapped architecture**,
So that **I understand how encryption integrates with DatabaseSessionService and how to configure multi-database support**.

**Acceptance Criteria:**

**Given** the architecture has migrated from raw aiosqlite to DatabaseSessionService wrapping
**When** the getting-started guide is updated
**Then** it shows configuration for SQLite (default) and mentions PostgreSQL/MySQL/MariaDB as supported via DatabaseSessionService
**And** the integration swap example reflects the new architecture

**Given** `docs/project-overview.md` describes the library's architecture
**When** it is updated
**Then** it accurately describes the TypeDecorator wrapping approach
**And** the dependency table reflects the removal of aiosqlite and the use of SQLAlchemy via DatabaseSessionService

**Given** `docs/ARCHITECTURE.md` describes the system design
**When** it is updated
**Then** it reflects the new wrapper architecture with the TypeDecorator at the ORM boundary
**And** it references ADR-007 (from Story 7.2) as the decision record

**Given** the docs site has an index page and feature bullets
**When** they are updated
**Then** multi-database support is listed as a feature
**And** the description matches the accurate language established in Epic 6

**And** all new or modified documentation pages pass the docvet pre-commit hook
**And** no code logic is changed — only documentation

### Story 7.6: Revise Epic 4 Scope & Roadmap

As a **contributor reading the backlog or roadmap**,
I want **Epic 4's superseded stories formally closed and the roadmap updated to reflect that PostgreSQL comes for free**,
So that **I don't waste time planning or implementing stories that have been superseded by Epic 7**.

**Acceptance Criteria:**

**Given** Epic 4 Stories 4.1 (Persistence Protocol), 4.2 (Encryption Coordinator), and 4.3 (PostgreSQL Backend) are superseded by Epic 7
**When** `_bmad-output/planning-artifacts/epics.md` is updated
**Then** Stories 4.1, 4.2, and 4.3 have `[SUPERSEDED by Epic 7]` markers (already added in Step 2)
**And** Epic 4's goal statement is revised to reflect reduced scope: key rotation, backend docs, ops guide, Python version tracking
**And** Epic 4's FR coverage is updated: FR49 remapped to Epic 7

**Given** `docs/ROADMAP.md` describes Phase 3 capabilities
**When** it is updated
**Then** PostgreSQL support is listed as delivered by Epic 7 (not Epic 4)
**And** the Phase 3 scope accurately reflects: AES-256-GCM (Epic 3) + architecture migration with multi-DB (Epic 7) + key rotation and docs (Epic 4 remainder)

**And** any sprint plans or status documents referencing Epic 4 Stories 4.1-4.3 are updated or annotated
