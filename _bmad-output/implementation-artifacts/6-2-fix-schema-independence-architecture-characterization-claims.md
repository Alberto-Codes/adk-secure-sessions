# Story 6.2: Fix Schema Independence & Architecture Characterization Claims

Status: done
Branch: feat/docs-6-2-fix-schema-claims
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/121

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **contributor reading project conventions or planning docs**,
I want **accurate descriptions of the schema relationship with ADK and what the library actually is**,
so that **I don't build on false assumptions about schema independence, table counts, or the library being "just an encryption layer"**.

## Acceptance Criteria

1. **CLAUDE.md line 11** — Fix "own schema independent of ADK" to accurately describe schema as derived from ADK's Session/Event data model with encrypted column types, managed via raw aiosqlite (FR-NEW-2)

2. **.claude/rules/conventions.md "Own Our Schema" section** — Update to:
   - List all 4 tables: `app_states`, `user_states`, `sessions`, `events` (not just 2)
   - Describe schema relationship honestly: derived from ADK's public model contract; operationally independent (own tables, own migrations) but structurally coupled to ADK's data model
   - Preserve "raw parametrized SQL via aiosqlite" as accurate (FR-NEW-2)

3. **_bmad-output/project-context.md line 73** — Update table list from `(sessions, events)` to all 4: `app_states`, `user_states`, `sessions`, `events` (FR-NEW-2)

4. **_bmad-output/planning-artifacts/prd.md line 334** — Update table list and description from "independent of ADK's internal schema" with only 2 tables to list all 4 tables with honest framing about schema relationship (FR-NEW-2)

5. **docs/ROADMAP.md line 5** — Change "missing encryption layer" to "encrypted session persistence" or equivalent accurate characterization (FR-NEW-1)

6. **_bmad-output/planning-artifacts/prd.md line 372** — Change "encryption layer" to accurate characterization consistent with the library being a full session service, not just a layer (FR-NEW-1)

7. **docs/project-overview.md line 28** — Reclassify SQLAlchemy row as transitive dependency via google-adk (not a direct dependency; we use raw aiosqlite). Update category from "ORM" to "ORM (transitive)" and purpose to clarify it's pulled in by ADK, not used directly.

8. **docs/project-overview.md lines 62-68** — Reframe schema description from "independent of ADK internals" to "schema derived from ADK's Session/Event data model with encrypted column types; operationally independent (own tables, migrations, encryption) but structurally coupled to ADK's public model contract" (verify 4-table list is already correct here — it is)

9. **docs/contributing/docstring-templates.md line 51** — Update template language from "Encrypted drop-in replacement for ADK's DatabaseSessionService" to "Encrypted session service implementing ``BaseSessionService`` with field-level encryption". Also fix line 54: change `db_url (str): SQLAlchemy database URL` to `db_url (str): Database connection URL`

## Tasks / Subtasks

- [x] Task 1: Fix CLAUDE.md schema description (AC: 1)
  - [x] Change "own schema independent of ADK" to "schema derived from ADK's data model with encrypted columns, managed via raw aiosqlite"
- [x] Task 2: Fix conventions.md "Own Our Schema" section (AC: 2)
  - [x] Update table list to all 4: `app_states`, `user_states`, `sessions`, `events`
  - [x] Reframe as "derived from ADK's public model contract; operationally independent but structurally coupled"
  - [x] Keep "raw parametrized SQL via aiosqlite, not SQLAlchemy ORM" (accurate)
- [x] Task 3: Fix project-context.md table list (AC: 3)
  - [x] Update line 73 to list all 4 tables
  - [x] Reframe as "derived from ADK's data model, operationally independent"
- [x] Task 4: Fix prd.md schema description (AC: 4)
  - [x] Update line 334 table list from 2 to 4 tables
  - [x] Reframe "independent of ADK's internal schema" with honest "derived from" language
- [x] Task 5: Fix ROADMAP.md "encryption layer" characterization (AC: 5)
  - [x] Change "missing encryption layer" to "encrypted session persistence"
- [x] Task 6: Fix prd.md "encryption layer" characterization (AC: 6)
  - [x] Change "encryption layer" to "session encryption architecture" at line 372
- [x] Task 7: Fix project-overview.md SQLAlchemy row (AC: 7)
  - [x] Reclassify as transitive dependency via google-adk
  - [x] Update category to "ORM (transitive)" and purpose to "Transitive via google-adk — not used directly; all DB access uses raw aiosqlite"
- [x] Task 8: Fix project-overview.md schema description (AC: 8)
  - [x] Reframe "independent of ADK internals" at line 62 to "derived from ADK's data model, operationally independent"
  - [x] Verify 4-table list is correct (it already lists all 4)
- [x] Task 9: Fix docstring-templates.md template language (AC: 9)
  - [x] Change line 51: "Encrypted drop-in replacement for ADK's DatabaseSessionService" to "Encrypted session service implementing ``BaseSessionService`` with field-level encryption"
  - [x] Change line 54: `db_url (str): SQLAlchemy database URL` to `db_url (str): Database connection URL`
- [x] Task 10: Run `pre-commit run --all-files` to verify all hooks pass
- [x] Task 11: Run `git diff --stat` to confirm only doc/config files changed

### Cross-Cutting Test Maturity (Standing Task)

<!-- Every story includes one small-footprint, high-risk-area test addition.
     This is brownfield hardening -- pick a gap in an area NOT related to the
     story scope so the safety net grows steadily across epics. -->

- [x] Identify one high-risk area lacking test coverage (outside story scope)
- [x] Add test(s) -- small footprint, meaningful assertion
- [x] Verify new test(s) pass in CI

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1 | Manual: verified CLAUDE.md line 11 uses "schema derived from ADK's data model with encrypted columns" | pass |
| 2 | Manual: verified conventions.md lists 4 tables, "derived from ADK's Session/Event data model contract" framing | pass |
| 3 | Manual: verified project-context.md lists all 4 tables with "derived from" framing | pass |
| 4 | Manual: verified prd.md line 334 lists 4 tables, "Schema derived from ADK's data model contract" | pass |
| 5 | Manual: verified ROADMAP.md line 5 says "encrypted session persistence" | pass |
| 6 | Manual: verified prd.md line 372 says "session encryption architecture" | pass |
| 7 | Manual: verified project-overview.md SQLAlchemy row says "ORM (transitive)" with "Transitive via google-adk" | pass |
| 8 | Manual: verified project-overview.md line 62 reframed to "derived from ADK's Session/Event data model, operationally independent" | pass |
| 9 | Manual: verified docstring-templates.md line 51 and 54 updated | pass |

## Dev Notes

### Replacement Language Table (Audience-Appropriate)

| File | Audience | Schema Framing |
|------|----------|---------------|
| `CLAUDE.md` | AI agents (terse) | "schema derived from ADK's data model with encrypted columns" |
| `.claude/rules/conventions.md` | Contributors (precise) | "Schema derived from ADK's Session/Event data model contract with encrypted column types. Operationally independent — own tables, own migrations, own encryption — but structurally coupled to ADK's public model contract." |
| `_bmad-output/project-context.md` | AI agents (terse) | "Schema derived from ADK's data model" + 4-table list |
| `_bmad-output/planning-artifacts/prd.md` | Planning (factual) | "Schema derived from ADK's data model contract" + 4-table list |
| `docs/project-overview.md` | Docs visitors (explanatory) | "Schema derived from ADK's Session/Event data model (operationally independent, encrypted column types)" |
| `docs/ROADMAP.md` | Prospective users (accessible) | "encrypted session persistence" (not "encryption layer") |
| `docs/contributing/docstring-templates.md` | Contributors (template) | "Encrypted session service implementing BaseSessionService" |

### Exact Text to Replace

**CLAUDE.md line 11:**
- Current: `- SQLite via aiosqlite (async), own schema independent of ADK (006-encrypted-session-service)`
- Target: `- SQLite via aiosqlite (async), schema derived from ADK's data model with encrypted columns (006-encrypted-session-service)`

**conventions.md lines 35-39:**
- Current:
  ```
  ## Own Our Schema

  We manage our own SQLite tables (`sessions`, `events`), independent of ADK's internal schema. All database access uses raw parametrized SQL via aiosqlite, not SQLAlchemy ORM.

  This gives us full control over the storage layer -- encryption, indexing, and migration -- without coupling to ADK's internal database decisions.
  ```
- Target: List all 4 tables (`app_states`, `user_states`, `sessions`, `events`). Reframe as "Schema derived from ADK's Session/Event data model contract with encrypted column types. Operationally independent — own tables, own migrations, own encryption — but structurally coupled to ADK's public model contract." Keep aiosqlite statement, keep ADR-004 reference.

**project-context.md line 73:**
- Current: `- **Own schema, independent of ADK** — we manage our own SQLite tables (`sessions`, `events`), not ADK's internal schema`
- Target: `- **Schema derived from ADK's data model** — we manage our own SQLite tables (`app_states`, `user_states`, `sessions`, `events`) with encrypted column types, operationally independent of ADK's internal tables`

**prd.md line 334:**
- Current: `**Own schema, no coupling.** The library manages its own SQLite tables (`sessions`, `events`), independent of ADK's internal schema.`
- Target: List all 4 tables, reframe as "Schema derived from ADK's data model contract, operationally independent"

**ROADMAP.md line 5:**
- Current: `adk-secure-sessions provides the missing encryption layer for Google ADK's session storage.`
- Target: Replace "missing encryption layer" with "encrypted session persistence"

**prd.md line 372:**
- Current: `...it trades 2 bytes of overhead per record for a fundamentally more capable encryption layer.`
- Target: Replace "encryption layer" with "session encryption architecture"

**project-overview.md line 28:**
- Current: `| ORM | SQLAlchemy | >=2.0.0 | Listed as dependency (raw SQL via aiosqlite in practice) |`
- Target: `| ORM (transitive) | SQLAlchemy | >=2.0.0 | Transitive via google-adk — not used directly; all DB access uses raw aiosqlite |`

**project-overview.md line 62:**
- Current: `Own SQLite schema (independent of ADK internals):`
- Target: `Own SQLite schema (derived from ADK's Session/Event data model, operationally independent with encrypted column types):`

**docstring-templates.md line 51:**
- Current: `"""Encrypted drop-in replacement for ADK's DatabaseSessionService.`
- Target: `"""Encrypted session service implementing ``BaseSessionService`` with field-level encryption.`

**docstring-templates.md line 54:**
- Current: `db_url (str): SQLAlchemy database URL.`
- Target: `db_url (str): Database connection URL.`

### Guardrails

- **No code logic changes** — only documentation, conventions, and planning artifact text. If `git diff --stat` shows any `.py` source file under `src/`, something went wrong.
- **Do NOT touch these files** (verified correct in Story 6.1): `docs/faq.md`, `docs/adr/ADR-002-async-first.md`, `tests/integration/test_adk_runner.py`

### Previous Story Intelligence (6.1)

Story 6.1 established these patterns for Story 6.2 to follow:

1. **Context-appropriate language** — Different files serve different audiences. PyPI is short, README medium, docstrings technical, docs explanatory. Use appropriate tone for each file.
2. **Preservation of accurate claims** — 6.1 verified that `docs/faq.md` (drop-in backend = encryption backends), `docs/adr/ADR-002-async-first.md` ("Direct drop-in" = async integration), and `tests/integration/test_adk_runner.py` ("drop-in" = BaseSessionService contract) are correct and must NOT be changed.
3. **Grep verification** — After changes, grep for "drop-in replacement" and "independent of ADK" to ensure no stale instances remain in changed files.
4. **Code review finding M1** — Avoid redundant "implements BaseSessionService" repetition; vary language across files.

### Peripheral Config Impact

No peripheral config impact — this story changes only documentation, conventions, and planning artifact text. No CI, no pyproject.toml, no mkdocs.yml changes needed (unless SQLAlchemy dependency needs removal from pyproject.toml, which would be AC 7 scope).

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| docs/ROADMAP.md | "encryption layer" -> "encrypted session persistence" |
| docs/project-overview.md | SQLAlchemy row fix, schema description reframe |
| docs/contributing/docstring-templates.md | "drop-in replacement" -> BaseSessionService language |
| CLAUDE.md | Schema description correction |
| .claude/rules/conventions.md | "Own Our Schema" section rewrite |

### Project Structure Notes

- All changes are documentation/convention text — no source tree or module changes
- Files span three categories: project rules (CLAUDE.md, conventions.md), user-facing docs (ROADMAP.md, project-overview.md, docstring-templates.md), planning artifacts (prd.md, project-context.md)
- Planning artifacts are in `_bmad-output/` and are not published to the docs site

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 6, Story 6.2 acceptance criteria]
- [Source: _bmad-output/implementation-artifacts/6-1-fix-user-facing-drop-in-replacement-claims.md — Previous story patterns]
- [Source: src/adk_secure_sessions/services/encrypted_session.py:67-107 — Ground truth: 4 CREATE TABLE statements]
- [Source: docs/adr/ADR-004-adk-schema-compatibility.md — Schema design rationale]
- [Source: Issue #118 — Documentation honesty audit findings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage (99%)
- [x] `pre-commit run --all-files` -- all hooks pass

## Code Review

- **Reviewer:** Code Review Workflow (adversarial)
- **Outcome:** Changes Requested → Fixed

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| M1 | MEDIUM | `.specify/memory/constitution.md:52` stale "independent of ADK" in governance principle | Fixed — added "derived from ADK's public model contract with encrypted column types, operationally independent" |
| M2 | MEDIUM | Completion Notes grep audit incomplete — missed `.specify/memory/constitution.md` | Fixed — added constitution.md to grep audit list |
| L1 | LOW | `prd.md:252` "encryption layer" in Kenji persona narrative | Dismissed — persona narrative context, not library characterization |
| L2 | LOW | Unreachable dead code (line 723 temp: discard) not tracked as issue | Dismissed — documented in Dev Notes, sufficient for 3 lines of defensive code |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes (178 passed)
- [x] Quality gates re-verified (ruff clean)

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-04 | Story created by create-story workflow |
| 2026-03-04 | Implementation complete — all 9 ACs addressed, pre-commit passes, cross-cutting test added |
| 2026-03-04 | Code review fixes — M1: fixed stale "independent of ADK" in `.specify/memory/constitution.md:52`; M2: updated Completion Notes grep audit; L1/L2 dismissed (persona narrative + documented dead code) |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging needed.

### Completion Notes List

- Updated 7 files across 3 categories (project rules, user-facing docs, planning artifacts)
- All 9 ACs satisfied: schema descriptions reframed from "independent of ADK" to "derived from ADK's data model, operationally independent"
- Table counts corrected from 2 to 4 everywhere (`app_states`, `user_states`, `sessions`, `events`)
- "encryption layer" replaced with "encrypted session persistence" (ROADMAP) and "session encryption architecture" (PRD)
- SQLAlchemy reclassified as transitive dependency via google-adk
- Docstring template updated from "drop-in replacement" to "BaseSessionService with field-level encryption"
- Grep verification: no stale "drop-in replacement" in changed files; remaining "independent of ADK" instances are in ADR-004 (accurate), CHANGELOG (historical), `.specify/memory/constitution.md` (governance — fixed in review), and reference material (appropriate)
- Cross-cutting test: added `test_round_trip_empty_dict` to serialization tests — verifies empty dict survives full encrypt/decrypt cycle
- Discovery: line 723 (`temp:` key discard in `_extract_and_persist_state_delta`) is unreachable because `_trim_temp_delta_state` removes temp keys before this method is called — defensive dead code

### File List

- CLAUDE.md (modified — schema description fix)
- .claude/rules/conventions.md (modified — "Own Our Schema" section rewrite)
- _bmad-output/project-context.md (modified — table list and schema framing)
- _bmad-output/planning-artifacts/prd.md (modified — schema description + "encryption layer" fix)
- docs/ROADMAP.md (modified — "encryption layer" to "encrypted session persistence")
- docs/project-overview.md (modified — SQLAlchemy row + schema description)
- docs/contributing/docstring-templates.md (modified — "drop-in replacement" + db_url description)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — story status)
- _bmad-output/implementation-artifacts/6-2-fix-schema-independence-architecture-characterization-claims.md (modified — story file)
- tests/unit/test_serialization.py (modified — added empty dict round-trip test)
- .specify/memory/constitution.md (modified — fixed stale "independent of ADK" in governance principle)
