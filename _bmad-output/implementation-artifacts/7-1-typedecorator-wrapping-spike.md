# Story 7.1: TypeDecorator Wrapping Spike

Status: review
Branch: feat/spike-7-1-typedecorator-wrapping
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/129

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **library maintainer**,
I want **a validated proof-of-concept that wraps DatabaseSessionService via SQLAlchemy TypeDecorator for transparent encrypt/decrypt at the ORM boundary**,
so that **I have evidence-based confidence (or a clear no-go) before committing to the architecture migration**.

## Acceptance Criteria

1. **Round-trip prototype works.** Given ADK V1's `DatabaseSessionService` merges state in Python (`dict | delta`), when a prototype `TypeDecorator` is implemented that encrypts on `process_bind_param` and decrypts on `process_result_value`, then a round-trip test demonstrates: create session with state -> retrieve session -> state matches original. The prototype uses the existing `FernetBackend` and serialization envelope for encryption. (FR-NEW-4)

2. **Conformance verified.** Given the prototype wraps `DatabaseSessionService`, when the same inputs are provided to both the wrapped and unwrapped service, then the resulting `Session` and `Event` objects are structurally identical (same fields, same types, same values).

3. **Version column assessment.** Given the current schema reserves a `version INTEGER DEFAULT 1` column on `sessions`, `app_states`, and `user_states` (Story 1.2), when wrapping `DatabaseSessionService` inherits ADK's schema, then the spike assesses whether the `version` column reservation is preserved, lost, or can be added via schema extension. The impact on Story 4.4 (optimistic concurrency / key rotation) is documented.

4. **Migration path assessed.** Given existing users have SQLite databases with encrypted data under the current raw-aiosqlite schema, when they upgrade to the wrapped version, then the spike assesses whether data migration is required, whether the wrapped service can read existing databases, and whether a migration utility is needed. The migration assessment is documented with a recommendation.

5. **Test feasibility assessed.** Given the prototype exists, when test feasibility is assessed, then the spike documents whether the new architecture can be tested cleanly — conformance tests, round-trip tests, and runner integration tests are all feasible. Any testing challenges or limitations are documented.

6. **Go/no-go findings document produced.** Given all assessments are complete, when the spike produces a findings document, then it contains a clear **go/no-go recommendation** with evidence. The findings document is saved to `_bmad-output/implementation-artifacts/7-1-spike-findings.md`. If no-go, the document explains what blocked the approach and proposes alternatives.

**This story gates all subsequent Epic 7 stories. Stories 7.2-7.6 proceed only on a "go" decision.**

## Tasks / Subtasks

- [x] Task 1: Research and document ADK's DatabaseSessionService internals (AC: 1, 2, 3)
  - [x] Read ADK source: `google/adk/sessions/database_session_service.py`
  - [x] Read ADK schema: `google/adk/sessions/schemas/v1.py` (StorageSession, StorageAppState, StorageUserState, StorageEvent models)
  - [x] Read ADK shared types: `google/adk/sessions/schemas/shared.py` (DynamicJSON TypeDecorator)
  - [x] Document table schema, column types, state merging mechanism, and `_merge_state()` flow
  - [x] Identify all columns that store sensitive data needing encryption: `state` (3 tables) + `event_data` (events table)
- [x] Task 2: Implement `EncryptedJSON` TypeDecorator prototype (AC: 1)
  - [x] Create `scripts/spike_typedecorator.py` (standalone prototype, NOT under `src/`)
  - [x] Implement `process_bind_param`: `dict -> json.dumps -> encrypt_json(backend) -> base64/bytes`
  - [x] Implement `process_result_value`: `bytes -> decrypt_json(backend) -> json.loads -> dict`
  - [x] Handle the envelope format: `[version_byte][backend_id_byte][ciphertext]` must be preserved
  - [x] Address sync/async mismatch: TypeDecorator methods are synchronous — call `cryptography.fernet.Fernet.encrypt()`/`decrypt()` directly (sync API), NOT the async `encrypt_json`/`decrypt_json` wrappers. SQLAlchemy's `AsyncSession.run_sync()` already runs in a thread pool, so sync Fernet is safe. Verify this assumption.
  - [x] Handle dialect differences (optional, low priority): spike targets SQLite only. PostgreSQL compatibility is a "comes for free later" benefit, not a spike deliverable
- [x] Task 3: Wire prototype to DatabaseSessionService (AC: 1, 2)
  - [x] **CRITICAL FIRST**: Check if `DatabaseSessionService.__init__` accepts schema configuration or custom engine/sessionmaker. If it hardcodes schema classes, determine the cleanest override path (custom model classes, engine-level type mapping, or event hooks). If no clean path exists, **that is an early blocker — document and assess**.
  - [x] Create custom SQLAlchemy model classes mirroring ADK's v1 schema but using `EncryptedJSON` instead of `DynamicJSON` on `state` and `event_data` columns
  - [x] Create a wrapped `DatabaseSessionService` instance using the custom models
  - [x] Write a round-trip test: `create_session(state={"key": "secret"})` -> `get_session()` -> assert state matches
  - [x] Write a conformance test: compare Session/Event objects from wrapped vs. unwrapped service
- [x] Task 4: Assess version column reservation (AC: 3)
  - [x] Check if ADK's v1 schema includes a `version` column or if it was our custom addition
  - [x] If custom: determine if SQLAlchemy schema extension (e.g., `Column` injection or migration) can add it
  - [x] Document impact on Story 4.4 (optimistic concurrency / key rotation)
- [x] Task 5: Assess migration path (AC: 4)
  - [x] Compare current schema (raw aiosqlite, BLOB columns) vs. ADK's schema (SQLAlchemy, JSON/TEXT columns)
  - [x] Determine if a migration utility is needed (schema transformation + data re-encryption)
    - [x] Keep assessment lightweight — we have no real users with production data yet. Focus on "is migration needed?" not "how to migrate." Details deferred to Story 7.3.
  - [x] Document recommendation: clean migration vs. side-by-side vs. fresh start
- [x] Task 6: Assess test feasibility (AC: 5)
  - [x] Can existing conformance tests (`test_adk_integration.py`) be adapted for the wrapped service?
  - [x] Can raw-DB encryption verification tests still work? (TypeDecorator hides encryption from ORM, need to bypass)
  - [x] Can the ADK Runner integration test (`test_adk_runner.py`) work with the wrapped service?
  - [x] Document any testing challenges or limitations
- [x] Task 7: Produce go/no-go findings document (AC: 6)
  - [x] Create `_bmad-output/implementation-artifacts/7-1-spike-findings.md`
  - [x] **FIRST LINE after title**: Bold `## Decision: GO` or `## Decision: NO-GO` — unmissable, not buried in prose
  - [x] Include: prototype results, conformance assessment, version column assessment, migration assessment, test feasibility, performance notes
  - [x] Include clear evidence supporting the decision
  - [x] If go: outline the implementation plan for Stories 7.2-7.6
  - [x] If no-go: explain blockers and propose alternatives

### Cross-Cutting Test Maturity (Standing Task)

<!-- Every story includes one small-footprint, high-risk-area test addition.
     This is brownfield hardening -- pick a gap in an area NOT related to the
     story scope so the safety net grows steadily across epics. -->

**Source: TEA test-review 2026-03-05 Coverage Gap Document**

- [x] Identify one high-risk area lacking test coverage (outside story scope)
  - TEA Priority 1: Concurrent event appends on SAME session — already covered by T066
  - TEA Priority 2: Session state with deeply nested dicts (5+ levels of nesting, verify round-trip fidelity) — **selected**
- [x] Add test(s) -- small footprint, meaningful assertion
  - Added T036: `test_deeply_nested_dict_round_trip` in `tests/unit/test_serialization.py`
- [x] Verify new test(s) pass in CI

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1 | Spike script: `test_round_trip`, `test_append_event`, `test_deeply_nested_state`, `test_app_user_state_separation` in `scripts/spike_typedecorator.py` (8/8 pass) | done |
| 2 | Spike script: `test_conformance` (wrapped vs unwrapped Session objects — field-by-field comparison) | done |
| 3 | Findings document: Section 3 "Version Column Assessment" — no version column in ADK, schema extension viable | done |
| 4 | Findings document: Section 4 "Migration Path Assessment" — fresh start recommended, no users to migrate | done |
| 5 | Findings document: Section 5 "Test Feasibility Assessment" — all test categories feasible | done |
| 6 | `_bmad-output/implementation-artifacts/7-1-spike-findings.md` exists with `## Decision: GO` | done |

## Dev Notes

### Key Technical Context: Why Wrapping Became Viable

**ADK V0** (original): `DatabaseSessionService.append_event` used SQL-side state merging via `json_patch` — no interception points for encryption. Wrapping was correctly rejected in ADR-000.

**ADK V1** (current, >=1.22.0): State merging changed to Python-side `dict | delta` operation. The `_merge_state()` function in ADK's source does `copy.deepcopy(session_state)` and overlays `app:` and `user:` prefixed keys. This removed the SQL interception barrier, making TypeDecorator-based wrapping viable.

### ADK DatabaseSessionService Internals (from research)

**Schema (v1, `google/adk/sessions/schemas/v1.py`):**

| Table | Primary Key | Sensitive Columns | TypeDecorator |
|-------|-------------|-------------------|---------------|
| `sessions` | `(app_name, user_id, id)` | `state: MutableDict[str, Any]` | `DynamicJSON` |
| `app_states` | `app_name` | `state: MutableDict[str, Any]` | `DynamicJSON` |
| `user_states` | `(app_name, user_id)` | `state: MutableDict[str, Any]` | `DynamicJSON` |
| `events` | `(id, app_name, user_id, session_id)` | `event_data: dict[str, Any]` | `DynamicJSON` |

**DynamicJSON TypeDecorator** (`google/adk/sessions/schemas/shared.py`):
- `impl = Text` (uses TEXT for SQLite/MySQL, JSONB for PostgreSQL)
- `process_bind_param`: `dict -> json.dumps(value)` (non-PostgreSQL) or passthrough (PostgreSQL JSONB handles natively)
- `process_result_value`: `json.loads(value) -> dict` (non-PostgreSQL) or passthrough

**State merging** happens in Python via `_merge_state(app_state, user_state, session_state)`:
- Deep copies session state, overlays app/user states with prefixed keys
- No SQL-level state manipulation — all in Python

### Critical Risk: Sync/Async Mismatch in TypeDecorator

TypeDecorator's `process_bind_param` and `process_result_value` are **synchronous** methods. However:

1. SQLAlchemy's `AsyncSession` uses `run_sync()` internally, which runs the entire ORM operation (including TypeDecorator calls) in a **thread pool** via `asyncio.to_thread()`.
2. Therefore, Fernet `encrypt()`/`decrypt()` calls within TypeDecorator are already running in a thread — they won't block the event loop.
3. **This means synchronous Fernet calls in TypeDecorator are safe.** No need for `asyncio.to_thread()` wrapping inside the TypeDecorator itself.

**Verify this assumption in the spike.** If SQLAlchemy's async session does NOT use a thread pool for TypeDecorator calls, this is a blocker.

### Approach: Custom EncryptedJSON TypeDecorator

The prototype should implement a TypeDecorator that:
1. **Wraps or replaces** `DynamicJSON` on the `state` and `event_data` columns
2. On `process_bind_param`: `dict -> json.dumps() -> encrypt_json(backend, backend_id) -> base64 encode -> TEXT` (for SQLite compatibility)
3. On `process_result_value`: `TEXT -> base64 decode -> decrypt_json(backend) -> json.loads() -> dict`
4. Preserves the envelope format `[version_byte][backend_id_byte][ciphertext]` for key rotation compatibility

**Start with Approach A** (replace `DynamicJSON` entirely with `EncryptedJSON` wrapping `LargeBinary`/`Text`). This is simpler and has fewer moving parts. Only try Approach B (composing `EncryptedJSON` around `DynamicJSON`) if Approach A fails or has clear deficiencies.

### Prototype Location

**All spike code goes in `scripts/spike_typedecorator.py`** — NOT under `src/`. This is throwaway proof-of-concept code. The findings document goes in `_bmad-output/implementation-artifacts/7-1-spike-findings.md`.

All spike tests go in `scripts/` alongside the prototype. Do NOT create a `tests/spike/` directory — it could confuse the test runner and get accidentally committed.

### Guardrails

- **Do NOT modify any existing source code under `src/`** — this is a spike, not a production change
- **Do NOT modify existing tests** — spike tests are standalone in `scripts/`
- **Do NOT add new dependencies to `pyproject.toml`** — all needed packages (SQLAlchemy, aiosqlite, cryptography) are already in deps
- **DO use the existing `FernetBackend` and serialization envelope** — import from `adk_secure_sessions`
- **DO call Fernet's sync API directly** (`cryptography.fernet.Fernet.encrypt()`/`decrypt()`) inside TypeDecorator methods — NOT the async `encrypt_json`/`decrypt_json` wrappers, which are `async def` and cannot be called from sync TypeDecorator hooks. Reuse the envelope format logic (version byte + backend ID) but call encryption synchronously.
- **DO document everything** — the findings document IS the primary deliverable, not the code

### Previous Story Intelligence (6.3)

Story 6.3 was docs-only (revision markers). Key patterns from Epic 6 overall:
1. **Adversarial code review catches real issues** — even for non-code stories. Apply to spike findings document.
2. **Grep verification** — after any documentation changes, grep for consistency.
3. **Context-appropriate language** — findings document is for architects/maintainers, not end users.

### Peripheral Config Impact

No peripheral config impact — this story creates prototype code in `scripts/` and a findings document. No CI, pyproject.toml, mkdocs.yml, or pre-commit changes needed.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------:|
| `_bmad-output/implementation-artifacts/7-1-spike-findings.md` | NEW — spike findings document with go/no-go recommendation |
| None (docs site) | No user-facing docs changes — spike is internal |

### Project Structure Notes

- Spike prototype: `scripts/spike_typedecorator.py` — standalone script, NOT part of the package
- Findings document: `_bmad-output/implementation-artifacts/7-1-spike-findings.md` — primary deliverable
- No changes to `src/adk_secure_sessions/` or published docs
- All existing module paths, naming conventions, and public API remain untouched

### References

- [Source: docs/adr/ADR-000-strategy-decorator-architecture.md — "Why not wrap DatabaseSessionService" section + Revision Note]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 7, Story 7.1 acceptance criteria]
- [Source: google/adk/sessions/database_session_service.py — DatabaseSessionService implementation]
- [Source: google/adk/sessions/schemas/v1.py — StorageSession, StorageAppState, StorageUserState, StorageEvent models]
- [Source: google/adk/sessions/schemas/shared.py — DynamicJSON TypeDecorator]
- [Source: src/adk_secure_sessions/serialization.py — encrypt_json, decrypt_json, envelope format]
- [Source: _bmad-output/test-artifacts/test-review.md — Coverage Gap Document for cross-cutting test items]
- [Source: Issue #118 — Documentation honesty audit findings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 181 tests pass, 99.68% coverage
- [x] `pre-commit run --all-files` -- 9/9 hooks pass

## Code Review

- **Reviewer:**
- **Outcome:**

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
|   |          |         |            |

### Verification

- [ ] All HIGH findings resolved
- [ ] All MEDIUM findings resolved or accepted
- [ ] Tests pass after review fixes
- [ ] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-05 | Story created by create-story workflow |
| 2026-03-05 | Party mode review: 6 adjustments applied (sync API clarification, schema config check-first, approach A priority, lightweight migration, bold go/no-go, no tests/spike dir) |
| 2026-03-05 | Implementation complete: 8/8 spike tests pass, GO decision, findings document produced, T036 cross-cutting test added (181 tests, 99.68% coverage) |
| 2026-03-05 | Post-implementation party mode review: 6 findings applied to findings document (wrong-key error propagation, _SchemaClasses bypass, shared instance, sentinel test, sync/async note, changelog) |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — spike executed cleanly, 8/8 tests passed on second run (first run had a minor test bug: `append_event` returns `Event` not `Session`).

### Completion Notes List

1. `DatabaseSessionService.__init__` has NO schema customization — override path is `_get_schema_classes()` + `_prepare_tables()`
2. Sync Fernet in TypeDecorator is confirmed safe — SQLAlchemy AsyncSession runs ORM ops in thread pool
3. No version column in ADK's v1 schema — schema extension is viable for Story 4.4
4. Migration: fresh start recommended (no existing users)
5. All test categories feasible for the wrapped architecture
6. **Decision: GO** — all criteria support proceeding with Stories 7.2-7.6

### File List

| File | Action |
|------|--------|
| `scripts/spike_typedecorator.py` | Created — spike prototype with EncryptedJSON TypeDecorator, EncryptedDatabaseSessionService, 8 tests |
| `_bmad-output/implementation-artifacts/7-1-spike-findings.md` | Created — go/no-go findings document (GO decision) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified — 7-1 status: ready-for-dev → review |
| `_bmad-output/implementation-artifacts/7-1-typedecorator-wrapping-spike.md` | Modified — tasks marked done, AC-to-Test mapping filled, quality gates checked |
| `tests/unit/test_serialization.py` | Modified — added T036 deeply nested dict round-trip test (cross-cutting) |
