# Story 2.2: MkDocs Documentation Site Setup

Status: done
Branch: feat/docs-2-2-mkdocs-site-setup
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/86

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer evaluating the library**,
I want **a documentation site with auto-generated API reference and published ADRs**,
so that **I can browse comprehensive documentation without reading raw source files**.

## Acceptance Criteria

1. **Given** `mkdocs.yml` exists and MkDocs Material is configured
   **When** the documentation site is built with `uv run mkdocs build --strict`
   **Then** the site builds without errors or warnings (strict mode — warnings are errors) (FR35, FR36)

2. **Given** `scripts/gen_ref_pages.py` generates API reference pages at build time
   **When** the script is reviewed
   **Then** it uses dynamic module discovery (`src.rglob("*.py")`), not hardcoded paths (FR35)
   **And** auto-generated API reference pages render correctly for all public symbols via mkdocstrings

3. **Given** ADR-000 through ADR-006 exist in `docs/adr/`
   **When** the site navigation is inspected
   **Then** all ADRs (ADR-000 through ADR-006) are accessible in the navigation (FR36)

4. **Given** this epic will produce documentation pages across stories 2.2–2.6
   **When** the site navigation is structured
   **Then** it accommodates all documentation pages created in this epic (Getting Started, API Reference, Architecture Decisions, Roadmap, Envelope Protocol Spec, Algorithm Documentation, FAQ)
   **And** future stories 2.3–2.6 can add their pages by inserting a single nav entry under an existing section — no section restructuring required

5. **Given** `.github/workflows/docs.yml` verifies documentation builds on PRs
   **When** the workflow is updated
   **Then** the docs CI workflow verifies the build with `--strict` on PRs
   **And** build failures are blocking (not `continue-on-error`)

6. **Given** all documentation changes are complete
   **When** the quality pipeline runs
   **Then** `pre-commit run --all-files` passes (all hooks including docvet)

## Tasks / Subtasks

- [x] Task 1: Add ADR-006 to mkdocs.yml navigation (AC: #3)
  - [x] 1.1 Add `Configuration Error: adr/ADR-006-configuration-error.md` entry under the Architecture nav section, after ADR-005
  - [x] 1.2 Verify `uv run mkdocs build` picks up the new nav entry

- [x] Task 2: Restructure mkdocs.yml nav to target structure (AC: #3, #4)
  - [x] 2.1 Replace the entire `nav:` section in `mkdocs.yml` with the prescribed target nav (see "Target Nav Structure" in Dev Notes)
  - [x] 2.2 Add `ROADMAP.md` and `development-guide.md` to nav in their prescribed positions
  - [x] 2.3 Exclude BMAD artifacts (`project-overview.md`, `source-tree-analysis.md`) from nav — add `not_in_nav` top-level config (MkDocs 1.6 syntax)
  - [x] 2.4 Do NOT create placeholder/stub pages for Stories 2.3–2.6 — only place pages that exist today

- [x] Task 4: Update docs CI workflow for strict builds (AC: #5)
  - [x] 4.1 Change `uv run mkdocs build` to `uv run mkdocs build --strict` in `.github/workflows/docs.yml`
  - [x] 4.2 Remove `continue-on-error: true` from the build job (make failures blocking)
  - [x] 4.3 Keep the `draft == false` condition — draft PRs should still skip docs build

- [x] Task 5: Fix any strict-mode build warnings (AC: #1)
  - [x] 5.1 Run `uv run mkdocs build --strict` locally and capture any warnings/errors
  - [x] 5.2 Fix all issues (common: orphaned pages not in nav, broken cross-references, missing files referenced in nav)
  - [x] 5.3 Confirm clean build with zero warnings under `--strict`

- [x] Task 6: Run quality gates (AC: #1, #6)
  - [x] 6.1 `uv run mkdocs build --strict` — zero warnings, zero errors
  - [x] 6.2 `pre-commit run --all-files` — all hooks pass
  - [x] 6.3 `uv run ruff check .` — zero lint violations
  - [x] 6.4 `uv run pytest` — all tests pass (no regressions from YAML/config changes)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `uv run mkdocs build --strict` exits 0 with no warnings | pass |
| 2    | Visual inspection: `gen_ref_pages.py` uses `src.rglob("*.py")` (pre-verified); API ref renders all symbols in built site | pass |
| 3    | ADR-006 appears in `mkdocs.yml` nav under Architecture > Decisions; all ADRs 000–006 in nav | pass |
| 4    | Nav matches prescribed target structure exactly; YAML comments mark where 2.3–2.6 insert single entries | pass |
| 5    | `docs.yml` uses `--strict` (line 36); `continue-on-error: true` removed from build job; `draft == false` preserved | pass |
| 6    | `pre-commit run --all-files` — 9/9 hooks pass | pass |

## Dev Notes

### What This Story Does

This story makes the existing MkDocs documentation site **production-ready** by fixing navigation gaps, enabling strict builds, and structuring the nav for the remaining Epic 2 stories. Most of the MkDocs infrastructure already exists — this story is about **alignment and hardening**, not greenfield setup.

### What Already Exists (Do NOT Recreate)

The following are already in place and working:

| Component | Status | File |
|-----------|--------|------|
| `mkdocs.yml` — Material theme, plugins, extensions | Complete | `mkdocs.yml` |
| `gen_ref_pages.py` — dynamic module discovery | Complete | `scripts/gen_ref_pages.py` |
| mkdocstrings config (Google-style, spacy sections, griffe extensions) | Complete | `mkdocs.yml` plugins section |
| All MkDocs dependencies in dev group | Complete | `pyproject.toml` |
| `docs.yml` CI workflow — build verification on PRs | Exists, needs `--strict` | `.github/workflows/docs.yml` |
| `docs/reference/index.md` — hand-authored API reference landing | Complete | `docs/reference/index.md` |
| docvet pre-commit hook | Complete | `.pre-commit-config.yaml` |
| `site/` in `.gitignore` | Complete | `.gitignore` lines 181, 245 |

### Known Issues to Fix

1. **ADR-006 missing from nav**: `docs/adr/ADR-006-configuration-error.md` exists on disk and is listed in `docs/adr/index.md`, but `mkdocs.yml` nav only includes ADR-000 through ADR-005 (line 149). Add it after ADR-005.

2. **Orphaned pages not in nav**: `--strict` build reports these pages exist but are not in nav:
   - `ROADMAP.md` — add to nav (Story 2.4 will refine content)
   - `development-guide.md` — add to nav under Contributing
   - `project-overview.md` — BMAD artifact, NOT user-facing. Exclude via `not_in_nav` or move out of `docs/`
   - `source-tree-analysis.md` — BMAD artifact, NOT user-facing. Exclude via `not_in_nav` or move out of `docs/`
   - `reference/SUMMARY.md` and `reference/adk_secure_sessions/*.md` — generated by `gen-files`/`literate-nav`, expected to not be in explicit nav. Exclude via `not_in_nav` glob: `reference/**/*.md` (the literate-nav plugin handles their inclusion)

3. **docs.yml not strict**: Build step is `uv run mkdocs build` (no `--strict`). Also has `continue-on-error: true` on the job, making it non-blocking.

### Things That Are Fine (Do NOT Change)

- **`edit_uri: edit/HEAD/`** — `HEAD` is a valid git ref pointing to the default branch. More portable than hardcoding `edit/main/docs/` because it survives branch renames. Leave as-is.
- **`gen_ref_pages.py`** — already uses `src.rglob("*.py")` for dynamic module discovery. Verified, no changes needed.

### CI Constraint: Draft PRs Skip Docs Build

The `docs.yml` workflow triggers only on non-draft PRs (`if: github.event.pull_request.draft == false`). Since project convention is to always create PRs as draft, the docs CI build will **not run until the PR is marked ready for review**. During development, always verify locally with `uv run mkdocs build --strict`.

### Target Nav Structure (Prescribed)

This is the **exact nav** the dev agent must implement. Future stories add entries where indicated by comments — no section restructuring required.

```yaml
nav:
  - Home: index.md
  # Story 2.6 adds: - Getting Started: getting-started.md
  - API Reference:
      - Overview: reference/index.md
      - Full Module Index: reference/adk_secure_sessions/index.md
  - Architecture:
      - Overview: ARCHITECTURE.md
      # Story 2.3 adds: - Envelope Protocol: envelope-protocol.md
      # Story 2.3 adds: - Algorithm Documentation: algorithms.md
      - Decisions:
          - adr/index.md
          - Direct Implementation: adr/ADR-000-strategy-decorator-architecture.md
          - Protocol Interfaces: adr/ADR-001-protocol-based-interfaces.md
          - Async-First: adr/ADR-002-async-first.md
          - Field-Level Encryption: adr/ADR-003-field-level-encryption.md
          - ADK Schema Compatibility: adr/ADR-004-adk-schema-compatibility.md
          - Exception Hierarchy: adr/ADR-005-exception-hierarchy.md
          - Configuration Error: adr/ADR-006-configuration-error.md
  - Roadmap: ROADMAP.md
  # Story 2.5 adds: - FAQ: faq.md
  - Changelog: changelog.md
  - Contributing:
      - Development Guide: development-guide.md
      - Docstring Templates: contributing/docstring-templates.md
```

YAML comments are stripped at build time — they serve only as dev guidance and do NOT affect the built site.

### Excluding Non-Nav Pages

Pages that exist in `docs/` but must NOT be in the nav need to be excluded from strict-mode warnings. Add this to `mkdocs.yml`:

```yaml
validation:
  nav:
    not_in_nav: |
      project-overview.md
      source-tree-analysis.md
      reference/SUMMARY.md
      reference/**/*.md
```

- `project-overview.md`, `source-tree-analysis.md` — BMAD-generated internal artifacts, not user-facing
- `reference/SUMMARY.md`, `reference/**/*.md` — generated by `gen-files`/`literate-nav`, handled by those plugins (not explicit nav)

### Actual `--strict` Build Output (2026-03-02)

Current build passes with `--strict` but reports these INFO-level messages about pages not in nav:

```
INFO - The following pages exist in the docs directory, but are not included in the "nav" configuration:
  - ROADMAP.md
  - development-guide.md
  - project-overview.md
  - source-tree-analysis.md
  - adr/ADR-006-configuration-error.md
  - reference/SUMMARY.md
  - reference/adk_secure_sessions/exceptions.md
  - reference/adk_secure_sessions/protocols.md
  - reference/adk_secure_sessions/serialization.md
  - reference/adk_secure_sessions/backends/index.md
  - reference/adk_secure_sessions/backends/fernet.md
  - reference/adk_secure_sessions/services/index.md
  - reference/adk_secure_sessions/services/encrypted_session.md
```

These are INFO, not WARNING, so they don't currently fail `--strict`. However, the target nav + `not_in_nav` config above resolves all of them. After applying Tasks 1–3, this list should be empty.

Also noted: mkdocs-material prints a banner warning about MkDocs 2.0 incompatibility. This is a visual banner from the theme, not a MkDocs warning — it does NOT fail `--strict`. No action needed.

### Peripheral Config Impact

| File | Change | Reason |
|------|--------|--------|
| `mkdocs.yml` | Nav restructure + ADR-006 + possible `not_in_nav` | Core deliverable |
| `.github/workflows/docs.yml` | Add `--strict`, remove `continue-on-error` | AC #5 |
| `pyproject.toml` | No changes expected | Deps already present |
| `.pre-commit-config.yaml` | No changes expected | docvet hook already configured |

No new files created. No source code changes. No test changes.

### Previous Story Intelligence (2.1)

From Story 2.1 (Docstring Examples):
- All docstrings now use fenced code blocks — mkdocstrings will render them with syntax highlighting
- docvet `fail-on` enforcement is active in `pyproject.toml`
- `interrogate` was removed; docvet handles docstring coverage
- Story 2.1 explicitly noted: "No mkdocs.yml changes (mkdocs config alignment is Story 2.2)"
- 9 pre-commit hooks pass on the current codebase
- Quality gates: ruff check, ruff format, ty check, pytest (167 tests), pre-commit (9/9 hooks)

### Git Intelligence

Recent commits on `main`:
- `44911c4` — `docs(docstrings): add fenced examples to all public APIs and enforce docvet fail-on`
- `bb9a69a` — `chore(deps): add dependency health gates and drop interrogate`

The codebase is stable post-Story 2.1. No active development branches.

### Anti-Patterns to Avoid

- **DO NOT** create placeholder/stub `.md` files for Stories 2.3–2.6 — those stories create their own content
- **DO NOT** add a GitHub Pages deploy workflow — deployment is out of scope (may be a future story or manual)
- **DO NOT** modify `gen_ref_pages.py` — it already uses dynamic discovery and works correctly
- **DO NOT** change mkdocstrings handler options — those are already tuned
- **DO NOT** add `@pytest.mark.asyncio` — project uses `asyncio_mode = "auto"`
- **DO NOT** modify source code — this story only touches `mkdocs.yml`, `docs.yml`, and possibly docs `.md` files
- **DO NOT** commit the `site/` directory — it's gitignored

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `mkdocs.yml` | Nav restructure: add ADR-006, add orphaned pages, prepare extensible structure |
| `.github/workflows/docs.yml` | Add `--strict` flag, make build failures blocking |
| docs/ pages | No content changes — only nav placement changes |

### Project Structure Notes

- All config changes are in project root (`mkdocs.yml`) and `.github/workflows/`
- Source code (`src/`) is untouched
- Test files (`tests/`) are untouched
- The `docs/` directory content is unchanged — only its organization in the nav changes

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2 — MkDocs Documentation Site Setup]
- [Source: _bmad-output/planning-artifacts/architecture.md — Development Toolchain (lines 142-145)]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Directory Structure (lines 636-658)]
- [Source: _bmad-output/planning-artifacts/prd.md — Documentation Architecture (lines 474-485)]
- [Source: FR35 — Auto-generated API reference documentation for all public symbols]
- [Source: FR36 — Published architecture decision records]
- [Source: mkdocs.yml — Current nav structure (lines 136-153)]
- [Source: .github/workflows/docs.yml — Current docs CI workflow]
- [Source: scripts/gen_ref_pages.py — Dynamic module discovery via src.rglob("*.py")]
- [Source: _bmad-output/implementation-artifacts/2-1-docstring-examples-on-all-public-apis.md — Previous story learnings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 167 passed, >=90% coverage
- [x] `pre-commit run --all-files` -- 9/9 hooks pass

## Code Review

- **Reviewer:** Claude Opus 4.6 (adversarial code review workflow)
- **Outcome:** Approved — 0 blocking findings, story done

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | MEDIUM | `edit_uri: edit/HEAD/` missing `docs/` prefix — broken edit links on all pages (pre-existing) | Accepted as informational — pre-existing, out of scope per story spec. Backlog for future fix. |
| 2 | LOW | Story task numbering gap (1, 2, 4, 5, 6 — no Task 3) | Dismissed — renumbering would break completion record traceability |
| 3 | LOW | `scripts/` not in docs.yml trigger paths (pre-existing) | Accepted as informational — backlog item, one-line future fix |
| 4 | LOW | `.vscode/` untracked in working tree | Dismissed — environment artifact, not story-related |

### Verification

- [x] All HIGH findings resolved (none found)
- [x] All MEDIUM findings resolved or accepted (1 accepted as informational — pre-existing, not introduced by this story)
- [x] Tests pass after review fixes (167 passed, no changes needed)
- [x] Quality gates re-verified (mkdocs strict build clean, ruff 0 violations, pytest 167 passed)

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-02 | Story created by create-story workflow. Comprehensive analysis: mkdocs infrastructure exists, needs nav fixes (ADR-006 missing, orphaned pages), strict build enforcement, and nav restructure for Epic 2 extensibility. Scope: mkdocs.yml + docs.yml only. |
| 2026-03-02 | Party-mode review (Paige, Winston, Bob, Amelia). 7 improvements applied: prescribed target nav structure (no design delegation to dev), excluded BMAD artifacts from nav, removed `edit_uri` false concern, added draft-PR CI constraint note, tightened AC #4 with measurable extensibility criterion, removed redundant Task 6 (gen_ref_pages.py already verified), captured actual `--strict` build output in Dev Notes. Task count: 7 → 6. |
| 2026-03-02 | Implementation complete. Restructured mkdocs.yml nav to prescribed target structure, added ADR-006, excluded BMAD artifacts via top-level `not_in_nav` (corrected from nested `validation.nav.not_in_nav` which is invalid in MkDocs 1.6.1). Updated docs.yml CI to use `--strict` and removed `continue-on-error`. All quality gates pass: 9/9 pre-commit hooks, 167 tests, zero lint violations. |
| 2026-03-02 | Code review complete (adversarial). 4 findings: 1 MEDIUM (pre-existing `edit_uri` broken edit links — accepted informational), 2 LOW dismissed, 1 LOW backlogged. 0 blocking findings. All 6 ACs verified implemented. All 5 tasks verified done. Party-mode consensus: story approved, status → done. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Dev Notes prescribed `validation.nav.not_in_nav` syntax, but MkDocs 1.6.1 uses top-level `not_in_nav:` key. Corrected during implementation. `--strict` build confirmed clean after fix.

### Completion Notes List

- Task 1: Added ADR-006 to nav after ADR-005. Build verified.
- Task 2: Replaced entire nav with prescribed target structure. Added `not_in_nav` top-level key for BMAD artifacts and gen-files output. ROADMAP.md and development-guide.md placed in nav. No placeholder pages created. ADRs nested under Architecture > Decisions subsection.
- Task 4: docs.yml updated: `--strict` flag added, `continue-on-error: true` removed from build job, `draft == false` condition preserved.
- Task 5: Strict build was clean after Tasks 1-2 resolved all orphaned page warnings. No additional fixes needed.
- Task 6: All quality gates pass — mkdocs strict build (0 warnings), pre-commit (9/9), ruff check (0 violations), pytest (167 passed).

### File List

- `mkdocs.yml` — Nav restructured to target layout; added `not_in_nav` top-level config; ADR-006 added to nav
- `.github/workflows/docs.yml` — Added `--strict` to build command; removed `continue-on-error: true` from build job
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Story status: ready-for-dev → in-progress → review
- `_bmad-output/implementation-artifacts/2-2-mkdocs-documentation-site-setup.md` — Story file updated with task completion, AC mapping, quality gates, dev record
