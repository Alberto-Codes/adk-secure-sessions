# Story 6.1: Fix User-Facing "Drop-In Replacement" Claims

Status: review
Branch: feat/docs-6-1-fix-drop-in-claims
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/119

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer evaluating the library**,
I want **accurate descriptions of what adk-secure-sessions is on PyPI, README, docs site, and API reference**,
so that **I understand exactly what I'm installing — an encrypted session service implementing BaseSessionService — without false expectations about DatabaseSessionService compatibility**.

## Acceptance Criteria

1. **Given** `pyproject.toml:4` says "drop-in replacement for DatabaseSessionService"
   **When** the description is corrected
   **Then** it reads "Encrypted session persistence for Google ADK agents" (FR-NEW-1)
   **And** the description is concise and appropriate for PyPI package metadata context

2. **Given** `README.md:13` says "drop-in replacement for `DatabaseSessionService`"
   **When** the description is corrected
   **Then** it accurately describes the library as implementing BaseSessionService with encryption (FR-NEW-1)
   **And** the language is appropriate for a README audience (medium detail)

3. **Given** `docs/index.md:13` says "drop-in replacement for ADK's `DatabaseSessionService` and `SqliteSessionService`"
   **When** the description is corrected
   **Then** it accurately describes the library as an encrypted session persistence service (FR-NEW-1)
   **And** the docs site landing page provides enough context for a first-time visitor

4. **Given** `src/adk_secure_sessions/__init__.py:10-11` says "Drop-in replacement for ADK's ``DatabaseSessionService``"
   **When** the module docstring is corrected
   **Then** it accurately references BaseSessionService, not DatabaseSessionService (FR-NEW-1, FR28)

5. **Given** `src/adk_secure_sessions/services/encrypted_session.py:3` says "drop-in replacement for ADK's ``DatabaseSessionService``"
   **And** line 123 says "Drop-in replacement for ADK's ``DatabaseSessionService``"
   **When** the module and class docstrings are corrected
   **Then** they accurately reference BaseSessionService with field-level encryption at rest (FR-NEW-1, FR28)
   **And** the docstring is appropriate for API reference context (technical detail)

6. **Given** `CHANGELOG.md:39` correctly says "drop-in replacement for ADK's BaseSessionService"
   **When** reviewing changelog entries
   **Then** this entry is NOT modified — it is already accurate

7. **Given** `docs/project-overview.md:8` says "drop-in replacement for ADK's `DatabaseSessionService` and `SqliteSessionService`"
   **When** the description is corrected
   **Then** it accurately describes the library as an encrypted session persistence service implementing BaseSessionService (FR-NEW-1)

8. **And** all replacement language is contextually appropriate per the target audience (PyPI short, README medium, docstrings technical, docs site explanatory)
   **And** no code logic is changed — only docstrings, descriptions, and documentation text
   **And** `docs/faq.md` "drop-in backend" usage is NOT changed (refers to encryption backends, not service replacement — already accurate)
   **And** `docs/adr/ADR-002-async-first.md` "Direct drop-in" usage is NOT changed (refers to async integration, not service replacement — already accurate)
   **And** `tests/integration/test_adk_runner.py` "drop-in" usage is NOT changed (refers to BaseSessionService contract validation — already accurate)

## Tasks / Subtasks

- [x] Task 1: Fix pyproject.toml description (AC: 1)
  - [x] Change `description` field from "drop-in replacement for DatabaseSessionService" to "Encrypted session persistence for Google ADK agents"
- [x] Task 2: Fix README.md (AC: 2)
  - [x] Rewrite line 13 to accurately describe the library as implementing BaseSessionService
  - [x] Preserve the compliance value proposition language (PHI, PII, financial data)
- [x] Task 3: Fix docs/index.md (AC: 3)
  - [x] Rewrite line 13 to remove DatabaseSessionService and SqliteSessionService claims
  - [x] Keep the regulated industries context
- [x] Task 4: Fix __init__.py docstring (AC: 4)
  - [x] Change lines 10-11 from "Drop-in replacement for ADK's DatabaseSessionService" to reference BaseSessionService
- [x] Task 5: Fix encrypted_session.py docstrings (AC: 5)
  - [x] Fix module docstring at line 3
  - [x] Fix class docstring at line 123
- [x] Task 6: Verify CHANGELOG.md is correct (AC: 6)
  - [x] Confirm line 39 says "BaseSessionService" — no change needed
- [x] Task 7: Fix docs/project-overview.md (AC: 7)
  - [x] Rewrite line 8 to remove DatabaseSessionService and SqliteSessionService claims
- [x] Task 8: Verify excluded files are not changed (AC: 8)
  - [x] Confirm faq.md, ADR-002, test_adk_runner.py "drop-in" usages are untouched

### Cross-Cutting Test Maturity (Standing Task)

<!-- Every story includes one small-footprint, high-risk-area test addition.
     This is brownfield hardening — pick a gap in an area NOT related to the
     story scope so the safety net grows steadily across epics. -->

- [x] Identify one high-risk area lacking test coverage (outside story scope)
- [x] Add test(s) — small footprint, meaningful assertion
- [x] Verify new test(s) pass in CI

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | Manual: verified `pyproject.toml` description = "Encrypted session persistence for Google ADK agents" | pass |
| 2    | Manual: verified README.md line 13 references BaseSessionService, preserves PHI/PII/financial language | pass |
| 3    | Manual: verified docs/index.md line 13 references BaseSessionService, preserves regulated industries context | pass |
| 4    | Manual: verified `__init__.py` docstring references BaseSessionService with transparent encryption | pass |
| 5    | Manual: verified encrypted_session.py module docstring (line 3) and class docstring (line 123) reference BaseSessionService | pass |
| 6    | Manual: verified CHANGELOG.md line 39 already says "BaseSessionService" — unchanged | pass |
| 7    | Manual: verified docs/project-overview.md line 8 references BaseSessionService | pass |
| 8    | Grep verification: `grep -r "drop-in replacement.*DatabaseSessionService"` returns zero hits in corrected source files; faq.md, ADR-002, test_adk_runner.py untouched | pass |

## Dev Notes

### Context-Appropriate Replacement Language

The team agreed on context-appropriate variants — NOT a single string pasted everywhere:

| File | Audience | Recommended Language |
|------|----------|---------------------|
| `pyproject.toml` | PyPI metadata (short) | "Encrypted session persistence for Google ADK agents" |
| `README.md` | GitHub visitors (medium) | "...encrypted session service implementing ADK's BaseSessionService..." |
| `docs/index.md` | Docs site visitors (explanatory) | "...encrypted session persistence implementing BaseSessionService..." |
| `__init__.py` | IDE tooltips (technical) | "Encrypted session service implementing ``BaseSessionService`` with transparent encryption" |
| `encrypted_session.py` | API reference (technical) | "Encrypted session service implementing ``BaseSessionService`` with field-level encryption at rest" |
| `docs/project-overview.md` | Docs overview (medium) | "...encrypted session storage implementing BaseSessionService..." |

### Exact Current Text to Replace

**pyproject.toml:4:**
```
description = "Encrypted session storage for Google ADK — drop-in replacement for DatabaseSessionService with at-rest encryption"
```

**README.md:13:**
```
**adk-secure-sessions** is a drop-in replacement for `DatabaseSessionService` that encrypts state and conversation history at rest, so you can close the encryption-at-rest gap without changing your agent code.
```

**docs/index.md:13:**
```
adk-secure-sessions is a drop-in replacement for ADK's `DatabaseSessionService` and `SqliteSessionService` that encrypts session data at rest.
```

**src/adk_secure_sessions/__init__.py:10-11:**
```python
    EncryptedSessionService: Drop-in replacement for ADK's
        ``DatabaseSessionService`` with transparent encryption.
```

**src/adk_secure_sessions/services/encrypted_session.py:3:**
```python
Provides a drop-in replacement for ADK's ``DatabaseSessionService`` with
transparent field-level encryption for session state and event data.
```

**src/adk_secure_sessions/services/encrypted_session.py:123:**
```python
    event data. Drop-in replacement for ADK's ``DatabaseSessionService``.
```

**docs/project-overview.md:8:**
```
It is a drop-in replacement for ADK's `DatabaseSessionService` and `SqliteSessionService` that encrypts session data at rest using pluggable encryption backends.
```

### Files That Must NOT Be Changed

- `CHANGELOG.md:39` — already says "BaseSessionService" (correct)
- `docs/faq.md:37-38` — "drop-in backend" refers to encryption backends (correct usage)
- `docs/adr/ADR-002-async-first.md:35` — "Direct drop-in" refers to async integration (correct usage)
- `tests/integration/test_adk_runner.py:1,4,117` — "drop-in" refers to BaseSessionService contract validation (correct usage)

### Blast Radius — Peripheral Config Impact

| File | Impact | Reason |
|------|--------|--------|
| `pyproject.toml` | YES — description field only | Package metadata correction |
| `mkdocs.yml` | NO | No nav structure changes, only page content |
| `.github/workflows/*.yml` | NO | No CI/CD changes |
| `.pre-commit-config.yaml` | NO | No hook changes |
| `release-please-config.json` | NO | No release config changes |

### Previous Story Intelligence

**From Epic 2 Retrospective (2026-03-03):**
- Documentation quality bar established: consistent structure by Story 2.3
- Cross-cutting test maturity: 9 tests added beyond story scope across Epic 2
- Story document drift risk: keep file lists and counts in sync
- Doc impact analysis should be explicit in every story

**Recent commit pattern:** Last 5 commits are all docs-focused (branding, getting-started, deploy workflow). Documentation patterns are fresh in the codebase.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `pyproject.toml` | Fix `description` field — PyPI metadata |
| `README.md` | Fix project description paragraph |
| `docs/index.md` | Fix landing page description |
| `docs/project-overview.md` | Fix overview description |
| `src/adk_secure_sessions/__init__.py` | Fix module docstring (affects auto-generated API reference via griffe) |
| `src/adk_secure_sessions/services/encrypted_session.py` | Fix module + class docstrings (affects auto-generated API reference via griffe) |

### Project Structure Notes

- All changes are to existing files — no new files created
- Docstring changes in `src/` will automatically propagate to `docs/reference/` via griffe on next MkDocs build
- `pyproject.toml` description change will take effect on next PyPI publish

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Story 6.1 ACs]
- [Source: GitHub Issue #118 — "Revisit 'Own Our Schema' architecture claim"]
- [Source: .claude/rules/conventions.md — Project conventions]
- [Source: _bmad-output/implementation-artifacts/epic-2-retro-2026-03-03.md — Epic 2 learnings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 177 passed, 99.68% coverage
- [x] `pre-commit run --all-files` -- all hooks pass

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
| 2026-03-04 | Story created — comprehensive context engine analysis |
| 2026-03-04 | Implementation complete — all 8 tasks done, cross-cutting test added, all quality gates pass |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no errors or retries.

### Completion Notes List

- Replaced "drop-in replacement for DatabaseSessionService" with context-appropriate language across 6 files per Dev Notes guidance
- Verified CHANGELOG.md line 39 already correct (BaseSessionService) — no change needed
- Verified excluded files (faq.md, ADR-002, test_adk_runner.py) untouched via grep
- Cross-cutting test: added `TestSessionRecreateAfterDelete` integration test verifying no stale data after session deletion and recreation (tests/integration/test_adk_integration.py)
- All quality gates pass: 177 tests, 99.68% coverage, ruff clean, ty clean, pre-commit clean

### File List

- `pyproject.toml` — fixed description field (PyPI metadata)
- `README.md` — fixed project description paragraph (line 13)
- `docs/index.md` — fixed landing page description (line 13)
- `docs/project-overview.md` — fixed overview description (line 8)
- `src/adk_secure_sessions/__init__.py` — fixed module docstring (lines 10-11)
- `src/adk_secure_sessions/services/encrypted_session.py` — fixed module docstring (line 3) and class docstring (line 123)
- `tests/integration/test_adk_integration.py` — added cross-cutting test (TestSessionRecreateAfterDelete)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status updated to review
- `_bmad-output/implementation-artifacts/6-1-fix-user-facing-drop-in-replacement-claims.md` — story file updated
