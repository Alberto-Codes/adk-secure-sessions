# Story 7.6: Revise Epic 4 Scope & Roadmap

Status: done
Branch: feat/docs-7-6-revise-epic-4-scope-roadmap
GitHub Issue:

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **contributor reading the backlog or roadmap**,
I want **Epic 4's superseded stories formally closed and the roadmap updated to reflect that PostgreSQL comes for free**,
So that **I don't waste time planning or implementing stories that have been superseded by Epic 7**.

## Acceptance Criteria

1. **Given** Epic 4 Stories 4.1 (Persistence Protocol), 4.2 (Encryption Coordinator), and 4.3 (PostgreSQL Backend) are superseded by Epic 7
   **When** `_bmad-output/planning-artifacts/epics.md` is updated
   **Then** Stories 4.1, 4.2, and 4.3 have `[SUPERSEDED by Epic 7]` markers (already present from Epic 6)
   **And** Epic 4's goal statement is revised to reflect reduced scope: key rotation, backend docs, ops guide, Python version tracking
   **And** Epic 4's FR coverage is updated: FR49 remapped to Epic 7

2. **Given** `docs/ROADMAP.md` describes Phase 3 capabilities
   **When** it is updated
   **Then** PostgreSQL support is listed as delivered by Epic 7 (not Epic 4)
   **And** the Phase 3 scope accurately reflects: AES-256-GCM (Epic 3) + architecture migration with multi-DB (Epic 7) + key rotation and docs (Epic 4 remainder)

3. **And** any sprint plans or status documents referencing Epic 4 Stories 4.1-4.3 are updated or annotated

## Tasks / Subtasks

- [x] Task 1: Update Epic 4 goal statement in `epics.md` (AC: #1)
  - [x] 1.1 Revise Epic 4 title from "PostgreSQL Persistence & Key Rotation" to reflect reduced scope (e.g., "Key Rotation & Operational Documentation")
  - [x] 1.2 Rewrite Epic 4 goal paragraph to focus on remaining stories: key rotation (4.4), backend authoring docs (4.5), ops guide (4.6), Python version tracking (4.7)
  - [x] 1.3 Update FR coverage: remap FR49 (PostgreSQL) from Epic 4 to Epic 7; verify no other FRs need remapping

- [x] Task 2: Verify superseded markers in `epics.md` (AC: #1)
  - [x] 2.1 Confirm Stories 4.1, 4.2, 4.3 headers already have `[SUPERSEDED by Epic 7]` markers (added in Epic 6 Story 6.3)
  - [x] 2.2 If missing, add the markers; if present, verify consistency with sprint-status.yaml

- [x] Task 3: Update `docs/ROADMAP.md` Phase 3 section (AC: #2)
  - [x] 3.1 Verify PostgreSQL is already listed as delivered via Epic 7 (Story 7.5 added this -- confirm) — no changes needed
  - [x] 3.2 Ensure Phase 3 scope summary accurately reflects: AES-256-GCM + key derivation (Epic 3) + multi-DB via DatabaseSessionService wrapper (Epic 7, delivered) + key rotation + docs (Epic 4 remainder) — no changes needed, already accurate from Story 7.5
  - [x] 3.3 Add or update any Phase 3 timeline or status notes to reflect Epic 7 completion — no changes needed, Phase 3 checklist accurately shows delivered vs. pending items

- [x] Task 4: Update sprint-status.yaml annotations (AC: #3)
  - [x] 4.1 Verify Epic 4 stories 4-1, 4-2, 4-3 already show `superseded` status (confirmed present)
  - [x] 4.2 Verify `# [SUPERSEDED by Epic 7]` comments are present on lines 82-84

- [x] Task 5: Quality verification (AC: #1, #2, #3)
  - [x] 5.1 Run `pre-commit run --all-files` -- all 9 hooks pass
  - [x] 5.2 Verify no code logic changes -- only planning artifacts and documentation
  - [x] 5.3 Run `uv run pytest` to confirm no regressions (all 171 tests pass via pre-commit)

### Cross-Cutting Test Maturity (Standing Task)

<!-- Sourced from test-review.md recommendations. The create-story workflow
     picks the next unaddressed item and assigns it here. -->

**Test Review Item**: Extract shared service fixture in integration tests
**Severity**: P2 (Medium)
**Location**: `tests/integration/test_adk_crud.py`, `test_adk_encryption.py`, `test_adk_conformance.py` (~20 occurrences total)

The pattern `async with EncryptedSessionService(db_url=..., backend=...) as service:` appears ~20 times across integration test files. The `conftest.py` already provides an `encrypted_service` fixture -- many of these could use it instead. The `test_conformance.py` correctly uses dedicated fixtures rather than duplicating inline instantiation.

**Important**: Preserve inline service creation for tests that need custom configuration (wrong-key tests, shared-DB tests, custom db_url). Only extract tests that use the default config pattern.

- [x] Implement the test review recommendation above
- [x] Verify new/changed test(s) pass in CI
- [x] Mark item as done in `_bmad-output/test-artifacts/test-review.md`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | Manual review: Epic 4 title revised, goal rewritten, FR49 remap verified, superseded markers confirmed | pass |
| 2    | Manual review + docvet hook: ROADMAP.md verified accurate (no changes needed — Story 7.5 already updated) | pass |
| 3    | Manual review: sprint-status.yaml annotations verified (superseded status + comments present) | pass |

## Dev Notes

This is a **docs/planning-only story** -- no source code changes (except the cross-cutting test item). The scope is updating planning artifacts (`epics.md`, `sprint-status.yaml`) and documentation (`docs/ROADMAP.md`) to reflect that Epic 7 superseded Epic 4 Stories 4.1-4.3.

**AC-to-Test mapping**: For docs ACs, use "Manual review + docvet hook" (same pattern as Story 7-5). For the cross-cutting test item, list actual test names.

### Architecture Context

Epic 7 replaced the planned Epic 4 persistence extraction (4.1), coordinator extraction (4.2), and PostgreSQL backend (4.3) with a simpler approach: wrapping ADK's `DatabaseSessionService` via SQLAlchemy `TypeDecorator`. This delivered multi-database support (SQLite, PostgreSQL, MySQL, MariaDB) as a side effect of the architecture migration, eliminating the need for separate persistence protocol extraction.

**What Epic 4 retains**:
- Story 4.4: Zero-downtime key rotation (still needed -- envelope-based, not affected by architecture change)
- Story 4.5: Backend authoring documentation (still needed -- custom backends not yet supported)
- Story 4.6: Operations guide (still needed -- key management, monitoring, troubleshooting)
- Story 4.7: Python version matrix tracking (still needed -- google-adk compatibility)

**FR remapping**:
- FR49 (PostgreSQL support) was originally assigned to Epic 4 Story 4.3. It is now delivered by Epic 7 (DatabaseSessionService wrapper provides PostgreSQL via `postgresql+asyncpg://` connection string).

### Pre-existing State

Much of this work was partially done in earlier stories:
- **Epic 6, Story 6.3** added `[SUPERSEDED by Epic 7]` markers to Stories 4.1-4.3 headers in `epics.md`
- **Story 7.5** updated `docs/ROADMAP.md` to list PostgreSQL as delivered and note superseded stories
- **Sprint-status.yaml** already has `superseded` status on 4-1, 4-2, 4-3

This story's primary remaining work is:
1. Revise Epic 4's **goal statement** and **title** (not yet done)
2. Update Epic 4's **FR coverage** mapping (not yet done)
3. Verify all existing annotations are consistent and complete

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `_bmad-output/planning-artifacts/epics.md` | Revise Epic 4 title, goal statement, FR coverage |
| `docs/ROADMAP.md` | Verify Phase 3 scope accuracy (mostly done in 7.5) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Verify annotations (already present) |

### Project Structure Notes

- Planning artifacts are under `_bmad-output/planning-artifacts/`
- Sprint tracking is in `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Documentation is under `docs/` and served via MkDocs
- No source code files (`src/`) should be modified

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4] -- current Epic 4 definition with revision note
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.6] -- AC definition
- [Source: docs/ROADMAP.md#Phase 3] -- current Phase 3 scope
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] -- current story statuses
- [Source: _bmad-output/implementation-artifacts/7-5-documentation-mkdocs-site-updates.md] -- previous story (docs updates, ROADMAP changes)
- [Source: _bmad-output/test-artifacts/test-review.md#Recommendation 2] -- cross-cutting test item

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all 171 tests pass, 98.51% coverage
- [x] `pre-commit run --all-files` -- all 9 hooks pass

## Code Review

- **Reviewer:** Claude Opus 4.6 (adversarial code review)
- **Outcome:** Approved with fixes

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| M1 | MEDIUM | test-review.md Next Steps still listed resolved item as backlog | Fixed — removed from backlog list |
| L1 | LOW | test-review.md file analysis table had stale line counts | Fixed — updated to 395/97 |
| L2 | LOW | test-review.md Violation Summary had stale duplication entry | Fixed — marked RESOLVED |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-06 | Revised Epic 4 title and goal statement in epics.md; verified superseded markers, FR49 remap, ROADMAP.md accuracy, sprint-status annotations |
| 2026-03-06 | Refactored 9 integration tests across test_adk_crud.py and test_adk_conformance.py to use shared encrypted_service fixture |
| 2026-03-06 | Updated test-review.md: marked Recommendation 2 as RESOLVED |
| 2026-03-06 | Code review: 0 HIGH, 1 MEDIUM, 2 LOW findings — all fixed in test-review.md bookkeeping |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None -- no issues encountered.

### Completion Notes List

- Revised Epic 4 title from "PostgreSQL Persistence & Key Rotation" to "Key Rotation & Operational Documentation" in both epics.md (heading + FR summary) and sprint-status.yaml (comment)
- Rewrote Epic 4 goal paragraph to focus on remaining stories: 4.4 (key rotation), 4.5 (backend docs), 4.6 (ops guide), 4.7 (Python version tracking)
- Verified FR49 already remapped to Epic 7; no other FRs need remapping
- Verified superseded markers on Stories 4.1-4.3 (already present from Epic 6 Story 6.3)
- Verified ROADMAP.md Phase 3 scope already accurate from Story 7.5 — no changes needed
- Verified sprint-status.yaml annotations already present — no changes needed
- Cross-cutting test maturity: refactored 9 tests to use `encrypted_service` fixture, preserving inline creation for tests needing custom config (wrong-key, raw DB reads)
- Updated test-review.md: marked Recommendation 2 as RESOLVED

### File List

- `_bmad-output/planning-artifacts/epics.md` — Revised Epic 4 title and goal statement (2 locations: heading at line 766, FR summary at line 269)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Updated Epic 4 comment to match new title; story status: ready-for-dev → in-progress → review
- `tests/integration/test_adk_crud.py` — Refactored 7 tests to use `encrypted_service` fixture (1 kept inline for raw DB read)
- `tests/integration/test_adk_conformance.py` — Refactored 2 tests to use `encrypted_service` fixture
- `_bmad-output/test-artifacts/test-review.md` — Marked Recommendation 2 as RESOLVED
- `_bmad-output/implementation-artifacts/7-6-revise-epic-4-scope-roadmap.md` — Story file (status, tasks, AC-to-Test, quality gates, dev record)
