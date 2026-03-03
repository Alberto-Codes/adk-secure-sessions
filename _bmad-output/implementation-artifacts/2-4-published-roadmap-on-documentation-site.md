# Story 2.4: Published Roadmap on Documentation Site

Status: review
Branch: feat/docs-2-4-roadmap-update
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/93

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer or compliance reviewer**,
I want **a published roadmap on the docs site showing phase timeline and planned capabilities**,
so that **I can evaluate the project's trajectory and plan my adoption timing (e.g., waiting for AES-256-GCM)**.

## Acceptance Criteria

1. **Given** `docs/ROADMAP.md` exists with phase definitions
   **When** the roadmap is included in the MkDocs site navigation
   **Then** it displays the 4-phase timeline (Core, Ship, Expand, Enterprise) (FR56)
   **And** it lists planned capabilities per phase
   **And** it includes the backend upgrade schedule (Fernet now, AES-256-GCM in Phase 3, KMS in Phase 4)
   **And** the content is verified against the PRD's phase definitions for consistency
   **And** docvet pre-commit hook passes on any modified roadmap files

## Tasks / Subtasks

- [x] Task 1: Update Phase 1 and Phase 2 completion status (AC: #1)
  - [x] 1.1 Update Phase 2 status from "In Progress" to "Complete" — all 9 items are done (see Dev Notes for evidence)
  - [x] 1.2 Mark all Phase 2 `[ ]` checkboxes as `[x]` — trunk migration, PyPI pipeline, SECURITY.md, README, py.typed, clean test suite, docstrings, MkDocs site, community announcement are all complete
  - [x] 1.3 Do NOT add internal story IDs (e.g., "Story 2.1") to the public roadmap — external developers don't know what these mean. Instead, let completed checkboxes speak for themselves; traceability lives in commit messages and PR descriptions.
  - [x] 1.4 Update Phase 1 bullet items to reflect current test count (168 tests, 99% coverage) instead of outdated numbers (86 tests)

- [x] Task 2: Add Backend Upgrade Schedule section (AC: #1)
  - [x] 2.1 Add a "Backend Upgrade Schedule" section after the Phase 4 section (or as a standalone summary section at the top, after Vision)
  - [x] 2.2 Content must include: Fernet (AES-128-CBC + HMAC-SHA256) available now in Phase 1, AES-256-GCM planned for Phase 3, KMS backends (AWS, GCP, HashiCorp Vault) planned for Phase 4
  - [x] 2.3 Include a summary table: `| Phase | Backend | Key Size | Standard | Status |` with 3 rows (5-column format serves compliance reviewers who need algorithm details at a glance)
  - [x] 2.4 Note that the envelope protocol enables zero-downtime migration between backends (cross-reference `docs/envelope-protocol.md`)

- [x] Task 3: Verify against PRD phase definitions (AC: #1)
  - [x] 3.1 Cross-check Phase 1 items against PRD section "MVP — Minimum Viable Product" — all items match
  - [x] 3.2 Cross-check Phase 3 items against PRD section "Growth Features (Post-MVP)" — add any PRD items missing from roadmap
  - [x] 3.3 Cross-check Phase 4 items against PRD section "Vision (Future)" — add any PRD items missing from roadmap
  - [x] 3.4 Verify FR56 satisfaction: "phase timeline, planned capabilities per phase, and backend upgrade schedule" — all three present

- [x] Task 4: Clean up stale references (AC: #1)
  - [x] 4.1 Remove or update GitHub issue refs that are outdated — keep refs only if issues are still open and accurately describe the work
  - [x] 4.2 Remove "SQLAlchemy ORM migration (#20)" from roadmap — ADR-004 decided "Own Our Schema" with raw parametrized SQL, and the PRD does not list SQLAlchemy ORM migration in any phase
  - [x] 4.3 Update Phase 3 "CI matrix" item — this is already done (CI tests against google-adk 1.22.0 + latest on Python 3.12 + 3.13)
  - [x] 4.4 Ensure no Phase 2 items remain in Phase 3 (e.g., "Backend authoring documentation" may belong in Phase 3 or 4)

- [x] Task 5: Run quality gates (AC: #1)
  - [x] 5.1 `uv run mkdocs build --strict` — zero warnings, zero errors
  - [x] 5.2 `pre-commit run --all-files` — all hooks pass
  - [x] 5.3 `uv run ruff check .` — zero lint violations
  - [x] 5.4 `uv run pytest` — all tests pass (no regressions, documentation-only story)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `uv run mkdocs build --strict` renders `docs/ROADMAP.md` with zero errors; page contains: 4 phases with updated completion status, backend upgrade schedule table, capabilities per phase, cross-reference to envelope protocol; PRD FR56 requirements verified; `pre-commit run --all-files` passes all 9 hooks including docvet | pass |

## Dev Notes

### What This Story Does

This story **updates** the existing `docs/ROADMAP.md` — it does NOT create a new file. The roadmap already exists and is already in the mkdocs.yml nav at line 161 (`- Roadmap: ROADMAP.md`). The work is:
1. Fix stale completion status (Phase 1-2 items shown as `[ ]` that are actually done)
2. Add the missing "Backend Upgrade Schedule" section required by FR56
3. Verify content against PRD phase definitions
4. Clean up outdated references

### What Already Exists (Do NOT Recreate)

| Component | Status | File |
|-----------|--------|------|
| ROADMAP.md with 4-phase structure | Complete (but stale) | `docs/ROADMAP.md` |
| MkDocs nav entry for Roadmap | Complete | `mkdocs.yml` line 161 |
| MkDocs site with strict builds | Complete | `mkdocs.yml`, `.github/workflows/docs.yml` |
| Envelope Protocol page (cross-ref target) | Complete | `docs/envelope-protocol.md` |
| Algorithm Documentation page (cross-ref target) | Complete | `docs/algorithms.md` |

### Phase 2 Completion Evidence

Every Phase 2 `[ ]` item in the current ROADMAP.md is actually done:

| ROADMAP.md Item | Evidence | Story/Commit |
|-----------------|----------|-------------|
| Trunk-based migration to main | Current branch is `main` | Epic 1, Story 1-10 |
| PyPI/TestPyPI publish pipeline | v1.0.1 on PyPI, `publish.yml` exists | Epic 1, Story 1-11 |
| SECURITY.md | `/SECURITY.md` exists with disclosure policy | Epic 1, Story 1-8 |
| README rewrite | Compliance gateway positioning, badges, quick-start | Epic 1, Story 1-9 |
| py.typed marker + pyproject extras | `src/adk_secure_sessions/py.typed` exists | Epic 1, Story 1-7 |
| Clean test suite (zero warnings) | 168 tests, 99% coverage, zero lint | Epic 1, Story 1-4 |
| Docstring Examples on public API | All 8 modules, docvet enforced | Epic 2, Story 2-1 |
| MkDocs documentation site | Full site with API ref, ADRs, architecture docs | Epic 2, Stories 2-2, 2-3 |
| Community announcement | GitHub Discussion post | Epic 1, Story 1-12 |

### Phase 3 Items — GitHub Issue Status

All Phase 3 GitHub issue refs are still valid and open:

| Issue | Title | Status |
|-------|-------|--------|
| #16 | AES-256-GCM encryption backend | Open |
| #17 | Replace fixed PBKDF2 salt with per-key random salt | Open |
| #9 | Phase 2: Hardening + PostgreSQL (key rotation, PostgreSQL, benchmarks) | Open |
| #20 | Migrate from raw SQL to SQLAlchemy ORM | Open |
| #22 | Stale session detection with optimistic concurrency | Open |
| #38 | Split test_encrypted_session_service.py | Open |
| #39 | Refactor test_adk_integration.py | Open |

**Note on #20 (SQLAlchemy ORM):** ADR-004 decided "Own Our Schema" with raw parametrized SQL via aiosqlite. The roadmap lists SQLAlchemy ORM migration as a Phase 3 item, but this may conflict with the ADR. The dev agent should check if issue #20 is still aligned with project direction. If the ADR holds, remove or reclassify this item. If #20 has been updated to propose something compatible (e.g., SQLAlchemy Core, not ORM), keep it.

**Note on CI matrix:** The CI already tests against google-adk 1.22.0 + latest on Python 3.12 + 3.13 (see `.github/workflows/ci.yml`). This Phase 3 item is done — mark it `[x]`.

### Backend Upgrade Schedule Content

The AC requires a "backend upgrade schedule." Include this information:

| Phase | Backend | Key Size | Standard | Status |
|-------|---------|----------|----------|--------|
| Phase 1 (now) | Fernet (AES-128-CBC + HMAC-SHA256) | 128-bit | FIPS 197, SP 800-38A | Available |
| Phase 3 | AES-256-GCM | 256-bit | FIPS 197, SP 800-38D | Planned |
| Phase 4 | AWS KMS / GCP Cloud KMS / HashiCorp Vault | Provider-managed | Provider-dependent | Planned |

Cross-reference `docs/envelope-protocol.md` for how the envelope protocol enables zero-downtime backend migration: old Fernet data (backend ID `0x01`) coexists with new AES-256-GCM data (backend ID `0x02`).

### PRD Phase Definitions (Source of Truth)

From `_bmad-output/planning-artifacts/prd.md`:

- **FR56** `[MVP]`: "Developer can read a published roadmap on the documentation site with phase timeline, planned capabilities per phase, and backend upgrade schedule"
- **Phase 1 (Core)**: Encryption engine — EncryptionBackend protocol, FernetBackend, exception hierarchy, serialization with envelope, EncryptedSessionService with SQLite
- **Phase 2 (Ship)**: PyPI launch — documentation, compliance positioning, market presence
- **Phase 3 (Expand)**: AES-256-GCM, per-key random salt, key rotation, PostgreSQL, performance benchmarks
- **Phase 4 (Enterprise)**: AWS KMS, GCP Cloud KMS, HashiCorp Vault, SQLCipher, audit logging, FIPS deployment guide

### Anti-Patterns to Avoid

- **DO NOT** create a new `docs/ROADMAP.md` — edit the existing one
- **DO NOT** modify `mkdocs.yml` nav — the Roadmap entry is already there (line 161)
- **DO NOT** modify source code — this is a documentation-only story
- **DO NOT** add time estimates or dates — the roadmap uses phase-based planning, not date-based
- **DO NOT** claim Phase 2 is "In Progress" — all items are complete
- **DO NOT** add `@pytest.mark.asyncio` — project uses `asyncio_mode = "auto"`
- **DO NOT** remove GitHub issue refs that are still valid — only update or remove truly stale ones

### CI Constraint: Draft PRs Skip Docs Build

The `docs.yml` workflow only runs on non-draft PRs. Since project convention is always draft PRs, verify locally with `uv run mkdocs build --strict` during development.

### Previous Story Intelligence (2.3)

From Story 2.3 (Envelope Protocol & Algorithm Specification Pages):
- MkDocs strict builds enforce valid markdown links and nav entries
- `git-revision-date-localized-plugin` warnings for modified files are expected and don't fail strict mode
- MkDocs Material prints a MkDocs 2.0 compatibility banner — visual only, does NOT fail `--strict`
- docvet only checks `.py` files (types: [python]), not `.md` — real markdown validation is `mkdocs build --strict`
- 168 tests pass, 9/9 pre-commit hooks pass, zero lint violations
- Use relative paths from `docs/` root for cross-references (e.g., `[Envelope Protocol](envelope-protocol.md)`)

### Git Intelligence

Recent commits on `main`:
- `f76555a` — `docs(architecture): add envelope protocol and algorithm specification pages (#92)` — Story 2.3 merge
- `cd3eca5` — `fix(release): guard fromJSON with short-circuit to prevent empty parse (#90)` — Release automation fix
- `4607c94` — `ci(release): sync uv.lock after release-please version bump (#89)` — Release automation
- Codebase is stable post-Story 2.3. No active development branches.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/ROADMAP.md` | Updated — phase completion status, backend upgrade schedule, PRD consistency |

### Peripheral Config Impact

| File | Change | Reason |
|------|--------|--------|
| `docs/ROADMAP.md` | Modified | Core deliverable — update content |
| `mkdocs.yml` | No changes | Roadmap already in nav (line 161) |
| `.github/workflows/docs.yml` | No changes | Already strict from Story 2.2 |
| `pyproject.toml` | No changes | No new deps |
| `.pre-commit-config.yaml` | No changes | docvet already configured |
| Source code (`src/`) | No changes | Documentation-only story |
| Tests (`tests/`) | No changes | No code changes to test |

### Project Structure Notes

- `docs/ROADMAP.md` stays in `docs/` root — consistent with existing placement
- No new files created — this is a content update to an existing file

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4 — Published Roadmap on Documentation Site]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2 — Documentation & Compliance Credibility]
- [Source: _bmad-output/planning-artifacts/prd.md#FR56 — Published roadmap on docs site]
- [Source: _bmad-output/planning-artifacts/prd.md#MVP — Phase definitions]
- [Source: docs/ROADMAP.md — Current roadmap (stale)]
- [Source: docs/envelope-protocol.md — Migration enablement section (cross-ref)]
- [Source: docs/algorithms.md — Backend algorithm details (cross-ref)]
- [Source: mkdocs.yml — Nav structure (line 161, Roadmap already present)]
- [Source: _bmad-output/implementation-artifacts/2-3-envelope-protocol-algorithm-specification-pages.md — Previous story learnings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest` -- all tests pass, >=90% coverage
- [x] `pre-commit run --all-files` -- all hooks pass
- [x] `uv run mkdocs build --strict` -- zero errors, roadmap renders correctly

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
| 2026-03-02 | Story created by create-story workflow. Documentation update story: update `docs/ROADMAP.md` with Phase 1-2 completion status, add backend upgrade schedule section (FR56), verify against PRD phase definitions, clean up stale references. No new files, no nav changes. |
| 2026-03-02 | Party mode consensus (7 agents, unanimous): 3 LOW findings applied — (1) Task 4.2 made definitive: remove SQLAlchemy ORM #20 per ADR-004, (2) Task 2.3 updated to 5-column backend upgrade table for compliance reviewers, (3) Task 1.3 reversed: no internal story IDs on public roadmap. |
| 2026-03-02 | Implementation complete: updated Phase 1-2 completion status, added Backend Upgrade Schedule section with compliance table, verified all phases against PRD, cleaned up stale references (removed SQLAlchemy ORM #20, marked CI matrix done), added blog post item from PRD. All quality gates pass. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Documentation-only story with no code changes.

### Completion Notes List

- Updated Phase 2 status to "Complete" and marked all 9 items as `[x]` with issue refs removed (closed issues)
- Updated Phase 1 CI bullet to reflect 168 tests at 99% coverage
- Added "Backend Upgrade Schedule" section after Vision with 5-column compliance table (Phase, Backend, Key Size, Standard, Status) and envelope protocol cross-reference
- Cross-checked all phases against PRD definitions: Phase 1 items match MVP, added "Blog post or tutorial" to Phase 3 from PRD, Phase 4 items match Vision
- Verified FR56 satisfaction: phase timeline, planned capabilities per phase, and backend upgrade schedule all present
- Removed "SQLAlchemy ORM migration (#20)" from Phase 3 per ADR-004 "Own Our Schema"
- Marked CI matrix as done `[x]` in Phase 3 (already testing google-adk 1.22.0 + latest on Python 3.12 + 3.13)
- Verified "Backend authoring documentation" stays in Phase 3 (matches PRD FR50)
- All quality gates pass: mkdocs strict build, pre-commit (9/9 hooks), ruff, pytest (168 passed)

### File List

| File | Action |
|------|--------|
| `docs/ROADMAP.md` | Modified |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified |
| `_bmad-output/implementation-artifacts/2-4-published-roadmap-on-documentation-site.md` | Modified |
