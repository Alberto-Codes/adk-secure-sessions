# Story 7.2: ADR — Architecture Migration Decision

Status: done
Branch: feat/adr-7-2-architecture-migration
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/131

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **future contributor reading the ADR trail**,
I want **a formal ADR documenting the decision to migrate from direct BaseSessionService implementation to DatabaseSessionService wrapping**,
so that **I understand why the architecture changed, what evidence supported the decision, and what trade-offs were accepted**.

## Acceptance Criteria

1. **ADR created following established format.** Given the spike (Story 7.1) produced a GO decision with evidence, when a new ADR is created (e.g., `docs/adr/ADR-007-architecture-migration.md`), then it follows the existing ADR format established by ADR-000 through ADR-006 — with Status, Date, Deciders header, and Context / Decision / Consequences / Alternatives Considered sections.

2. **Context explains the architectural evolution.** Given ADR-000 originally rejected DatabaseSessionService wrapping, when the Context section is written, then it explains: ADR-000's original rejection was based on V0-era `json_patch` SQL operations; ADK V1 changed state merging to Python-side `dict | delta`, making wrapping viable. The Context cites the specific technical change that unblocked wrapping.

3. **Decision states the new architecture.** Given the spike validated TypeDecorator-based wrapping, when the Decision section is written, then it states: wrap `DatabaseSessionService` via SQLAlchemy `TypeDecorator` for transparent encrypt/decrypt at the ORM boundary. The Decision describes the `EncryptedJSON` TypeDecorator approach and the `EncryptedDatabaseSessionService` subclass pattern.

4. **Rationale documents the benefits.** Given the wrapper approach provides significant benefits, when the Rationale/Decision section is written, then it documents: multi-database support for free (SQLite, PostgreSQL, MySQL, MariaDB), connection pooling for free, row-level locking for free, schema migration for free, focus on encryption as sole value-add, ~800 lines of raw SQL replaced by thin wrapper.

5. **Consequences section documents impacts.** Given the migration has concrete impacts, when the Consequences section is written, then it documents: aiosqlite removed as direct dependency, Epic 4 Stories 4.1-4.3 superseded, existing user migration path required (fresh start recommended), and the components that are kept vs. replaced (per spike findings Section 6).

6. **ADR references evidence.** Given the decision is evidence-based, when the ADR is written, then it references the spike findings document (`_bmad-output/implementation-artifacts/7-1-spike-findings.md`) and Issue #118 as evidence. The ADR status is "Accepted".

7. **ADR-000 revision note updated.** Given ADR-000 already has a revision note referencing Epic 7, when the new ADR is created, then ADR-000's revision note is reviewed for consistency with ADR-007 and updated if needed to cross-reference the new ADR number.

## Tasks / Subtasks

- [x] Task 1: Create ADR-007 file (AC: 1, 2, 3, 4, 5, 6)
  - [x] Create `docs/adr/ADR-007-architecture-migration.md` following the established format
  - [x] Write Status/Date/Deciders header block (Status: Accepted)
  - [x] Write Context section: ADR-000 V0 rejection reasoning, ADK V1 change to Python-side state merging, TypeDecorator viability. State that this ADR supersedes the "Direct Implementation" portion of ADR-000 (the "Strategy" portion — pluggable backends — remains valid)
  - [x] Write Decision section: EncryptedDatabaseSessionService wrapping DatabaseSessionService, EncryptedJSON TypeDecorator on state/event_data columns, sync Fernet in TypeDecorator (safe due to SQLAlchemy thread pool)
  - [x] Write Consequences section: what becomes easier (multi-DB, connection pooling, schema migration), what becomes harder (coupled to DatabaseSessionService internals), trade-offs (base64 overhead, `_get_schema_classes` internal dependency)
  - [x] Write Alternatives Considered section: keeping current direct implementation (rejected — more code to maintain, feature parity burden, no multi-DB), full ORM rewrite (rejected — over-engineering)
  - [x] Add references to spike findings document and Issue #118
- [x] Task 2: Update mkdocs nav and ADR index (AC: 1)
  - [x] Add ADR-007 entry to `mkdocs.yml` nav under the ADR section (~line 169, after ADR-006)
  - [x] Add ADR-007 row to `docs/adr/index.md` table (after ADR-006 row)
- [x] Task 3: Review and update ADR-000 cross-reference (AC: 7)
  - [x] Read current ADR-000 revision note
  - [x] Update revision note to reference ADR-007 by number (currently references "Epic 7" generically)
  - [x] ADR-000 status remains "Accepted" — update revision note only, do NOT change status
  - [x] Verify no contradictions between ADR-000 and ADR-007
- [x] Task 4: Verify ADR-004 consistency (AC: 7)
  - [x] Read ADR-004 revision note about schema ownership
  - [x] Update ADR-004 revision note to reference ADR-007 (change "may change" to "changes per ADR-007")
  - [x] Ensure ADR-004's "own our schema" principle is accurately contextualized: we now own the TypeDecorator and encrypted models, ADK owns the base schema

### Cross-Cutting Test Maturity (Standing Task)

<!-- Every story includes one small-footprint, high-risk-area test addition.
     This is brownfield hardening -- pick a gap in an area NOT related to the
     story scope so the safety net grows steadily across epics. -->

**Source: _bmad-output/test-artifacts/test-review.md — Coverage Gap Document, Priority 3, Gap 2**

**Selected gap: Tampered envelope header bytes** — security-critical path with zero current coverage. The envelope is a wire protocol; tampered version/backend_id bytes must produce clean `DecryptionError`, not silent garbage or crashes. This test survives the architecture migration (serialization layer is kept per spike findings Section 6).

- [x] Add test to `tests/unit/test_serialization.py` (near existing tampered-ciphertext tests, T030-T035 area)
  - [x] Flip version byte (position 0) to `0xFF` on a valid envelope, assert `DecryptionError`
  - [x] Flip backend_id byte (position 1) to `0xFF` on a valid envelope, assert `DecryptionError`
  - [x] Two assertions, one test function (~10-15 lines)
- [x] Verify new test(s) pass in CI

## AC-to-Test Mapping

<!-- This is a docs-only story. Verification is grep/file-existence checks, NOT pytest.
     For each AC, verify the ADR file exists and contains the required sections/content. -->

| AC # | Verification Method | Status |
|------|---------------------|--------|
| 1    | File exists at `docs/adr/ADR-007-architecture-migration.md` + section headers: Status/Date/Deciders, Context, Decision, Consequences, Alternatives (7 matches) | pass |
| 2    | grep ADR-007 for V0 rejection, ADK V1 change, json_patch, dict delta (6 matches) | pass |
| 3    | grep ADR-007 for TypeDecorator, EncryptedJSON, EncryptedDatabaseSessionService (16 matches) | pass |
| 4    | grep ADR-007 for multi-database, connection pooling, ~800 lines (3 matches) | pass |
| 5    | grep ADR-007 for aiosqlite, Epic 4, superseded, fresh, kept vs replaced (8 matches) | pass |
| 6    | grep ADR-007 for spike findings reference and Issue #118; Status: Accepted confirmed (4 matches) | pass |
| 7    | ADR-000 revision note references ADR-007; ADR-004 revision note references ADR-007; `mkdocs.yml` nav entry present; `index.md` row present | pass |

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch
- Testing standards summary

### Key Technical Context

**This is a documentation-only story.** No source code under `src/` is modified. The primary deliverable is `docs/adr/ADR-007-architecture-migration.md`.

### ADR Format (from existing ADRs)

All existing ADRs follow this structure:
```markdown
# ADR-NNN: Title

> **Status**: Accepted
> **Date**: YYYY-MM-DD
> **Deciders**: adk-secure-sessions maintainers

## Context
## Decision
## Consequences
### What becomes easier
### What becomes harder
### Trade-offs
## Alternatives Considered
```

Key formatting conventions:
- Status/Date/Deciders in blockquote header
- Code blocks for architecture diagrams (ASCII art)
- Tables for structured comparisons
- Revision Notes in blockquote format when updating existing ADRs

### ADR-000 Status Decision

ADR-000 status remains **"Accepted"** — do NOT change it to "Amended" or "Superseded." ADR-000's Strategy pattern (pluggable backends) is still fully valid. Only the "Direct Implementation" half is superseded by ADR-007. Update the revision note to reference ADR-007 by number, and have ADR-007's Context section state that it supersedes the "Direct Implementation" portion of ADR-000.

### Content Sources for ADR-007

The ADR content should be synthesized from these primary sources:

1. **Spike findings** (`_bmad-output/implementation-artifacts/7-1-spike-findings.md`):
   - Section 1: Round-trip prototype results (evidence for Decision)
   - Section 2: Conformance assessment (evidence for Decision)
   - Section 6: Implementation architecture — what we keep vs. replace (for Consequences)
   - Section 7: Risks and mitigations (for Consequences/Trade-offs)

2. **ADR-000** (`docs/adr/ADR-000-strategy-decorator-architecture.md`):
   - "Why not wrap DatabaseSessionService" section — the original V0 rejection reasoning
   - Revision Note — already acknowledges V1 changed the calculus

3. **ADR-004** (`docs/adr/ADR-004-adk-schema-compatibility.md`):
   - "Own our schema" principle — needs recontextualization
   - Revision Note — already references Epic 7

4. **Issue #118** — documentation honesty audit that prompted Epic 7

### ADR-000 Current Revision Note

The existing revision note in ADR-000 reads:
> **Revision Note (2026-03-04):** The rejection reasoning above was correct for ADK V0. ADK V1 changed state merging from SQL-side `json_patch` operations to Python-side `dict | delta`, removing the interception barrier described in point 1. `DatabaseSessionService` wrapping is now viable via `TypeDecorator`-based column encryption. Epic 7 explores this path — see Issue #118 and Epic 7 for the architectural evolution path.

This should be updated to reference "ADR-007" instead of "Epic 7 explores this path" since the decision is now formalized.

### ADR-004 Current Revision Note

The existing revision note in ADR-004 reads:
> **Revision Note (2026-03-04):** "Own our schema" is more precisely characterized as "schema derived from ADK's data model contract with encrypted column types." [...] Epic 7 (Architecture Migration) may change the schema ownership model by wrapping `DatabaseSessionService` instead of reimplementing storage. See Issue #118 and Epic 7 for the architectural evolution path.

This should be updated to reference ADR-007 and change "may change" to "will change" (decision is now accepted).

### Previous Story Intelligence (7.1)

From Story 7.1 development:
1. **Spike confirmed GO decision** — all 6 ACs met, 8/8 prototype tests passed
2. **Key architectural insight**: ADK V1's `_merge_state()` uses Python-side `dict | delta`, removing the V0 `json_patch` SQL barrier
3. **TypeDecorator approach validated**: `EncryptedJSON` replacing `DynamicJSON` on state/event_data columns
4. **Override points identified**: `_get_schema_classes()` and `_prepare_tables()` (internal but stable)
5. **Sync Fernet is safe**: SQLAlchemy AsyncSession runs ORM operations in thread pool
6. **Components kept**: FernetBackend, EncryptionBackend protocol, envelope format, exception hierarchy
7. **Components replaced**: EncryptedSessionService (current), raw aiosqlite, custom schema, manual encrypt/decrypt in CRUD

### Git Intelligence

Recent commits show:
- `b9919df` feat(spike): TypeDecorator wrapping spike — GO decision for Epic 7 (#130)
- `afbb53e` docs: add superseded revision markers to planning artifacts and ADRs (#125)

The revision markers commit (#125) already added the revision notes to ADR-000 and ADR-004 that this story will update.

### Peripheral Config Impact

| File | Impact |
|------|--------|
| `mkdocs.yml` (~line 169) | Add ADR-007 nav entry under ADR section — nav is manually listed, NOT glob-matched |
| `docs/adr/index.md` | Add ADR-007 row to manually curated ADR table |

No CI, pyproject.toml, or pre-commit changes needed.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/adr/ADR-007-architecture-migration.md` | NEW — formal decision record for architecture migration |
| `docs/adr/ADR-000-strategy-decorator-architecture.md` | MODIFIED — revision note updated to reference ADR-007 |
| `docs/adr/ADR-004-adk-schema-compatibility.md` | MODIFIED — revision note updated to reference ADR-007 |
| `mkdocs.yml` | MODIFIED — add ADR-007 nav entry (~line 169) |
| `docs/adr/index.md` | MODIFIED — add ADR-007 row to table |

### Project Structure Notes

- New file: `docs/adr/ADR-007-architecture-migration.md` — follows naming convention of existing ADRs
- Modified files: `docs/adr/ADR-000-*.md`, `docs/adr/ADR-004-*.md`, `mkdocs.yml`, `docs/adr/index.md`
- No changes to `src/adk_secure_sessions/`; one test file modified (`tests/unit/test_serialization.py`)
- Alignment with unified project structure confirmed — all ADRs live in `docs/adr/`

### References

- [Source: _bmad-output/implementation-artifacts/7-1-spike-findings.md — GO decision with evidence]
- [Source: _bmad-output/implementation-artifacts/7-1-typedecorator-wrapping-spike.md — Story 7.1 dev notes and learnings]
- [Source: docs/adr/ADR-000-strategy-decorator-architecture.md — Original architecture decision and revision note]
- [Source: docs/adr/ADR-004-adk-schema-compatibility.md — Schema compatibility strategy and revision note]
- [Source: docs/adr/index.md — Manually curated ADR index table]
- [Source: mkdocs.yml:162-169 — Manually listed ADR nav section]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 7, Story 7.2 acceptance criteria]
- [Source: Issue #118 — Documentation honesty audit that prompted Epic 7]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only) — 22 diagnostics all pre-existing
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 182 tests pass, 99.68% coverage
- [x] `pre-commit run --all-files` -- 9/9 hooks pass

## Code Review

- **Reviewer:** Code Review Workflow (Claude Opus 4.6)
- **Outcome:** Changes Requested → Fixed

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| M1 | Medium | "~800 lines of raw SQL" inconsistent phrasing (lines 95, 117) | Fixed — aligned to "~800-line raw aiosqlite implementation" |
| M2 | Medium | `serialization.py` listed as fully "kept" is imprecise | Fixed — replaced with specific envelope helpers and constants |
| M3 | Medium | AC5 content (aiosqlite removal, Epic 4 supersession) missing from Consequences | Fixed — added dependency simplification bullet + Epic 4 supersession sentence |
| L1 | Low | "replacing our manual concurrency handling" — no such code exists | Fixed — changed to "available out of the box" |
| L2 | Low | ADR-000 "Simple Inheritance" rejection lacks ADR-007 cross-reference | Fixed — added parenthetical referencing ADR-007 TypeDecorator approach |
| L3 | Low | Story Dev Notes line 200 contradicts File List (test file modified) | Fixed — updated to reflect test file modification |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-05 | Story created by create-story workflow |
| 2026-03-05 | Party mode review: 7 adjustments applied (mkdocs nav task, index.md task, peripheral config fix, doc impact table fix, AC-to-Test verification guidance, ADR-000 status directive, TEA cross-cutting reference) |
| 2026-03-05 | Party mode consensus: cross-cutting test = tampered envelope header bytes (P3-2) — security-critical, small footprint, durable across migration |
| 2026-03-05 | Implementation complete: ADR-007 created, ADR-000/ADR-004 revision notes updated, mkdocs nav + index updated, T037 cross-cutting test added (182 tests, 99.68% coverage) |
| 2026-03-05 | Code review: 3 MEDIUM + 3 LOW findings (party mode consensus). All 6 fixed — claim precision, AC5 content placement, ADR-000 cross-ref. 182 tests pass, 9/9 hooks pass. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — clean execution, all quality gates passed on first run.

### Completion Notes List

1. Created `docs/adr/ADR-007-architecture-migration.md` — formal ADR documenting the migration from direct BaseSessionService to DatabaseSessionService wrapping via TypeDecorator
2. ADR-007 synthesizes evidence from spike findings (7-1), ADR-000 (V0 rejection context), and Issue #118
3. ADR-000 revision note updated: references ADR-007 by number, states "Direct Implementation" is superseded, "Strategy" remains valid
4. ADR-004 revision note updated: "may change" → "changes per ADR-007", schema ownership recontextualized
5. `mkdocs.yml` nav entry added for ADR-007 (line 170, after ADR-006)
6. `docs/adr/index.md` table updated with ADR-007 row
7. T037 added: `test_tampered_envelope_header_raises` — verifies tampered version byte and backend_id byte both raise `DecryptionError` with appropriate error messages

### File List

| File | Action |
|------|--------|
| `docs/adr/ADR-007-architecture-migration.md` | Created — formal ADR for architecture migration decision |
| `docs/adr/ADR-000-strategy-decorator-architecture.md` | Modified — revision note updated to reference ADR-007 |
| `docs/adr/ADR-004-adk-schema-compatibility.md` | Modified — revision note updated to reference ADR-007 |
| `docs/adr/index.md` | Modified — added ADR-007 row to table |
| `mkdocs.yml` | Modified — added ADR-007 nav entry |
| `tests/unit/test_serialization.py` | Modified — added T037 tampered envelope header test |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified — 7-2 status: ready-for-dev → in-progress → review |
| `_bmad-output/implementation-artifacts/7-2-adr-architecture-migration-decision.md` | Modified — tasks marked done, quality gates checked, completion notes |
