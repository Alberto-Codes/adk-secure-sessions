---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-02-28'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/prd-validation-report.md'
  - '_bmad-output/project-context.md'
  - 'docs/ARCHITECTURE.md'
  - 'docs/ROADMAP.md'
  - 'docs/project-overview.md'
  - 'docs/source-tree-analysis.md'
  - 'docs/development-guide.md'
  - 'docs/changelog.md'
  - 'docs/adr/index.md'
  - 'docs/adr/ADR-000-strategy-decorator-architecture.md'
  - 'docs/adr/ADR-001-protocol-based-interfaces.md'
  - 'docs/adr/ADR-002-async-first.md'
  - 'docs/adr/ADR-003-field-level-encryption.md'
  - 'docs/adr/ADR-004-adk-schema-compatibility.md'
  - 'docs/adr/ADR-005-exception-hierarchy.md'
  - 'docs/reference/index.md'
  - 'docs/contributing/docstring-templates.md'
  - '_bmad-output/implementation-artifacts/tech-spec-release-please-cleanup.md'
workflowType: 'architecture'
project_name: 'adk-secure-sessions'
user_name: 'Alberto-Codes'
date: '2026-02-28'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Relationship to Existing Architecture

This architecture document extends the existing `docs/ARCHITECTURE.md` and ADR-000 through ADR-005. It does not re-decide settled architecture. It covers: (a) Phase 2 packaging/distribution decisions, (b) Phase 3-4 design direction, and (c) open decisions that affect the v0.1.0 public contract.

### Requirements Overview

**Functional Requirements:**
56 FRs across 9 capability areas. 41 are tagged MVP (Phase 2: Ship), 6 are Phase 3 (Expand), and 4 are Phase 4 (Enterprise). The MVP FRs split into two categories: (a) already-implemented core engine (FR1-FR26 — encryption, persistence, config, extensibility, error handling) and (b) go-to-market work (FR27-FR45, FR56 — PyPI, docs, release pipeline). Phase 3-4 FRs introduce new architectural surface: AES-256-GCM backend (FR46), key rotation (FR48), PostgreSQL persistence (FR49), KMS backends (FR52-54), and audit logging (FR55).

**Non-Functional Requirements:**
28 NFRs across 6 categories. The architecture-shaping NFRs are: encryption overhead <20% (NFR1), asyncio.to_thread for all crypto (NFR2), async I/O exclusively (NFR3), no plaintext data paths (NFR5), wrong-key always raises DecryptionError (NFR7), ≤5 runtime dependencies (NFR23), 50-coroutine concurrent write safety (NFR25), and 5-minute integration time (NFR28). Phase 3 adds PostgreSQL concurrency (NFR26) and optimistic concurrency (NFR27).

**Scale & Complexity:**

- Primary domain: Security library / backend infrastructure (Python)
- Complexity level: High
- Existing architectural components: 6 modules (protocols, exceptions, serialization, backends/fernet, services/encrypted_session, __init__)
- Phase 3-4 new components: ~4-6 (AES-GCM backend, PostgreSQL persistence, key rotation utilities, KMS backends, audit logging)

### Technical Constraints & Dependencies

| Constraint | Source | Status | Impact |
|-----------|--------|--------|--------|
| Python >=3.12,<3.13 | pyproject.toml | Satisfied | Single-version band; 3.13+ deferred to Phase 3 |
| google-adk >=1.22.0 | ADR-004 | Satisfied | BaseSessionService interface stability; CI matrix tests min + latest |
| cryptography >=44.0.0 | pyproject.toml | Satisfied | All crypto delegated here; no custom primitives (permanent constraint) |
| aiosqlite >=0.19.0 | pyproject.toml | Satisfied | Async SQLite; raw parametrized SQL only |
| ≤5 runtime deps | NFR23 | Satisfied (3 currently) | Constrains new dependencies; optional extras for backends |
| Envelope wire protocol | ADR-000, ADR-004 | Satisfied | [version][backend_id][ciphertext] is stable public contract |
| No ABC/abstractmethod | ADR-001 | Satisfied | All contracts via PEP 544 @runtime_checkable Protocol |
| Async-first only | ADR-002 | Satisfied | No sync public APIs; crypto wrapped in asyncio.to_thread() |
| Field-level encryption | ADR-003 | Satisfied | Metadata queryable, state/events encrypted; not full-DB |
| Own schema | ADR-004 | Satisfied | Independent of ADK internal tables; own migration path |

### Cross-Cutting Concerns

| # | Concern | Phase Relevance | Status |
|---|---------|----------------|--------|
| 1 | **Encryption boundary integrity** — Every data path to/from persistence goes through encrypt/decrypt. An unencrypted path is a security defect. | All phases | Satisfied (Phase 1). New data paths in Phase 3-4 must preserve this invariant. |
| 2 | **Envelope protocol stability** — New backends register backend IDs, produce/consume standard envelope. v1 format (`[version][backend_id][ciphertext]`) is stable. Supports 255 backends — sufficient for foreseeable future. | Phase 3-4 | Satisfied (Phase 1 format). New backends extend, not change. |
| 3 | **Async enforcement** — All public APIs async. CPU-bound ops use asyncio.to_thread(). Network-bound KMS backends are naturally async. | All phases | Satisfied (Phase 1). Phase 3-4 backends inherit the pattern. |
| 4 | **ADK interface tracking** — BaseSessionService signatures, Session/Event models, state prefix utilities. CI matrix tests min + latest. `_session_util.extract_state_delta` is an internal utility imported directly — if ADK removes it, reimplementation is ~20 LOC using public prefix constants (`State.APP_PREFIX`, `State.USER_PREFIX`, `State.TEMP_PREFIX`). | All phases | Satisfied (Phase 1 CI matrix). |
| 5 | **Error handling discipline** — Typed exceptions, no key leakage, envelope metadata in error context. | All phases | Satisfied (Phase 1). Phase 3-4 components must follow the same patterns. |
| 6 | **Dependency ceiling** — ≤5 runtime deps. PostgreSQL, KMS SDKs, Vault client cannot all be required. Optional extras (`[postgres]`, `[aws]`, `[gcp]`, `[vault]`) mandatory for new backends. | Phase 3-4 | Phase 3 prerequisite — extras skeleton ships in Phase 2. |
| 7 | **Testing strategy** — Serialization layer is the integration seam. Backend tests verify encrypt/decrypt round-trips. Persistence tests verify read/write with any encrypted blob. Integration tests verify full stack with representative combinations (linear matrix, not quadratic). | All phases | Satisfied (Phase 1 patterns). Phase 3 extends to new backends/persistence. |

### Forward-Looking Architectural Decisions

#### Decide Now (affects v0.1.0 schema/API)

1. **Concurrency model — schema reservation.** NFR25 (50 coroutines, SQLite), NFR26 (10 writers, PostgreSQL), NFR27 (optimistic concurrency). Adding a version column to the schema after v0.1.0 ships forces a migration on every early adopter. Decision: either reserve the column in v0.1.0 schema or explicitly accept the migration cost in Phase 3. SQLite is fundamentally single-writer (serializes via aiosqlite connection), so the column is inert for Phase 2 — but reserving it avoids a breaking migration.

2. **Exception hierarchy evolution.** FR15 introduces `ConfigurationError` and `DatabaseConnectionError` — neither exists in the current hierarchy (ADR-005: SecureSessionError, EncryptionError, DecryptionError, SerializationError). Decision: add these before v0.1.0 PyPI publish, or defer and add in a minor release? Adding exceptions is non-breaking (new symbols), but their absence means FR15's startup validation currently raises generic errors.

#### Design Direction (Phase 3+ intent, no current commitments)

3. **Service decomposition.** `EncryptedSessionService` is 740 LOC handling connection lifecycle, schema init, CRUD, event append with state delta logic, encryption delegation, and envelope dispatch. Phase 3 adds PostgreSQL, key rotation, and multi-backend — this file would double without decomposition. Design direction: decompose into persistence layer (SQLite/Postgres) + encryption coordinator (backend selection, key provider, envelope) + service orchestrator (ADK interface). The persistence abstraction is a consequence of this decomposition, not a standalone decision. Recommend a lightweight persistence protocol (PEP 544, same pattern as EncryptionBackend) rather than SQLAlchemy ORM migration — resolving the contradiction between PRD FR #20 and project-context.md's "Never use SQLAlchemy ORM" anti-pattern. Needs its own ADR when Phase 3 begins.

> **Revision Note (2026-03-04):** ADK V1 changed state merging from SQL-side `json_patch` to Python-side `dict | delta`, removing the SQL interception barrier that made `DatabaseSessionService` wrapping unviable. This makes a `TypeDecorator`-based wrapping approach viable — potentially collapsing the persistence extraction (Epic 4 Stories 4.1-4.3) into the architecture migration (Epic 7). The decomposition direction described above was designed for ADK V0's constraints; Epic 7 explores whether wrapping `DatabaseSessionService` achieves the same goals more simply. See Issue #118 and Epic 7 for the architectural evolution path.
>
> **Revision Note (2026-03-07):** Story 3.3 party-mode consensus confirmed that the "encryption coordinator" component of this decomposition is not needed for multi-backend dispatch alone. Dispatch is implemented as a `dict[int, Callable]` inside `EncryptedJSON` TypeDecorator. The coordinator class remains a deferred concept for Story 4.4 (key rotation), which requires the full coordination surface (key provider, migration strategy, backend registry with key associations). See Story 3.3 change log for consensus rationale.

4. **Key rotation design surface.** More complex than envelope dispatch alone. Requires: (a) key provider abstraction — service must know which keys to try during decryption, (b) migration strategy — re-encrypt on read, background task, or natural TTL expiration, (c) backend registry mapping backend IDs to key+backend pairs. The envelope protocol was designed for this; the service layer needs the supporting infrastructure.

> **Revision Note (2026-03-07, Story 3.3 party-mode consensus):** Multi-backend *decrypt dispatch* (item c above, backend ID → decrypt function routing) is implemented in Story 3.3 as a `dict[int, Callable]` inside `EncryptedJSON` TypeDecorator — not as a separate `EncryptionCoordinator` class. The coordinator concept from design direction #3 is deferred to Story 4.4 (key rotation), which will need the full key provider abstraction (item a) and migration strategy (item b). The dict-in-TypeDecorator approach is sufficient for dispatch alone; the coordinator adds value only when key rotation introduces key provider and migration responsibilities. Registration is construction-time only; FR19 "dynamic" means constructor-injected, not post-init mutable.

5. **API surface growth strategy.** Phase 3 adds AES-GCM backend, key rotation utilities, PostgreSQL config, potentially new exceptions. Decision: new symbols in top-level `__init__.py` (flat namespace, simple imports) or submodule imports (`from adk_secure_sessions.backends import AesGcmBackend`)? Affects the public API stability promise documented in the PRD's versioning section.

6. **Backend ecosystem architecture.** Third-party backends need: (a) backend ID registry in docs to avoid collisions, (b) optional entry-point discovery (`[project.entry-points]` in pyproject.toml) for Phase 3+, (c) decision on first-party vs. third-party packaging for KMS backends. Current constructor API accepting a backend instance is sufficient through Phase 2.

## Technology Foundation

### Primary Technology Domain

Python security library / backend infrastructure — brownfield project with Phase 1 complete.

### Established Foundation (Not a Starter Template)

This is a brownfield project. The technology stack, project structure, and development toolchain were established during Phase 1 implementation and are documented in `_bmad-output/project-context.md` (91 rules). No starter template evaluation is applicable. This section documents the existing foundation as the architectural baseline.

### Technology Decisions Already Made

**Language & Runtime:**

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | >=3.12,<3.13 | Single-version band; 3.13+ deferred to Phase 3 |
| uv | Latest | Package manager, build backend (`uv_build`), task runner |
| src/ layout | — | `src/adk_secure_sessions/` — standard Python package structure |

**Core Dependencies (Runtime):**

| Dependency | Version | Purpose |
|-----------|---------|---------|
| google-adk | >=1.22.0 | Upstream ADK; BaseSessionService, Session, Event models |
| cryptography | >=44.0.0 | Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) |
| aiosqlite | >=0.19.0 | Async SQLite driver; raw parametrized SQL |

**Development Toolchain:**

| Tool | Version | Purpose |
|------|---------|---------|
| ruff | >=0.13.0 | Linter + formatter (line-length 88, Google docstring convention). Includes `S` prefix rules (bandit-equivalent security checks). |
| ty | >=0.0.1a20 | Type checker (src/ only) |
| pytest | >=8.4.2 | Test framework (asyncio_mode auto) |
| pytest-mock | >=3.15.1 | Mock fixtures (mocker); replaces unittest.mock |
| pytest-asyncio | >=1.2.0 | Async test support |
| pytest-cov | — | Coverage reporting; 90% threshold enforced by CI |
| interrogate | >=1.7.0 | 95% docstring coverage enforcement |
| pip-audit | — | Vulnerability scanning (NFR8: zero unpatched CVEs at release) |
| griffe | — | Docstring parser (used by mkdocstrings + quality pipeline via `docstring_griffe_check.py`) |
| MkDocs Material | >=9.7.1 | Documentation site |
| mkdocstrings-python | >=2.0.1 | Auto-generated API reference |
| gen_ref_pages.py | — | Script that auto-generates API reference pages. Must use dynamic module discovery (walk `src/` tree), not hardcoded paths, for Phase 3 extensibility. |
| pre-commit | — | 7 hooks: yamllint, actionlint, ruff-check, ruff-format, ty, pytest, docvet |

**CI/CD Pipeline:**

| Component | Configuration |
|-----------|--------------|
| Test workflow | Python 3.12 x ADK matrix (1.22.0, latest); lint → format → type check → tests (90% coverage) |
| Docs workflow | MkDocs build verification on docs/ and src/ changes |
| Release workflow | release-please on develop; conventional commits drive changelog |
| Publish workflow | Phase 2: triggered on release tags. **Must run its own test suite independently** — does not trust branch protection. For a security library, the publish pipeline must be independently verified. Cost: ~2 minutes of CI time. Risk of skipping: shipping untested encryption code to PyPI. |
| Quality pipeline | 8-step local script: ruff, format, docstrings (freshness, enrichment, coverage), griffe, ty, pytest |
| CI/local alignment gap | interrogate (95% docstring coverage) runs locally but not in CI. **Recommendation: add interrogate to CI** — 5-second check that eliminates the gap between "CI passed" and "quality gate passed." |

**Security Scanning Posture:**

| Tier | Responsibility | Tools | Status |
|------|---------------|-------|--------|
| Tier 1 (our CI) | Project maintainers | pip-audit (dependency CVEs), ruff `S` rules (bandit-equivalent), SonarQube (OWASP categories) | pip-audit: add to CI. Ruff S rules: verify enabled in ruff config. SonarQube: manual scans on develop. |
| Tier 2 (evaluator) | Downstream security teams | Internal SAST (Snyk, Semgrep, Checkmarx) | We make the codebase SAST-friendly (see anti-patterns below). |

**Permanent Security Anti-Patterns (SAST Friendliness):**

The following are permanently prohibited in all production code. These constraints exist both for security and to ensure clean SAST scans for downstream evaluators (Diane's journey):

- No `eval()` or `exec()`
- No `pickle` (serialization uses `json` only)
- No `subprocess` with `shell=True`
- No dynamic SQL construction (parametrized queries only)
- No hardcoded secrets or keys
- No custom cryptographic primitives (delegate to `cryptography` library)

**Code Organization Patterns:**

| Pattern | Implementation |
|---------|---------------|
| Interface contracts | PEP 544 `@runtime_checkable` Protocol (never ABC) |
| Public API surface | `__init__.py` with `__all__` (13 symbols, alphabetically sorted) |
| Async model | All public APIs `async def`; CPU-bound ops via `asyncio.to_thread()` |
| Imports | Absolute only (`from adk_secure_sessions.x import Y`) |
| Docstrings | Google-style; module docstrings use `::` directive, function/class use fenced code blocks |
| Error handling | Exception msg in `msg` variable; `from exc` chaining; no sensitive data in messages |
| Database access | Raw parametrized SQL via aiosqlite; no ORM |
| Test structure | `test_<module>.py` mirroring source; `Test<Feature>` classes; `mocker` fixture |
| Session state contract | `dict[str, Any]`, JSON-serializable. Pydantic models must be converted to dicts before storage. Library does not serialize/deserialize Pydantic models directly. |

### Known Compatibility Edge Cases

**`from __future__ import annotations` + `@runtime_checkable` Protocol:** Every module uses `from __future__ import annotations` (required for PEP 604 unions). This makes all annotations strings at runtime. Combined with `@runtime_checkable` Protocol, this can cause subtle `isinstance()` failures if annotation resolution fails. Python 3.12 handles this correctly and the behavior is verified by unit tests across the ADK version matrix. Diagnostic note: if a downstream user reports a false negative `isinstance(obj, EncryptionBackend)` check, the first investigation should be `__future__ annotations` interaction in their environment.

**Session state serialization boundary:** ADK's `Session` and `Event` are Pydantic models. Downstream users may put Pydantic models in session state. The library serializes state via `json.dumps`/`json.loads` as plain `dict[str, Any]`. Pydantic models must be converted to dicts (e.g., `model.model_dump()`) before storage. The library does not handle Pydantic serialization — this is the user's responsibility. Document in Getting Started guide.

### Contributor Setup Tiers

| Tier | Commands | Who Needs It |
|------|----------|-------------|
| **Minimum** | `uv sync --dev && uv run pytest` | Backend plugin authors (Tomás's journey), quick contributors |
| **Full** | Above + `pre-commit install` + `uv run mkdocs serve` + SonarQube (optional) | Core maintainers, regular contributors |

Backend plugin authors need only the minimum setup — they develop against the Protocol definition and test suite, not the full docs/quality pipeline.

### Phase 2 Technology Additions

Phase 2 (Ship) does not add runtime dependencies. It adds packaging and distribution configuration:

| Addition | Purpose |
|---------|---------|
| `py.typed` marker | PEP 561 — IDE autocomplete for downstream users |
| `[project.optional-dependencies]` skeleton | `[postgres]`, `[dev]` extras — empty but ready for Phase 3 |
| PyPI publish workflow | GitHub Actions triggered on release tags; runs own test suite |
| TestPyPI pre-release | Validation before production publish |
| SECURITY.md | Responsible disclosure policy |
| NFR1 benchmark test | Overhead <20% verified via `time.perf_counter()` (no new dep; pytest-benchmark deferred to Phase 3) |

### Phase 3 Anticipated Technology Additions

| Addition | Dependency Impact | Extras Group | Notes |
|---------|-------------------|-------------|-------|
| AES-256-GCM backend | cryptography (already present) | None | Same dep, different algorithm |
| PostgreSQL persistence | asyncpg or psycopg3 (TBD) | `[postgres]` | See driver decision criteria below |
| Key rotation utilities | No new deps | None | — |
| Performance benchmarks | pytest-benchmark (dev only) | None | Formal benchmarks replacing Phase 2 perf_counter test |

**PostgreSQL driver decision criteria (deferred to Phase 3 research):**

| Criterion | asyncpg | psycopg3 (async) |
|-----------|---------|-------------------|
| Parameterization style | `$1, $2` (differs from aiosqlite `?`) | `%s` (closer to aiosqlite `?` but still different) |
| Connection pool | Own API (`asyncpg.create_pool()`) | Standard or external (e.g., connpool) |
| Async model | Pure async, native | Sync + async wrapper |
| Performance | Fastest Python PG driver | Slightly slower, more compatible |
| SQLAlchemy integration | Not compatible with SA async engine | Compatible with SA async engine |
| Persistence protocol impact | Requires query parameterization abstraction | Simpler abstraction, closer to aiosqlite patterns |

Decision deferred. Both are viable. Selection depends on the persistence protocol design (see Forward-Looking Decision #3 in Project Context Analysis).

### Phase 4 Anticipated Technology Additions

| Addition | Dependency Impact | Extras Group | Notes |
|---------|-------------------|-------------|-------|
| AWS KMS backend | boto3 (~100MB installed) | `[aws]` | Heavy SDK; document install size expectation |
| GCP Cloud KMS backend | google-cloud-kms + google-auth chain | `[gcp]` | Moderate footprint |
| HashiCorp Vault backend | hvac (lightweight) | `[vault]` | Small dependency |
| FIPS 140-2 support | No new deps | None | Deployment configuration guide for OpenSSL FIPS module, not a code change |
| Audit logging | No new deps (stdlib logging) | None | — |

### Extras Group Strategy

**No `[all]` extras group.** Deliberate decision: security libraries should minimize installed surface by default. Installing `adk-secure-sessions[aws]` pulls ~100MB of boto3; `[all]` would pull every KMS SDK into a single install. Enterprise teams evaluating the library should install only the extras they need. Each extras group is documented with its dependency footprint.

Extras groups: `[postgres]`, `[aws]`, `[gcp]`, `[vault]`, `[dev]`. No `[all]`.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**

1. **Schema Reservation for Optimistic Concurrency** — Reserve `version INTEGER DEFAULT 1` on `sessions`, `app_states`, and `user_states` tables in v0.1.0 schema. Events table excluded (append-only). Column inert in Phase 2, activated in Phase 3.

**Important Decisions (Shape Architecture):**

2. **Exception Hierarchy Evolution** — Add `ConfigurationError` as a `SecureSessionError` subclass before v0.1.0 for startup validation (bad key, invalid backend, misconfiguration). Defer `DatabaseConnectionError` to Phase 3 when the persistence protocol decomposition introduces a proper persistence error contract.

**Deferred Decisions (Phase 3+):**

3. Service decomposition strategy (persistence protocol, encryption coordinator, service orchestrator)
4. Key rotation design surface (key provider abstraction, migration strategy, backend-ID-to-key mapping)
5. API surface growth strategy (flat namespace vs. submodule imports)
6. Backend ecosystem architecture (backend ID registry, entry-point discovery, first-party vs. third-party packaging)

### Data Architecture

#### Decision 1: Schema Reservation for Optimistic Concurrency

- **Decision:** Option A (extended) — Reserve `version INTEGER DEFAULT 1` on `sessions`, `app_states`, and `user_states` tables
- **Rationale:** Adding a version column after v0.1.0 ships forces a migration on every early adopter. Reserving it in the initial schema avoids a breaking migration while costing nothing (column is inert in Phase 2). Extended to all state tables because concurrent writes can affect `app_states` and `user_states`, not just `sessions`. Events table excluded — it is append-only and does not require optimistic concurrency.
- **Affects:** Database schema (`_init_db`), Phase 3 optimistic concurrency implementation (NFR25, NFR26, NFR27)
- **Phase:** Reserved in Phase 2, activated in Phase 3
- **Decided by:** Party Mode consensus (Winston, Murat, John, Amelia — unanimous)

### Error Handling

#### Decision 2: Exception Hierarchy Evolution

- **Decision:** Option B — Add `ConfigurationError` only; defer `DatabaseConnectionError` to Phase 3
- **Rationale:** `ConfigurationError` meets ADR-005's bar: callers have a concrete need to catch misconfiguration separately from runtime encryption/decryption failures in `try/except` blocks. Covers: bad key format, empty key, invalid `backend_id`, missing backend. `DatabaseConnectionError` is deferred because (a) SQLite connection failures are extremely rare, (b) `aiosqlite` already raises well-typed `sqlite3.OperationalError`, (c) the exception belongs in the Phase 3 persistence abstraction layer, not bolted onto the current monolithic service. Adding exceptions is non-breaking, so deferral cost is zero.
- **Affects:** `exceptions.py`, `services/encrypted_session.py` constructor validation, `__init__.py` public API surface
- **Phase:** Implemented in Phase 2 before v0.1.0 PyPI publish
- **Decided by:** Party Mode consensus (Winston, Murat, Amelia, John — unanimous)

### Deferred Design Direction (Phase 3+)

The following are documented architectural intents, not active decisions. Each will require its own ADR when Phase 3 begins.

#### 3. Service Decomposition

`EncryptedSessionService` (740 LOC) handles connection lifecycle, schema init, CRUD, event append with state delta logic, encryption delegation, and envelope dispatch. Phase 3 adds PostgreSQL, key rotation, and multi-backend — the file would double without decomposition.

**Intent:** Decompose into three layers:
- **Persistence layer** — SQLite/PostgreSQL implementations behind a PEP 544 persistence protocol (not SQLAlchemy ORM, resolving the contradiction between PRD FR20 and project-context.md)
- **Encryption coordinator** — Backend selection, key provider, envelope dispatch
- **Service orchestrator** — ADK `BaseSessionService` interface, delegates to persistence + encryption

**Trigger:** When Phase 3 work begins on PostgreSQL persistence or key rotation.

#### 4. Key Rotation Design Surface

More complex than envelope dispatch alone. Requires:
- **Key provider abstraction** — Service must know which keys to try during decryption (current key + retired keys)
- **Migration strategy** — Re-encrypt on read, background task, or natural TTL expiration
- **Backend registry** — Mapping backend IDs to key+backend pairs for multi-backend scenarios

The envelope protocol's `[version][backend_id][ciphertext]` format was designed to support this; the service layer needs the infrastructure.

**Trigger:** When Phase 3 key rotation work begins (FR48).

#### 5. API Surface Growth Strategy

Phase 3 adds AES-GCM backend, key rotation utilities, PostgreSQL config, and potentially new exceptions. Decision needed: new symbols in top-level `__init__.py` (flat namespace) or submodule imports (`from adk_secure_sessions.backends import AesGcmBackend`)?

**Considerations:** Flat namespace is simpler for users but grows the `__init__.py` `__all__` list. Submodule imports keep the top-level surface stable but require users to know the internal structure. Affects the public API stability promise in the PRD's versioning section.

**Trigger:** When the first Phase 3 public symbol is ready to ship.

#### 6. Backend Ecosystem Architecture

Third-party backends need:
- **Backend ID registry** — Documentation to avoid ID collisions between first-party and community backends
- **Entry-point discovery** — Optional `[project.entry-points]` in pyproject.toml for automatic backend registration
- **Packaging strategy** — Whether KMS backends (AWS, GCP, Vault) ship as separate packages or optional extras

Current constructor API (accepting a backend instance) is sufficient through Phase 2.

**Trigger:** When the first KMS backend implementation begins (Phase 4).

#### 7. AAD (Associated Data) Binding for Encryption Backends

AESGCM natively supports `associated_data` to cryptographically bind ciphertext to authenticated-but-unencrypted metadata. For `adk-secure-sessions`, this would bind encrypted state columns to their session metadata (session_id, app_name, user_id), preventing ciphertext relocation attacks (moving encrypted state between rows).

**Why deferred from Story 3.1:** Adding AAD requires changing the `EncryptionBackend` protocol signature (`encrypt(plaintext, associated_data)`) for all backends, threading session metadata through the encrypt path, and updating the TypeDecorator integration. Blast radius exceeds a single-backend story.

**Candidate for:** Story 3.2 (salt + security hardening) or a dedicated security hardening story in Epic 3.

**Added:** 2026-03-06, party mode consensus during Story 3.1 creation.

#### 8. AES-GCM-SIV Backend

Available in `cryptography>=46.0.0`. AES-GCM-SIV is nonce-misuse resistant -- it maintains confidentiality even under accidental nonce reuse, unlike standard AES-GCM where nonce reuse catastrophically compromises both confidentiality and authenticity.

**Considerations:** Slightly higher computational overhead than AES-GCM. Same `cryptography` dependency (no new deps). Would be `BACKEND_AES_GCM_SIV = 0x03` in the envelope registry.

**Trigger:** After AES-GCM backend ships and if enterprise users request nonce-misuse resistance.

**Added:** 2026-03-06, party mode consensus during Story 3.1 creation.

### Decision Impact Analysis

**Implementation Sequence:**
1. Add `ConfigurationError` to `exceptions.py` and export from `__init__.py` (Phase 2, pre-publish)
2. Add `version INTEGER DEFAULT 1` column to `sessions`, `app_states`, and `user_states` table schemas in `_init_db` (Phase 2, pre-publish)
3. Add constructor validation in `EncryptedSessionService` raising `ConfigurationError` for bad config (Phase 2, pre-publish)

**Cross-Component Dependencies:**
- Decision 1 (schema reservation) is independent — pure schema change, no behavior change in Phase 2
- Decision 2 (ConfigurationError) affects exceptions.py → services/encrypted_session.py → __init__.py (linear dependency chain)
- Deferred decisions 3-6 are interconnected — service decomposition (#3) shapes where key rotation (#4), API growth (#5), and backend ecosystem (#6) land architecturally

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 9 categories where AI agents could make incompatible choices, with 9 additional enhancements from collaborative review.

**Reference Implementation Principle:** Each pattern category points to an existing canonical file. Before creating a new module, read the reference implementation first.

### Naming Patterns

**Database Schema Conventions:**

Reference: `services/encrypted_session.py` (`_init_db` method)

| Element | Convention | Example |
|---------|-----------|---------|
| Table names | Plural, snake_case | `sessions`, `events`, `app_states` |
| Column names | snake_case | `session_id`, `created_at`, `backend_id` |
| Primary keys | `id` for surrogate, `<entity>_id` for natural | `session_id` (natural) |
| Timestamps | `created_at`, `updated_at` | UTC, stored as ISO 8601 text |
| Foreign keys | `<referenced_table_singular>_id` | `session_id` in `events` table |
| Indexes | `idx_<table>_<column(s)>` | `idx_sessions_app_name_user_id` |
| Version columns | `version INTEGER DEFAULT 1` | Per Decision 1 |

**SQL Formatting:**

| Element | Convention | Example |
|---------|-----------|---------|
| SQL keywords | UPPERCASE | `SELECT`, `INSERT INTO`, `CREATE TABLE` |
| String format | Triple-quoted, multi-line | `"""SELECT ... FROM ... WHERE ..."""` |
| Parameterization | Always `?` placeholders | `(?, ?, ?)` — never f-strings, never string concatenation |
| Indentation | Aligned for readability | Keywords left-aligned, columns indented |

**Anti-pattern:** `f"SELECT * FROM sessions WHERE id = '{session_id}'"` — SQL injection vulnerability. Always parametrize.

**Code Naming:**

Reference: `.claude/rules/python.md`

All Python naming follows Google Python Style Guide. snake_case functions/variables, PascalCase classes, CAPS_WITH_UNDER constants. No exceptions.

### Structure Patterns

**Module Placement:**

Reference: existing `src/adk_secure_sessions/` tree

| New Component | Location | Naming Pattern |
|--------------|----------|----------------|
| New encryption backend | `backends/<algorithm>.py` | Lowercase algorithm: `aes_gcm.py` |
| New persistence backend | `persistence/<engine>.py` | Lowercase engine: `sqlite.py`, `postgresql.py` |
| New service component | `services/<responsibility>.py` | Lowercase responsibility: `session_orchestrator.py`, `encryption_coordinator.py` |
| Key rotation utilities | `rotation.py` (top-level module) | Single module until complexity demands package |
| Audit logging | `audit.py` (top-level module) | Single module until complexity demands package |

**Rule:** New modules start as single files. Promote to a package (`foo/`) only when internal structure demands >1 file.

**Anti-patterns:**
- No `utils.py` or `helpers.py` grab-bag modules — put functions in the module that uses them
- No `constants.py` grab-bag — constants live in the owning module (backend IDs in their backend module, SQL table names in the persistence module)

### Protocol Extension Patterns

**Envelope Protocol Extension (Encryption Backends):**

Reference: `backends/fernet.py`, `protocols.py`

| Element | Convention | Example |
|---------|-----------|---------|
| Backend ID assignment | Sequential from existing max | Fernet=1, AES-GCM=2, next=3 |
| Backend ID registry | Class constant + documented in `BACKENDS.md` | `BACKEND_ID = 2` |
| Backend class naming | `<Algorithm>Backend` | `AesGcmBackend`, `AwsKmsBackend` |
| Backend module naming | Lowercase algorithm/provider | `aes_gcm.py`, `aws_kms.py` |
| Protocol conformance | Must satisfy `EncryptionBackend` protocol | `isinstance(backend, EncryptionBackend)` verified in unit test |

**Rule:** Never reuse a backend ID. Backend IDs are permanent — even deprecated backends retain their ID.

**Persistence Protocol Extension (Phase 3):**

Reference: Will follow same structural conventions as encryption backend pattern.

| Element | Convention |
|---------|-----------|
| Protocol definition | PEP 544 `@runtime_checkable` Protocol in `protocols.py` |
| Module placement | `persistence/<engine>.py` |
| Required methods | Matches the persistence protocol (CRUD + lifecycle) |
| Conformance test | `isinstance(backend, PersistenceBackend)` in unit test |
| Connection lifecycle | Async context manager (`__aenter__`/`__aexit__`) |

### Configuration Patterns

Reference: `services/encrypted_session.py` constructor

| Pattern | Convention | Example |
|---------|-----------|---------|
| Constructor params | Required params positional-or-keyword, optional keyword-only | `def __init__(self, backend, *, db_path="sessions.db")` |
| No config objects | Flat constructor params through Phase 2 | Introduce config dataclass only if constructor exceeds ~8 params |
| Environment variables | Never read directly | User reads env, passes to constructor |
| Defaults | Sensible for dev, explicit for production | `db_path` defaults; encryption key never defaults |
| Validation | Constructor validates, raises `ConfigurationError` | Per Decision 2 |

**Backend configuration boundary:** The service takes pre-configured backend instances. It never configures backends. Backend-specific config (nonce size, KMS region, key ARN) is the backend constructor's responsibility. This is dependency injection — the service depends on the backend *interface*, not its configuration.

**Anti-pattern:** Adding `backend_config: dict` to the service constructor. Violates separation of concerns.

### Public API Surface Management

Reference: `__init__.py`

| Element | Convention | Example |
|---------|-----------|---------|
| Export location | `__init__.py` with `__all__` | All public symbols explicitly listed |
| `__all__` ordering | Alphabetical | `["AesGcmBackend", "ConfigurationError", ...]` |
| New exception classes | Subclass `SecureSessionError` | `class ConfigurationError(SecureSessionError)` |
| New backend classes | Satisfy `EncryptionBackend` protocol | No base class inheritance required |
| Deprecation | `warnings.warn(DeprecationWarning)` | Never silent removal in minor versions |

**Rule:** Every new public symbol must appear in `__all__`, have a Google-style docstring with Examples section, and have a corresponding unit test for import availability.

### Async Boundary Rules

Reference: `backends/fernet.py`, `services/encrypted_session.py`

| Operation Type | Pattern | Example |
|---------------|---------|---------|
| `cryptography` library calls | Always `asyncio.to_thread()` | `await asyncio.to_thread(fernet.encrypt, data)` |
| `aiosqlite` calls | Already async, no wrapping | `await db.execute(sql, params)` |
| `json.dumps`/`json.loads` | No wrapping (fast, no I/O) | Direct call in async function |
| Future KMS SDK calls | Already async (network I/O) | `await kms_client.encrypt(...)` |
| File system operations | `asyncio.to_thread()` if blocking | `await asyncio.to_thread(Path.exists, path)` |

**Rule:** If unsure whether a third-party call blocks, wrap it in `asyncio.to_thread()`. False wrapping costs microseconds; missed wrapping blocks the event loop.

### Test Patterns

Reference: `tests/unit/test_fernet_backend.py` (backend tests), `tests/unit/test_serialization.py` (round-trip tests)

**New Backend Test Requirements:**

| Concern | Pattern |
|---------|---------|
| Round-trip | Encrypt then decrypt, assert plaintext matches |
| Wrong-key | Decrypt with different key, assert `DecryptionError` |
| Empty input | Encrypt/decrypt empty bytes, empty dict |
| Protocol conformance | `isinstance(backend, EncryptionBackend)` |

**New Persistence Test Requirements:**

| Concern | Pattern |
|---------|---------|
| CRUD round-trip | Create → read → update → delete through encrypt/decrypt |
| Concurrent access | Multiple coroutines writing simultaneously |
| Cleanup | Async generator fixtures: `yield svc; await svc.close()` |

**Encryption Boundary Verification Pattern:**

For any new persistence operation, write a test that:
1. Stores data through the service (normal API)
2. Reads the raw database row directly (bypassing the service, using raw `aiosqlite`)
3. Asserts the raw value is **not** plaintext — proving data went through encryption

This is the gold standard for encryption path verification.

**Multi-Backend Test Parameterization (Phase 3):**

Each backend module exposes a `create_test_backend()` factory function. Integration tests parameterize over all backends:

```python
@pytest.fixture(params=[create_fernet_backend, create_aesgcm_backend])
def backend(request):
    return request.param()
```

One test suite, all backends. Don't duplicate the full test suite per backend.

**Performance Test Pattern:**

| Element | Convention |
|---------|-----------|
| Marker | `@pytest.mark.benchmark` |
| Location | `tests/benchmarks/` |
| Assertion | Relative overhead (`< 1.20x` baseline), not absolute timing |
| Phase 2 | `time.perf_counter()` (no new dependency) |
| Phase 3 | `pytest-benchmark` for formal benchmarks |

**Test Fixture Naming:**

| Pattern | Example |
|---------|---------|
| Descriptive noun | `fernet_backend`, `encrypted_service` |
| Async with cleanup | Async generator: `yield svc; await svc.close()` |
| Integration marker | `@pytest.mark.integration` for tests requiring real DB |

### Enforcement Guidelines

**All AI Agents MUST:**
1. Read the canonical reference file before creating a new module in that category
2. Run `bash scripts/code_quality_check.sh --all --verbose` before marking any task complete
3. Verify new public symbols are in `__all__`, have docstrings, and have import tests
4. Verify new database operations go through encrypt/decrypt with a raw-DB-read test
5. Never add backend configuration to the service constructor — backends arrive pre-configured

**Anti-Patterns:**
- Creating `utils.py`, `helpers.py`, or `constants.py` grab-bag modules
- Adding `# type: ignore` without a specific error code and explanatory comment
- Using `Any` in type hints when a more specific type is known
- Creating abstract base classes (use Protocol instead)
- Reading environment variables, config files, or external state inside library code
- Using f-strings or string concatenation in SQL queries
- Writing absolute-timing performance assertions (use relative overhead)

## Project Structure & Boundaries

### Complete Project Directory Structure

**Current State (Phase 1 complete, Phase 2 in progress):**

```
adk-secure-sessions/
├── pyproject.toml                    # Package config, dependencies, build backend (uv_build)
├── uv.lock                           # Locked dependency graph
├── .python-version                   # 3.12
├── mkdocs.yml                        # Documentation site config
├── sonar-project.properties          # SonarQube scanner config
├── release-please-config.json        # Release automation config
├── .release-please-manifest.json     # Version manifest
├── .pre-commit-config.yaml           # 7 pre-commit hooks
├── .yamllint.yaml                    # YAML lint config
├── .gitignore
├── README.md
├── CHANGELOG.md                      # Auto-generated by release-please
├── CONTRIBUTING.md
├── CLAUDE.md                         # AI agent instructions (auto-generated)
│
├── .claude/rules/                    # AI agent behavioral rules
│   ├── conventions.md                # Project conventions and principles
│   ├── dev-quality-checklist.md      # Quality patterns for implementation
│   ├── pr-review-comments.md         # PR review comment handling
│   ├── pull-requests.md              # PR creation rules
│   ├── pytest.md                     # Test rules (scoped to tests/**/*.py)
│   ├── python.md                     # Python style rules (scoped to *.py)
│   └── sonarqube.md                  # SonarQube integration rules
│
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE/
│   │   ├── 01-bug-report.yml
│   │   ├── 02-feature-request.yml
│   │   ├── 03-tech-debt.yml
│   │   ├── 04-story.yml
│   │   └── 05-retro-action.yml
│   └── workflows/
│       ├── tests.yml                 # Lint → format → type check → test (matrix)
│       ├── docs.yml                  # MkDocs build verification
│       └── release-please.yml        # Release automation on develop
│
├── src/adk_secure_sessions/
│   ├── __init__.py                   # Public API: __all__ (13 symbols, alphabetical)
│   ├── protocols.py                  # EncryptionBackend protocol (PEP 544)
│   ├── exceptions.py                 # SecureSessionError hierarchy
│   ├── serialization.py              # encrypt_session, decrypt_session, envelope format
│   ├── backends/
│   │   ├── __init__.py               # Empty or __all__ only (not a public API surface)
│   │   └── fernet.py                 # FernetBackend (BACKEND_ID=1)
│   └── services/
│       ├── __init__.py               # Empty or __all__ only (not a public API surface)
│       └── encrypted_session.py      # EncryptedSessionService (BaseSessionService)
│
├── tests/
│   ├── conftest.py                   # ⚠️ MISSING — shared fixtures (backends, services)
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── conftest.py               # ⚠️ MISSING — unit-specific fixtures
│   │   ├── test_protocols.py         # Protocol conformance + runtime validation
│   │   ├── test_exceptions.py        # Exception hierarchy tests
│   │   ├── test_fernet_backend.py    # FernetBackend encrypt/decrypt round-trips
│   │   ├── test_serialization.py     # Envelope format, round-trip, edge cases
│   │   └── test_encrypted_session_service.py  # Service CRUD + encryption verification
│   └── integration/
│       ├── __init__.py
│       ├── conftest.py               # ⚠️ MISSING — integration-specific fixtures
│       └── test_adk_integration.py   # Full stack: create → append → get → verify
│
├── docs/
│   ├── index.md                      # Site homepage
│   ├── ARCHITECTURE.md               # High-level architecture (Mermaid diagrams)
│   ├── ROADMAP.md                    # 4-phase roadmap
│   ├── project-overview.md           # Project overview
│   ├── source-tree-analysis.md       # Source tree documentation
│   ├── development-guide.md          # Developer setup
│   ├── changelog.md                  # Points to CHANGELOG.md
│   ├── adr/
│   │   ├── index.md
│   │   ├── ADR-000-strategy-decorator-architecture.md
│   │   ├── ADR-001-protocol-based-interfaces.md
│   │   ├── ADR-002-async-first.md
│   │   ├── ADR-003-field-level-encryption.md
│   │   ├── ADR-004-adk-schema-compatibility.md
│   │   └── ADR-005-exception-hierarchy.md
│   ├── contributing/
│   │   └── docstring-templates.md
│   └── reference/
│       └── index.md                  # Auto-generated API reference entry
│
├── scripts/
│   └── gen_ref_pages.py              # MkDocs API reference generation
│
└── _bmad-output/                     # BMAD workflow outputs
    ├── project-context.md
    ├── planning-artifacts/
    │   ├── prd.md
    │   ├── prd-validation-report.md
    │   └── architecture.md           # This document
    ├── implementation-artifacts/
    │   └── tech-spec-release-please-cleanup.md
    └── test-artifacts/
        └── test-review.md
```

**Phase 2 Additions (pre-publish):**

```
src/adk_secure_sessions/
├── py.typed                          # PEP 561 marker
└── (ConfigurationError in exceptions.py, version column in schema)

tests/
├── conftest.py                       # Create: shared fixtures
├── unit/conftest.py                  # Create: unit-specific fixtures
└── integration/conftest.py           # Create: integration-specific fixtures

pyproject.toml                        # Register pytest markers: benchmark, integration

SECURITY.md                           # Responsible disclosure policy

.github/workflows/
├── publish.yml                       # PyPI publish on release tags (runs own tests)
└── (TestPyPI pre-release step in publish.yml)
```

**Phase 3 Anticipated Additions:**

```
src/adk_secure_sessions/
├── backends/
│   └── aes_gcm.py                    # AesGcmBackend (BACKEND_ID=2)
├── persistence/                      # NEW: Persistence abstraction
│   ├── __init__.py                   # Empty or __all__ only
│   ├── sqlite.py                     # SQLite persistence (extracted from service)
│   └── postgresql.py                 # PostgreSQL persistence
├── rotation.py                       # Key rotation utilities
└── services/
    ├── __init__.py
    ├── session_orchestrator.py        # ADK interface (REPLACES encrypted_session.py)
    └── encryption_coordinator.py      # Backend selection + envelope (REPLACES encrypted_session.py)
    # encrypted_session.py is DELETED — EncryptedSessionService re-exported
    # from session_orchestrator.py via top-level __init__.py for backwards compat

tests/
├── conftest.py                       # Add: multi-backend fixture factory
├── benchmarks/                       # NEW: Performance tests
│   ├── conftest.py                   # Benchmark fixtures
│   └── test_encryption_overhead.py
└── unit/
    ├── test_aes_gcm_backend.py
    ├── test_sqlite_persistence.py
    ├── test_postgresql_persistence.py
    └── test_rotation.py
```

### Subpackage Export Rule

Subpackage `__init__.py` files (`backends/__init__.py`, `services/__init__.py`, `persistence/__init__.py`) are **empty or contain only `__all__`** for subpackage-level imports. They are **not** public API surfaces.

The top-level `src/adk_secure_sessions/__init__.py` is the **sole public API surface**. All public symbols are re-exported there. This prevents two import paths to the same symbol and ensures a single canonical import for every public class, function, and exception.

### Architectural Boundaries

**Encryption Boundary:**

The encryption boundary is the core architectural invariant. All data crossing from the service layer to the persistence layer passes through `serialization.py` (`encrypt_session` / `decrypt_session`). No exceptions.

```
┌─────────────────────────────────┐
│  ADK Agent (upstream caller)    │
│  Session, Event models          │
└──────────┬──────────────────────┘
           │ async API
┌──────────▼──────────────────────┐
│  Service Layer                  │
│  EncryptedSessionService        │
│  (Phase 3: SessionOrchestrator) │
└──────────┬──────────────────────┘
           │ dict[str, Any]
┌──────────▼──────────────────────┐
│  Serialization Layer            │
│  encrypt_session / decrypt_session
│  Envelope: [ver][backend_id][ct]│
└──────────┬──────────────────────┘
           │ bytes (envelope)
┌──────────▼──────────────────────┐
│  Persistence Layer              │
│  SQLite (Phase 2)               │
│  PostgreSQL (Phase 3)           │
│  Stores opaque encrypted blobs  │
└─────────────────────────────────┘
```

**Metadata vs. Encrypted Data:**

| Field | Storage | Queryable |
|-------|---------|-----------|
| `session_id`, `app_name`, `user_id` | Plaintext | Yes |
| `created_at`, `updated_at` | Plaintext | Yes |
| `version` | Plaintext | Yes |
| Session `state` | Encrypted envelope | No (opaque blob) |
| Event `content` | Encrypted envelope | No (opaque blob) |

**Protocol Boundary:**

All extensibility contracts use PEP 544 `@runtime_checkable` Protocol. Protocols live in `protocols.py` — the single source of truth for interface contracts:

| Protocol | Consumers | Implementors |
|----------|-----------|-------------|
| `EncryptionBackend` | `serialization.py`, service layer | `FernetBackend`, future `AesGcmBackend`, KMS backends |
| `PersistenceBackend` (Phase 3) | Service orchestrator | `SqlitePersistence`, `PostgresqlPersistence` |

**Dependency Direction:**

```
protocols.py ← (no dependencies, leaf module)
exceptions.py ← (no dependencies, leaf module)
serialization.py ← protocols.py, exceptions.py
backends/fernet.py ← protocols.py, exceptions.py
services/encrypted_session.py ← serialization.py, backends, protocols.py, exceptions.py
__init__.py ← re-exports from all modules
```

**Rule:** Dependencies flow inward. `protocols.py` and `exceptions.py` are leaf modules with zero internal imports. Circular dependencies are forbidden.

### Data Flow

**Encrypt Path (write):**

```
ADK Agent → create_session(state={...})
  → EncryptedSessionService.create_session()
    → encrypt_session(state_dict, backend, backend_id)
      → json.dumps(state_dict) → plaintext bytes
      → backend.encrypt(plaintext) → ciphertext bytes
      → envelope: [version][backend_id][ciphertext]
    → INSERT INTO sessions (..., state=envelope_bytes)
  → return Session(state=original_dict)
```

**Decrypt Path (read) — envelope dispatch:**

```
ADK Agent → get_session(session_id=...)
  → EncryptedSessionService.get_session()
    → SELECT state FROM sessions WHERE session_id=?
    → envelope bytes
    → decrypt_session(envelope, backend)
      → read header: [version][backend_id]
      → dispatch to backend by backend_id
      → backend.decrypt(ciphertext) → plaintext bytes
      → json.loads(plaintext) → state dict
  → return Session(state=state_dict)
```

The header-first dispatch is what makes key rotation possible without changing the service layer. The service doesn't need to know which backend encrypted a given row — the envelope tells it.

### Requirements to Structure Mapping

**FR Category → Module Mapping:**

| FR Category | Primary Module(s) | Phase |
|------------|-------------------|-------|
| FR1-FR4: Encryption backend | `protocols.py`, `backends/fernet.py` | 1 (done) |
| FR5-FR10: Session operations | `services/encrypted_session.py` | 1 (done) |
| FR11-FR14: Configuration | `services/encrypted_session.py` constructor | 1 (done) |
| FR15: Error handling | `exceptions.py` (+`ConfigurationError` in Phase 2) | 1+2 |
| FR16-FR18: Extensibility | `protocols.py`, `serialization.py` (envelope) | 1 (done) |
| FR19-FR26: Database ops | `services/encrypted_session.py` | 1 (done) |
| FR27-FR45: PyPI/docs/release | `pyproject.toml`, `docs/`, `.github/workflows/` | 2 |
| FR46-FR47: AES-GCM backend | `backends/aes_gcm.py` | 3 |
| FR48: Key rotation | `rotation.py` | 3 |
| FR49-FR51: PostgreSQL | `persistence/postgresql.py` | 3 |
| FR52-FR54: KMS backends | `backends/aws_kms.py`, `gcp_kms.py`, `vault.py` | 4 |
| FR55: Audit logging | `audit.py` | 4 |
| FR56: Release pipeline | `.github/workflows/publish.yml` | 2 |

**Cross-Cutting Concern → Location Mapping:**

| Concern | Location(s) |
|---------|------------|
| Encryption boundary integrity | `serialization.py` (single enforcement point) |
| Envelope protocol | `serialization.py` (format), `protocols.py` (contract) |
| Async enforcement | Every public module (pattern, not a single file) |
| Exception discipline | `exceptions.py` (definitions), all modules (usage) |
| Public API surface | `__init__.py` (`__all__` list) |
| Quality enforcement | `scripts/code_quality_check.sh`, `.pre-commit-config.yaml` |
| CI quality gates | `.github/workflows/tests.yml` |
| AI agent rules | `.claude/rules/` (7 rule files) |

### Integration Points

**Internal Communication:**

Components communicate through direct Python imports and function calls. There is no message bus, event system, or inter-process communication. This is a single-process library, not a distributed system.

| Caller | Callee | Interface |
|--------|--------|-----------|
| Service layer | Serialization | `encrypt_session()` / `decrypt_session()` |
| Serialization | Backend | `EncryptionBackend.encrypt()` / `.decrypt()` |
| Service layer | Persistence (SQLite) | Direct `aiosqlite` queries (Phase 2) |
| Service layer | Persistence protocol | `PersistenceBackend` protocol methods (Phase 3) |

**External Integration Points:**

| External System | Integration | Direction |
|----------------|-------------|-----------|
| Google ADK | `BaseSessionService` subclass | ADK calls our service methods |
| SQLite | `aiosqlite` async driver | Our service writes/reads the database |
| `cryptography` library | `Fernet` (Phase 1), AES-GCM (Phase 3) | Our backends delegate to `cryptography` |
| PostgreSQL (Phase 3) | `asyncpg` or `psycopg3` | Our persistence writes/reads the database |
| KMS SDKs (Phase 4) | `boto3`, `google-cloud-kms`, `hvac` | Our backends delegate to KMS APIs |

### File Organization Patterns

**Configuration Files:** All in project root. No nested config directories.

**Source Organization:** `src/` layout with `src/adk_secure_sessions/` as the single package. No namespace packages. Subpackage `__init__.py` files are empty — top-level `__init__.py` is the sole public API.

**Test Organization:** `tests/` at project root with `unit/`, `integration/`, and (Phase 3) `benchmarks/` subdirectories. Test files mirror source: `test_<module>.py`. Shared fixtures in `conftest.py` at each level. Register custom markers (`benchmark`, `integration`) in `pyproject.toml`.

**Documentation:** `docs/` at project root. ADRs in `docs/adr/`. API reference auto-generated from docstrings via `scripts/gen_ref_pages.py`.

**Phase 2 Structural Action Items:**
- Create `tests/conftest.py`, `tests/unit/conftest.py`, `tests/integration/conftest.py`
- Register `benchmark` and `integration` markers in `pyproject.toml` `[tool.pytest.ini_options]`
- Add `py.typed` marker to `src/adk_secure_sessions/`
- Create `SECURITY.md`

## Architecture Validation Results

### How to Use This Document

- **Starting a new story?** → Check "Requirements to Structure Mapping" to find which modules you'll touch
- **Creating a new module?** → Read "Implementation Patterns" for naming, placement, and reference files
- **Adding a new backend?** → Follow "Protocol Extension Patterns" for backend ID, naming, and conformance tests
- **Unsure about a boundary?** → Check "Architectural Boundaries" and "Dependency Direction"
- **Checking Phase 2 priorities?** → See "Implementation Handoff" at the bottom

### Coherence Validation ✅

**Decision Compatibility:**

| Decision Pair | Compatible? | Notes |
|--------------|-------------|-------|
| Schema reservation (v. column) + ConfigurationError | ✅ Yes | Independent changes, no interaction |
| Schema reservation + existing ADR-004 (own schema) | ✅ Yes | Version column is within our owned schema |
| ConfigurationError + ADR-005 (exception hierarchy) | ✅ Yes | Follows ADR-005's "add when code demands" principle |
| Persistence protocol direction + ADR-001 (protocols over inheritance) | ✅ Yes | PEP 544 Protocol, consistent with all other contracts |
| Service decomposition direction + ADR-000 (direct implementation) | ✅ Yes | Still direct BaseSessionService impl, just decomposed internally |
| Extras group strategy + NFR23 (≤5 runtime deps) | ✅ Yes | Optional deps don't count toward the ceiling |

No contradictions found. All decisions are mutually compatible.

**Pattern Consistency:**

| Pattern Area | Aligned with Decisions? | Notes |
|-------------|------------------------|-------|
| Database naming | ✅ | snake_case matches existing schema in encrypted_session.py |
| SQL formatting | ✅ | Parametrized-only rule matches ADR-004 (own schema, raw SQL) |
| Module placement | ✅ | Follows existing src/ layout conventions |
| Protocol extension | ✅ | Matches ADR-001 (Protocol over inheritance) |
| Async boundaries | ✅ | Matches ADR-002 (async-first) |
| Test patterns | ✅ | Encryption boundary verification matches ADR-003 (field-level encryption) |
| Backend config boundary | ✅ | Dependency injection matches Protocol-based design |

**Structure Alignment:**

| Structure Element | Supports Decisions? | Notes |
|------------------|---------------------|-------|
| Phase 2 tree | ✅ | ConfigurationError, version column, py.typed, SECURITY.md all mapped |
| Phase 3 tree | ✅ | Persistence package, service decomposition, AES-GCM backend all placed |
| conftest.py gaps | ✅ | Identified as Phase 2 action item |
| Subpackage export rule | ✅ | Prevents import path ambiguity |

**Dependency Direction (Current + Phase 3):**

Current:

```
protocols.py ← (no dependencies, leaf module)
exceptions.py ← (no dependencies, leaf module)
serialization.py ← protocols.py, exceptions.py
backends/fernet.py ← protocols.py, exceptions.py
services/encrypted_session.py ← serialization.py, backends, protocols.py, exceptions.py
__init__.py ← re-exports from all modules
```

Phase 3 decomposition:

```
persistence/sqlite.py ← exceptions.py (only)
persistence/postgresql.py ← exceptions.py (only)
services/session_orchestrator.py ← serialization.py, persistence/, protocols.py, exceptions.py
services/encryption_coordinator.py ← backends/, protocols.py, exceptions.py
```

**Critical invariant:** Persistence modules depend only on `exceptions.py`. They never import from `serialization.py` or `backends/`. The persistence layer receives opaque bytes (already-encrypted envelopes) and stores them — it never sees plaintext. If a persistence module ever imports from `serialization.py`, the layering is violated.

### Requirements Coverage Validation ✅

**Functional Requirements (56 FRs):**

| FR Range | Category | Coverage | Status |
|----------|----------|----------|--------|
| FR1-FR4 | Encryption backend | `protocols.py`, `backends/fernet.py` | ✅ Phase 1 done |
| FR5-FR10 | Session operations | `services/encrypted_session.py` | ✅ Phase 1 done |
| FR11-FR14 | Configuration | `services/encrypted_session.py` constructor | ✅ Phase 1 done |
| FR15 | Error handling | `exceptions.py` + Decision 2 (ConfigurationError) | ✅ Phase 2 |
| FR16-FR18 | Extensibility | `protocols.py`, `serialization.py` (envelope) | ✅ Phase 1 done |
| FR19 | Database operations | `services/encrypted_session.py` | ✅ Phase 1 done |
| **FR20** | **SQLAlchemy ORM migration** | **Superseded** — persistence protocol (PEP 544) replaces ORM migration per Deferred Decision 3, resolving contradiction between PRD and project-context.md | ⚠️ **Superseded** |
| FR21-FR26 | Database operations | `services/encrypted_session.py` | ✅ Phase 1 done |
| FR27-FR45 | PyPI/docs/release | `pyproject.toml`, `docs/`, `.github/workflows/` | ✅ Phase 2 mapped |
| FR46-FR47 | AES-GCM backend | `backends/aes_gcm.py` + envelope extension pattern | ✅ Phase 3 mapped |
| FR48 | Key rotation | `rotation.py` + design direction documented | ✅ Phase 3 mapped |
| FR49-FR51 | PostgreSQL | `persistence/postgresql.py` + persistence protocol direction | ✅ Phase 3 mapped |
| FR52-FR54 | KMS backends | `backends/` + extras groups defined | ✅ Phase 4 mapped |
| FR55 | Audit logging | `audit.py` | ✅ Phase 4 mapped |
| FR56 | Release pipeline | `.github/workflows/publish.yml` | ✅ Phase 2 mapped |

**All 56 FRs architecturally addressed.** FR20 explicitly superseded by architecture decision.

**Non-Functional Requirements (28 NFRs):**

| NFR | Requirement | Architectural Support | Status |
|-----|------------|----------------------|--------|
| NFR1 | <20% encryption overhead | Performance test pattern (relative overhead) | ✅ |
| NFR2 | asyncio.to_thread for crypto | Async boundary rules table | ✅ |
| NFR3 | Async I/O exclusively | Async-first convention (ADR-002) | ✅ |
| NFR5 | No plaintext data paths | Encryption boundary invariant + verification test pattern | ✅ |
| NFR7 | Wrong-key → DecryptionError | Test pattern: wrong-key assertion | ✅ |
| NFR8 | Zero unpatched CVEs | pip-audit in security scanning tiers + publish pipeline | ✅ |
| NFR23 | ≤5 runtime deps | Extras group strategy, dependency ceiling constraint | ✅ |
| NFR25 | 50-coroutine SQLite writes | Phase 2: guaranteed by aiosqlite's single-writer connection model (serialized writes). Phase 3: version column enables optimistic concurrency when PostgreSQL introduces true multi-writer scenarios. | ✅ |
| NFR26 | 10-writer PostgreSQL | Deferred to Phase 3 persistence + concurrency design | ✅ |
| NFR27 | Optimistic concurrency | Decision 1: version column reserved, activated Phase 3 | ✅ |
| NFR28 | 5-minute integration | Phase 2 README/quickstart in roadmap | ✅ |

### Implementation Readiness Validation ✅

**Decision Completeness:** ✅
- 2 active decisions documented with rationale, options considered, consensus
- 4 deferred decisions documented with intent and trigger conditions
- All decisions traced to affected files and phases

**Structure Completeness:** ✅
- Complete current tree with every file
- Phase 2 and Phase 3 additions explicitly shown
- Missing files identified (conftest.py) with action items
- Phase 3 decomposition strategy explicit (replace, not coexist)

**Pattern Completeness:** ✅
- 9 pattern categories with 9 Party Mode enhancements
- Concrete reference implementations cited for each category
- Anti-patterns listed
- Enforcement guidelines with 5 mandatory rules

### Data Flow Completeness

**Encrypt Path — session state (write):**

```
ADK Agent → create_session(state={...})
  → EncryptedSessionService.create_session()
    → encrypt_session(state_dict, backend, backend_id)
      → json.dumps(state_dict) → plaintext bytes
      → backend.encrypt(plaintext) → ciphertext bytes
      → envelope: [version][backend_id][ciphertext]
    → INSERT INTO sessions (..., state=envelope_bytes)
  → return Session(state=original_dict)
```

**Encrypt Path — event content (append):**

```
ADK Agent → append_event(session, event)
  → EncryptedSessionService.append_event()
    → encrypt_json(event_content, backend, backend_id)
      → json.dumps(event_content) → plaintext bytes
      → backend.encrypt(plaintext) → ciphertext bytes
      → envelope: [version][backend_id][ciphertext]
    → INSERT INTO events (..., content=envelope_bytes)
```

**Decrypt Path — envelope dispatch (read):**

```
ADK Agent → get_session(session_id=...)
  → EncryptedSessionService.get_session()
    → SELECT state FROM sessions WHERE session_id=?
    → envelope bytes
    → decrypt_session(envelope, backend)
      → read header: [version][backend_id]
      → dispatch to backend by backend_id
      → backend.decrypt(ciphertext) → plaintext bytes
      → json.loads(plaintext) → state dict
  → return Session(state=state_dict)
```

The header-first dispatch is what makes key rotation possible without changing the service layer.

### Gap Analysis Results

**Critical Gaps:** None.

**Important Gaps:**

| # | Gap | Impact | Recommendation |
|---|-----|--------|---------------|
| 1 | **ADR-006 needed for ConfigurationError** | When Decision 2 is implemented, the exception addition should be captured in a new ADR | Create ADR-006 during the ConfigurationError implementation story |

**Nice-to-Have Gaps:**

| # | Gap | Notes |
|---|-----|-------|
| 1 | Mermaid diagrams | This document uses ASCII. Consider converting during Phase 2 docs work. |
| 2 | Decision changelog | Low priority — git history covers this. |

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed (56 FRs, 28 NFRs, 6 ADRs, 16 docs)
- [x] Scale and complexity assessed (high — security library)
- [x] Technical constraints identified (8 constraints, all satisfied)
- [x] Cross-cutting concerns mapped (7 concerns with phase relevance)
- [x] Forward-looking decisions categorized (2 decide-now, 4 design-direction)

**✅ Technology Foundation**
- [x] Runtime dependencies documented with versions
- [x] Development toolchain fully specified
- [x] CI/CD pipeline components mapped
- [x] Security scanning posture defined (2 tiers)
- [x] Phase 2-4 technology additions anticipated
- [x] Extras group strategy defined (no `[all]`)

**✅ Architectural Decisions**
- [x] Critical decisions documented with consensus (schema reservation)
- [x] Important decisions documented with consensus (ConfigurationError)
- [x] Deferred decisions documented with triggers (4 Phase 3+ items)
- [x] Implementation sequence defined (dependency-ordered)
- [x] Cross-component dependencies mapped
- [x] FR20 (SQLAlchemy ORM) explicitly superseded

**✅ Implementation Patterns**
- [x] Naming conventions established (database, SQL, code)
- [x] Structure patterns defined (module placement, subpackage exports)
- [x] Protocol extension patterns specified (encryption + persistence)
- [x] Configuration patterns documented (DI, no env vars)
- [x] Async boundary rules codified
- [x] Test patterns comprehensive (8 sub-patterns including encryption verification + schema reservation)
- [x] Enforcement guidelines with 5 mandatory rules + 7 anti-patterns

**✅ Project Structure**
- [x] Complete directory structure with every file
- [x] Phase 2 and Phase 3 additions explicitly mapped
- [x] Architectural boundaries defined (encryption, protocol, dependency direction)
- [x] Data flow documented (encrypt session + encrypt event + decrypt with envelope dispatch)
- [x] FR-to-module mapping complete (56 FRs → specific files, FR20 superseded)
- [x] Cross-cutting concern-to-location mapping complete
- [x] Integration points documented (internal + external)
- [x] Phase 2 structural action items identified
- [x] Phase 3 dependency direction documented (persistence never sees plaintext)

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- 6 accepted ADRs provide strong foundational decisions — this architecture builds on them, not against them
- Encryption boundary is a single invariant with a concrete verification test pattern
- Protocol-based extensibility gives clean separation for Phase 3-4 additions
- Schema reservation avoids a breaking migration for every early adopter
- Every FR maps to a specific file; every pattern points to a reference implementation
- 6 Party Mode sessions produced 33 enhancements across all sections
- Phase 3 dependency direction makes "persistence never sees plaintext" structurally enforceable

**Areas for Future Enhancement:**
- ADR-006 (ConfigurationError) should be written during implementation
- Phase 3 persistence protocol will need its own ADR
- Mermaid diagram conversion for this document (low priority)
- Backend authoring guide (Phase 3, supports Tomás's user journey)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently — read the reference file before creating a new module
- Respect project structure and boundaries — top-level `__init__.py` is the sole public API
- Run `bash scripts/code_quality_check.sh --all --verbose` before marking any task complete
- Verify encryption boundary for every new persistence path

**Phase 2 Implementation Priorities (dependency-ordered):**

| Order | Task | Dependencies | Parallelizable |
|-------|------|-------------|---------------|
| 1 | Register `benchmark` and `integration` markers in `pyproject.toml` | None | Yes (with #2-#4, #6-#8) |
| 2 | Create `tests/conftest.py`, `tests/unit/conftest.py`, `tests/integration/conftest.py` | None | Yes (with #1, #3-#4, #6-#8) |
| 3 | Add `ConfigurationError` to `exceptions.py` + export from `__init__.py` | None | Yes (with #1-#2, #4, #6-#8) |
| 4 | Add `version INTEGER DEFAULT 1` to schema (`sessions`, `app_states`, `user_states`) | None | Yes (with #1-#3, #6-#8) |
| 5 | Add constructor validation raising `ConfigurationError` | Depends on #3 | No |
| 6 | Add `py.typed` marker to `src/adk_secure_sessions/` | None | Yes |
| 7 | Create `SECURITY.md` | None | Yes |
| 8 | Add `pip-audit` check to publish workflow | None | Yes |

**Schema Reservation Test Pattern:** For inert columns (Phase 2 version column), verify column exists via `PRAGMA table_info` or equivalent and assert default value. No behavioral tests needed until the column is activated in Phase 3.
