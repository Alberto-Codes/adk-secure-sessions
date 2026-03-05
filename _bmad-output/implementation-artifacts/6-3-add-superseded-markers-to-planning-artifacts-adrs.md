# Story 6.3: Add Superseded Markers to Planning Artifacts & ADRs

Status: done
Branch: feat/docs-6-3-superseded-markers
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/124

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **future contributor or AI agent reading planning artifacts**,
I want **revision markers on documents that contain superseded architectural claims**,
so that **I don't build on stale assumptions while still understanding the historical context and reasoning**.

## Acceptance Criteria

1. **`_bmad-output/planning-artifacts/prd.md`** — Add revision marker near Epic 4 Stories 4.1-4.3 scope (now superseded by Epic 7) and near FR49 (PostgreSQL) noting it now maps to Epic 7 instead of Story 4.3. Format: `> **Revision Note (2026-03-04):** [What changed] that makes [specific claim] stale. See Issue #118 and Epic 7 for the architectural evolution path.` Original text is preserved — marker annotates, not replaces. Do NOT re-annotate claims already corrected by Story 6.2 (lines 334, 372 were rewritten, not preserved). (FR-NEW-3)

2. **`_bmad-output/planning-artifacts/architecture.md`** — Add revision marker noting that ADK V1 changed wrapping viability (Python-side state merging via `dict | delta`, no more `json_patch` SQL) and references Epic 7 as the evolution path. Original architecture description preserved as historical context. (FR-NEW-3)

3. **`_bmad-output/project-context.md`** — Fix line 23 SQLAlchemy characterization from "present in deps for async engine support" to "Transitive via google-adk — not used directly; all DB access uses raw aiosqlite" (consistent with project-overview.md correction in Story 6.2). No revision marker needed — schema claims on line 73 were already corrected in 6.2.

4. **`docs/adr/ADR-000-strategy-decorator-architecture.md`** — Add revision note to the "Why not wrap DatabaseSessionService" section acknowledging that ADK V1 changed this: `DatabaseSessionService` now merges state in Python (`dict | delta`), not SQL. Reference Epic 7 as the path to re-evaluate wrapping. Original rejection reasoning preserved (correct for V0). (FR-NEW-3)

5. **`docs/adr/ADR-004-adk-schema-compatibility.md`** — Add revision note clarifying the schema mirrors ADK's data model with encrypted column types, not a truly independent design. Reference Issue #118's finding about the schema relationship. (FR-NEW-3)

6. **`_bmad-output/planning-artifacts/epics.md`** — Add `[SUPERSEDED by Epic 7]` suffix to Story 4.1, 4.2, 4.3 headers and add revision note to the Epic 4 section body explaining scope reduction to Stories 4.4-4.7 only. (FR-NEW-3)

## Tasks / Subtasks

- [x] Task 1: Add revision markers to `prd.md` (AC: 1)
  - [x] Locate Epic 4 scope references (Stories 4.1-4.3) and add supersession marker
  - [x] Locate FR49 (PostgreSQL) mapping to Epic 4 Story 4.3 and add marker noting it now maps to Epic 7
  - [x] Do NOT annotate lines 334, 372 — those were already rewritten by Story 6.2
  - [x] Ensure markers follow the exact format: `> **Revision Note (2026-03-04):** ...`
- [x] Task 2: Add revision marker to `architecture.md` (AC: 2)
  - [x] Locate the direct-implementation architecture description (Decision 1 / schema section)
  - [x] Add revision note about ADK V0→V1 change: `json_patch` SQL → Python-side `dict | delta`
  - [x] Reference Epic 7 as the evolution path
- [x] Task 3: Fix `project-context.md` SQLAlchemy characterization (AC: 3)
  - [x] Change line 23 from "present in deps for async engine support, not for ORM usage" to "Transitive via google-adk — not used directly; all DB access uses raw aiosqlite"
  - [x] No revision marker needed — schema claims on line 73 already corrected in 6.2
- [x] Task 4: Add revision note to ADR-000 (AC: 4)
  - [x] Locate "Why not wrap DatabaseSessionService" or "Alternatives Considered" section
  - [x] Add revision note explaining V0→V1 ADK change that removes the interception barrier
  - [x] Reference Epic 7 as the path to re-evaluate wrapping (do NOT cite ADR-007 — it doesn't exist yet)
- [x] Task 5: Add revision note to ADR-004 (AC: 5)
  - [x] Locate "We own our schema" principle section
  - [x] Add revision note clarifying schema is derived from ADK's public model contract
  - [x] Note that this principle applies to current Phase 1-2; Epic 7 may change the schema ownership model
- [x] Task 6: Add superseded markers to `epics.md` (AC: 6)
  - [x] Add `[SUPERSEDED by Epic 7]` to Story 4.1, 4.2, 4.3 headers
  - [x] Add revision note to Epic 4 section body explaining scope reduction
  - [x] Verify existing "NOTE: Stories 4.1, 4.2, 4.3 are SUPERSEDED" comment is preserved
- [x] Task 7: Run `pre-commit run --all-files` to verify all hooks pass
- [x] Task 8: Run `git diff --stat` to confirm only doc/planning files changed — no `.py` source files under `src/`
- [x] Task 9: Grep verification for marker format consistency
  - [x] `grep -r "Revision Note" docs/ _bmad-output/` — all markers use identical format
  - [x] Verify all markers reference Issue #118 and/or Epic 7

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
| 1 | Manual: verify prd.md revision markers for Epic 4 scope (Phase 3 section) + FR49 (line 792) | pass |
| 2 | Manual: verify architecture.md revision marker after service decomposition section (line 96) | pass |
| 3 | Manual: verify project-context.md line 23 SQLAlchemy fix — now reads "Transitive via google-adk" | pass |
| 4 | Manual: verify ADR-000 revision note after "Why not wrap" section (line 51) | pass |
| 5 | Manual: verify ADR-004 revision note after "We own our schema" principle (line 28) | pass |
| 6 | Manual: verify epics.md Story 4.1-4.3 headers have [SUPERSEDED] + Epic 4 revision note (line 770) | pass |

## Dev Notes

### Marker Format Specification (MUST FOLLOW EXACTLY)

All revision markers use this exact format — no deviations:

```markdown
> **Revision Note (2026-03-04):** [What changed] that makes [specific claim] stale. See Issue #118 and Epic 7 for the architectural evolution path.
```

Rules:
- Date: `2026-03-04` (ISO 8601, this epic's date)
- Always reference Issue #118 (the documentation honesty audit finding)
- Reference Epic 7 when the marker relates to the architecture migration
- Markdown blockquote prefix `> ` so the note visually stands out
- **NEVER delete original text** — markers annotate history, they don't rewrite it
- Place marker immediately after or below the relevant claim

### Key Technical Context: Why Wrapping Became Viable

**ADK V0** (original): `DatabaseSessionService.append_event` used SQL-side state merging via `json_patch` — no interception points for encryption. Wrapping was correctly rejected in ADR-000.

**ADK V1** (current): State merging changed to Python-side `dict | delta` operation. This removed the SQL interception barrier, making `TypeDecorator`-based wrapping viable. Epic 7 explores this path.

This is the core "what changed" narrative for ADR-000 and architecture.md markers.

### Files to Modify (Exhaustive List)

| File | What to Add | Location |
|------|-------------|----------|
| `_bmad-output/planning-artifacts/prd.md` | Revision markers for Epic 4 scope supersession + FR49 remapping | Epic 4 references and FR49 |
| `_bmad-output/planning-artifacts/architecture.md` | Revision marker on direct-impl architecture | Decision 1 / schema section |
| `_bmad-output/project-context.md` | Fix SQLAlchemy line 23 characterization (no revision marker) | Technology Stack section, line 23 |
| `docs/adr/ADR-000-strategy-decorator-architecture.md` | Revision note on "Why not wrap" | Alternatives Considered section |
| `docs/adr/ADR-004-adk-schema-compatibility.md` | Revision note on "own schema" | Principles section |
| `_bmad-output/planning-artifacts/epics.md` | `[SUPERSEDED]` on 4.1-4.3 headers + Epic 4 revision note | Story headers + Epic 4 body |

### Files NOT to Modify (Verified Correct)

- `docs/adr/ADR-001-protocol-based-interfaces.md` — Encryption protocol unaffected by persistence migration
- `docs/adr/ADR-002-async-first.md` — Async design unaffected
- `docs/adr/ADR-003-field-level-encryption.md` — Encryption strategy unaffected
- `docs/adr/ADR-005-exception-hierarchy.md` — Exception taxonomy unaffected
- `docs/adr/ADR-006-configuration-error.md` — ConfigurationError unaffected
- Sprint-status.yaml — already has `superseded` status on 4-1, 4-2, 4-3
- Stories 4.4-4.7 — not superseded (key rotation, docs, ops, version tracking)

### Guardrails

- **No code logic changes** — only documentation and planning artifact text. If `git diff --stat` shows any `.py` source file under `src/`, something went wrong.
- **Do NOT rewrite original content** — only ADD revision markers via blockquote
- **Do NOT touch these files** (verified unaffected): ADR-001 through ADR-003, ADR-005, ADR-006
- **Do NOT change sprint-status.yaml** — superseded markers already in place

### Previous Story Intelligence (6.2)

Story 6.2 established these patterns for Story 6.3 to follow:

1. **Context-appropriate language** — Different files serve different audiences. Planning artifacts are for AI agents/contributors; ADRs are for architects; docs are for external users. Use appropriate tone.
2. **Grep verification** — After changes, grep for marker format consistency across all modified files.
3. **Governance files can hide stale claims** — Story 6.2 review found `.specify/memory/constitution.md` had stale language. Cast a wider net when auditing.
4. **Persona narrative ≠ library characterization** — Kenji's persona in prd.md says "encryption layer" (persona voice, not a library claim). Don't add markers to persona narratives.
5. **Preservation over rewriting** — Story 6.2 corrected text; Story 6.3 annotates text. Different approach: 6.3 adds markers alongside original text, never replacing it.

### Peripheral Config Impact

No peripheral config impact — this story changes only documentation, planning artifacts, and ADR text. No CI, no pyproject.toml, no mkdocs.yml changes needed.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| docs/adr/ADR-000-strategy-decorator-architecture.md | Add revision note to "Why not wrap" section |
| docs/adr/ADR-004-adk-schema-compatibility.md | Add revision note to "own schema" principle |

### Project Structure Notes

- All changes are documentation/planning artifact annotations — no source tree or module changes
- Files span two categories: ADRs (docs/adr/) and planning artifacts (_bmad-output/planning-artifacts/, _bmad-output/project-context.md)
- Planning artifacts are NOT published to the docs site; ADRs ARE published

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 6, Story 6.3 acceptance criteria]
- [Source: _bmad-output/implementation-artifacts/6-2-fix-schema-independence-architecture-characterization-claims.md — Previous story patterns and learnings]
- [Source: docs/adr/ADR-000-strategy-decorator-architecture.md — "Why not wrap DatabaseSessionService" section]
- [Source: docs/adr/ADR-004-adk-schema-compatibility.md — "We own our schema" principle]
- [Source: Issue #118 — Documentation honesty audit findings]
- [Source: Sprint-status.yaml — Stories 4-1, 4-2, 4-3 already marked superseded]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 180 passed, 99.68% coverage
- [x] `pre-commit run --all-files` -- all 9 hooks pass

## Code Review

- **Reviewer:** Code Review Workflow (adversarial)
- **Outcome:** Changes Requested — 2 fixes applied

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| H1 | HIGH | prd.md revision marker inserted between table rows breaks table rendering (GFM spec: tables terminate at blank lines/block elements) | Fixed — relocated marker to after table close |
| M1 | MEDIUM | prd.md revision marker inserted between FR list items breaks list continuity | Fixed — relocated marker to after FR55 |
| L1 | LOW | Commit scope `docs(adr)` too narrow — only 2 of 9 files are ADRs | Deferred — fix at PR title (squash-merge subject overrides) |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-04 | Story created by create-story workflow |
| 2026-03-04 | Implementation complete — 5 revision markers added, 1 characterization fix, 2 cross-cutting tests added |
| 2026-03-04 | Code review: 1 HIGH + 1 MEDIUM fixed (prd.md marker placement broke table and list rendering), 1 LOW deferred to PR title |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- All 5 revision markers follow identical format: `> **Revision Note (2026-03-04):** ...` with Issue #118 and Epic 7 references
- Lines 334, 372 in prd.md were correctly left untouched (already rewritten by Story 6.2)
- epics.md Story 4.1-4.3 headers already had `[SUPERSEDED by Epic 7]` — added formal revision note to Epic 4 body section
- project-context.md SQLAlchemy characterization fixed from "present in deps for async engine support" to "Transitive via google-adk"
- Cross-cutting: Added 2 tests for backend encryption failure propagation in `test_serialization.py` (T034, T035) — previously untested error path
- No `.py` source files under `src/` were modified — confirmed via `git diff --stat`

### File List

- `_bmad-output/planning-artifacts/prd.md` (modified — 2 revision markers added)
- `_bmad-output/planning-artifacts/architecture.md` (modified — 1 revision marker added)
- `_bmad-output/planning-artifacts/epics.md` (modified — 1 revision marker added to Epic 4 body)
- `_bmad-output/project-context.md` (modified — SQLAlchemy characterization fix)
- `docs/adr/ADR-000-strategy-decorator-architecture.md` (modified — 1 revision marker added)
- `docs/adr/ADR-004-adk-schema-compatibility.md` (modified — 1 revision marker added)
- `tests/unit/test_serialization.py` (modified — added `_BadEncryptBackend` + 2 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updates)
- `_bmad-output/implementation-artifacts/6-3-add-superseded-markers-to-planning-artifacts-adrs.md` (modified — story tracking)
