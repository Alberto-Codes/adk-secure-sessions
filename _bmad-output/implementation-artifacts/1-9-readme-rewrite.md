# Story 1.9: README Rewrite

Status: review
Branch: docs/readme-1-9-rewrite
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/65

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer discovering the library for the first time**,
I want **a README with compliance gateway positioning, a quick-start code example, and status badges**,
so that **I understand the value proposition in 30 seconds and can add encrypted sessions in 5 minutes**.

## Acceptance Criteria

1. **Given** the current README exists
   **When** it is rewritten with compliance gateway positioning
   **Then** the tagline communicates "Compliance Gateway for Google ADK" (not "encryption library")
   **And** the section hierarchy is: badges at top, one-liner description, install command, quick-start code block, then links to docs/SECURITY/contributing
   **And** the quick-start code example is 5 lines or fewer showing the exact swap from `BaseSessionService` to `EncryptedSessionService` — real code, not pseudocode (FR34)
   **And** badges display PyPI version, Python version, test status, and coverage (FR40) — PyPI-dependent badges included as markdown now, auto-resolve on first publish
   **And** the license (Apache-2.0), dependency tree, and test coverage are verifiable from the README (FR40)
   **And** the README links to the documentation site (when available) and SECURITY.md
   **And** NFR28 is supported: a developer can go from `pip install` to encrypted sessions in under 5 minutes using only the README

## Tasks / Subtasks

- [x] Task 1: Rewrite README.md with compliance gateway positioning (AC: #1)
  - [x] 1.1 Add badge row at top: CI test status (`ci.yml`), license, PyPI version, Python version, coverage — CI + license work now; PyPI badges auto-resolve on first publish; add HTML comment `<!-- PyPI badges activate on first publish (Story 1.11) -->`; check if Codecov or similar coverage service is configured in `.github/workflows/ci.yml` — use static badge or omit if not
  - [x] 1.2 Write one-liner tagline using compliance gateway positioning — choose or adapt from candidate taglines in Dev Notes (not "encryption library")
  - [x] 1.3 Add install command section (`pip install adk-secure-sessions` / `uv add adk-secure-sessions`) with runtime dependency count: "**3 runtime dependencies**: google-adk, cryptography, aiosqlite" — verify list matches `pyproject.toml` `[project.dependencies]`
  - [x] 1.4 Write quick-start "after" code block (5 lines or fewer) showing exact swap from `BaseSessionService` to `EncryptedSessionService` — real, runnable code; supplementary "before" block for context does not count toward 5-line limit
    - [x] 1.4a Verify quick-start code imports resolve and example is syntactically valid
  - [x] 1.5 Add "What Gets Encrypted" table after quick-start, before links — verify every row is accurate against current implementation
  - [x] 1.6 Add links section: documentation (GitHub `docs/` tree view as interim — add HTML comment `<!-- Update to https://alberto-codes.github.io/adk-secure-sessions/ when MkDocs deploys (Story 2.2) -->`), SECURITY.md, contributing, license
  - [x] 1.7 Verify section hierarchy matches AC: badges > one-liner > install > quick-start > what gets encrypted > links
  - [x] 1.8 Verify README is under 80 lines

- [x] Task 2: Run quality gates (AC: all)
  - [x] 2.1 `pre-commit run --all-files` — all 7 hooks pass
  - [x] 2.2 Verify no test regressions: `uv run pytest` — 167 passed, 99.68% coverage

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1 (tagline) | Manual: README line 10 — "The compliance gateway for Google ADK — add encrypted sessions in 5 minutes." | pass |
| 1 (hierarchy) | Manual: README structure — badges (L1-6) > one-liner (L10-12) > install (L14-22) > quick-start (L24-38) > what gets encrypted (L40-47) > links (L49-57) | pass |
| 1 (quick-start) | Manual: "After" block is 4 lines (import + 3-line constructor). Imports verified: `uv run python -c "from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET"` succeeds | pass |
| 1 (badges) | Manual: 5 badges present — CI, License, PyPI, Python, Coverage. HTML comment on L1: `<!-- PyPI badges activate on first publish (Story 1.11) -->`. CI + license render now; PyPI badges auto-resolve on publish. Coverage uses static badge (no Codecov configured). | pass |
| 1 (verifiable) | Manual: License badge present; "3 runtime dependencies: google-adk, cryptography, aiosqlite" on L22; coverage badge shows 99% | pass |
| 1 (links) | Manual: Links section (L49-57) — Documentation (GitHub docs/ tree, HTML comment for MkDocs on L50), SECURITY.md, CONTRIBUTING.md, Roadmap, License | pass |
| 1 (NFR28) | Manual: README is 60 lines; install command on L16; quick-start on L26-35; a developer reading sequentially reaches working encrypted code in ~2 minutes | pass |

## Dev Notes

### What This Story Does

This story **rewrites** the existing README.md. The current README is comprehensive (142 lines) but positions the library as an "encrypted session storage" — a technical description that misses the compliance value proposition. The rewrite must reposition it as a **compliance gateway** and simplify the structure to get developers from discovery to working code in under 5 minutes.

This is a documentation-only story — no Python code changes, no test changes.

### Current README Analysis

The current README (`README.md`, 142 lines) has:
- Title + 2-paragraph description (good detail, but verbose for discovery)
- "The Problem" section (useful but should be implicit in the tagline)
- "What This Package Does" section (4 bullets)
- Installation section (pip and uv)
- Quick Start (12 lines of code — too long for 5-line target)
- "What Gets Encrypted" table
- EncryptionBackend Protocol section
- Encryption Backends table (current + future)
- "How It Works" section with data flow diagram
- Project Status section
- Development section
- License section

**What changes:**
- **Remove**: "The Problem", "EncryptionBackend Protocol", "Encryption Backends" (future), "How It Works", "Project Status", "Development" — these belong in the documentation site, not the README
- **Keep**: "What Gets Encrypted" table — place after quick-start, before links (6-line trust signal for compliance reviewers)
- **Add**: Badge row, compliance gateway tagline, runtime dependency count
- **Simplify**: Quick-start from 12 lines to ≤5 lines (the "after" block)
- **Restructure**: badges > one-liner > install > quick-start > what gets encrypted > links

### Tagline Candidates

The dev agent should choose or adapt from these candidate taglines (positioning as "Compliance Gateway," not "encryption library"):

1. *"The compliance gateway for Google ADK — add encrypted sessions in 5 minutes."*
2. *"Compliance-ready session encryption for Google ADK — drop-in, audit-ready, 5 minutes to integrate."*
3. *"Drop-in encrypted sessions for Google ADK — from plaintext to audit-ready in 5 minutes."*

Pick the one that fits best under the badge row, or adapt to a shorter one-liner variant. The key elements: "compliance" or "audit-ready" (positioning), "Google ADK" (context), "drop-in" or "5 minutes" (low effort).

### Badge Specifications

Use shields.io badges with the following URLs (GitHub repository: `Alberto-Codes/adk-secure-sessions`):

1. **CI test status**: `https://img.shields.io/github/actions/workflow/status/Alberto-Codes/adk-secure-sessions/ci.yml?branch=develop&label=tests` — links to GitHub Actions. Workflow filename is **`ci.yml`** (verified).
2. **License**: `https://img.shields.io/github/license/Alberto-Codes/adk-secure-sessions` — reads LICENSE file from repo (works without PyPI publish)
3. **PyPI version**: `https://img.shields.io/pypi/v/adk-secure-sessions` — links to PyPI project page
4. **Python version**: `https://img.shields.io/pypi/pyversions/adk-secure-sessions` — shows supported Python versions from classifiers
5. **Coverage**: Check `.github/workflows/ci.yml` for Codecov or similar upload steps. If no coverage service is configured, use a static badge (e.g., `https://img.shields.io/badge/coverage-99%25-brightgreen`) or omit until a coverage service is added.

**PyPI badge strategy**: The package is NOT yet published to PyPI (Story 1.11 handles CI/CD publish). Include all badge markdown now — CI + license badges render correctly today. PyPI-dependent badges (version, Python version) will show "not found" until first publish, then auto-resolve. Add an HTML comment in the README: `<!-- PyPI badges activate on first publish (Story 1.11) -->`. This is acceptable — the badge markdown is the deliverable and it self-heals on publish.

### Quick-Start Code Requirements

The AC specifies "5 lines or fewer" — this limit applies to the **"after" (encrypted) code block only**. A supplementary "before" block showing the ADK default is context and does not count toward the 5-line limit.

**Verified constructor signature** (from `src/adk_secure_sessions/services/encrypted_session.py:138`):

```python
def __init__(
    self,
    db_path: str,
    backend: EncryptionBackend,
    backend_id: int,    # REQUIRED — no default value
) -> None:
```

All three parameters are **required**. `backend_id` has NO default. The quick-start MUST include `BACKEND_FERNET`.

**Example quick-start (4 lines for "after" block):**

```python
# Before (ADK default — unencrypted):
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")

# After (encrypted — swap the import and constructor):
from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET
session_service = EncryptedSessionService(
    db_path="sessions.db", backend=FernetBackend("your-secret-key"), backend_id=BACKEND_FERNET
)
```

**Guardrails for the quick-start:**
- Must use real import paths that match `__init__.py` exports: `from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET`
- `EncryptedSessionService` constructor requires ALL three args: `db_path` (str), `backend` (EncryptionBackend instance), `backend_id` (int) — `backend_id` is **required, no default**
- `FernetBackend` constructor takes a passphrase string
- `BACKEND_FERNET` IS needed in the quick-start — it's a required parameter (party mode research confirmed no default exists)
- Show the "before and after" pattern: ADK default vs encrypted — this makes the "drop-in" value proposition tangible
- The code must be runnable (no pseudocode, no `...` placeholders for important parts)
- **Verify the quick-start imports resolve and the example is syntactically valid** before marking Task 1.4 done

### Links Section

The README must link to:
1. **Documentation**: Link to GitHub `docs/` tree view as interim: `https://github.com/Alberto-Codes/adk-secure-sessions/tree/develop/docs` — the `docs/` folder has real content (ARCHITECTURE.md, 6 ADRs, ROADMAP.md, development-guide, contributing guide). Add an HTML comment: `<!-- Update to https://alberto-codes.github.io/adk-secure-sessions/ when MkDocs deploys (Story 2.2) -->` as a breadcrumb for the future dev agent.
2. **SECURITY.md**: Link to `SECURITY.md` (relative link within the repo)
3. **Contributing**: Link to contributing guidelines if they exist, or to the development section
4. **License**: Link to `LICENSE` file

### Critical Guardrails

- **DO NOT** claim the package is published on PyPI yet — use future tense or conditional language if referencing PyPI availability
- **DO NOT** mention specific compliance certifications (HIPAA, SOC 2, PCI-DSS) as if the library provides them — the library **supports** encryption at rest, certification is the deployer's responsibility. The current README handles this well; preserve that nuance.
- **DO NOT** mention SQLCipher, AWS KMS, GCP KMS, or HashiCorp Vault in the README — future backends belong in the roadmap/docs site, not the README (Story 1.8 review learning: "SECURITY.md is a policy document, not a product brochure" — same principle applies to README)
- **DO NOT** include the "EncryptionBackend Protocol" section — this is API documentation, belongs in docs site
- **DO NOT** include the "How It Works" data flow diagram — belongs in docs site
- **DO** keep the README under 80 lines — this is a discovery document, not a manual
- **DO** keep the "What Gets Encrypted" table — place after quick-start, before links. Verify every row is accurate against current implementation. This is a 6-line trust signal that compliance reviewers look for.
- **DO** use the phrase "Compliance Gateway" in the tagline — this is the positioning from the epics AC
- **DO** make the license, dependency count, and test coverage visible (FR40) — license badge, "3 runtime dependencies: google-adk, cryptography, aiosqlite" near install section, coverage via badge or text
- **License is Apache-2.0** (not MIT — corrected in Story 1.8)

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `README.md` | REWRITE — compliance gateway positioning, simplified structure, badges, 5-line quick-start |

### Project Structure Notes

- Modifies: `README.md` in repository root
- No changes to `src/` directory
- No changes to `tests/` directory
- No changes to `pyproject.toml`
- Aligns with architecture Phase 2 requirements (FR34: quick-start, FR40: badges/verifiability)

### Previous Story Intelligence (1.8)

**Patterns established:**
- Documentation-only story — no Python code changes, no test changes
- 167 tests passing at 99.68% coverage (all quality gates green)
- `pre-commit run --all-files` runs 7 hooks: yamllint, actionlint, ruff-check, ruff-format, ty check, pytest, docvet
- License confirmed as Apache-2.0 (not MIT — epics reference to "MIT" was a spec error)
- SECURITY.md and LICENSE already exist in repo root
- pyproject.toml version is `0.1.1`

**Review learnings to carry forward:**
- Be precise about technical claims (Story 1.8 had PBKDF2 attribution issues — SECURITY.md said "handled by cryptography library" but code uses `hashlib.pbkdf2_hmac`)
- Verify task completion claims with actual file inspection
- Always run the full quality pipeline, not just individual checks
- Keep policy/discovery documents focused — don't turn them into product brochures

### Git Context

Recent commits on develop:
- `e7ab509` docs(security): add SECURITY.md and Apache-2.0 LICENSE
- `8553c4b` chore(deps-dev): bump griffe from 1.15.0 to 2.0.0
- `da9e10d` chore(deps-dev): update uv-build requirement from <0.10.0 to <0.11.0
- `f1e1103` chore(deps): bump the minor-and-patch group with 10 updates
- `e0b506c` chore(deps): bump the github-actions group with 3 updates

This story follows a documentation story (1.8). No code conflicts expected. Conventional commit format for this story: `docs(readme): <description>`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.9]
- [Source: _bmad-output/planning-artifacts/prd.md#FR34 — Quick-start code example]
- [Source: _bmad-output/planning-artifacts/prd.md#FR40 — Badges and verifiability]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR28 — 5-minute integration time]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technology Foundation — badge and CI details]
- [Source: _bmad-output/implementation-artifacts/1-8-security-md.md#Dev Notes — previous story patterns]
- [Source: _bmad-output/project-context.md#Development Workflow Rules — conventional commits, PR rules]
- [Source: pyproject.toml — version 0.1.1, license Apache-2.0, project URLs]
- [Source: src/adk_secure_sessions/__init__.py — public API surface (13 symbols)]
- [Source: README.md — current state (142 lines) for rewrite baseline]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage (167 passed, 99.68%)
- [x] `pre-commit run --all-files` -- all 7 hooks pass

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
| 2026-03-01 | Story created by create-story workflow |
| 2026-03-01 | Party mode review (full roster): 8 consensus items applied. (1) Added 3 candidate taglines for dev agent. (2) Badge strategy: include all markdown now, CI+license work today, PyPI badges auto-resolve on publish, fixed ci.yml filename. (3) Keep "What Gets Encrypted" table after quick-start. (4) Docs link: GitHub docs/ tree as interim, HTML comment for future MkDocs URL. (5) Branch renamed to docs/readme-1-9-rewrite. (6) Clarified 5-line limit applies to "after" block only; fixed BACKEND_FERNET guardrail (required, no default). (7) Embedded verified constructor signature; added import validation subtask. (8) Added concrete dependency list task (3 runtime deps near install section). |
| 2026-03-01 | Dev implementation complete. README rewritten from 142 lines to 60 lines. Compliance gateway positioning, 5 badges, before/after quick-start (4-line "after" block), "What Gets Encrypted" table preserved, links to GitHub docs/ tree. Imports verified. No coverage upload service found — used static badge. All 7 pre-commit hooks pass, 167 tests at 99.68% coverage. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Documentation-only story — no Python code changes, no test changes
- README rewritten from 142 lines to 60 lines (58% reduction)
- Tagline chosen: candidate 1 — "The compliance gateway for Google ADK — add encrypted sessions in 5 minutes."
- Quick-start "after" block is 4 lines (import + 3-line constructor with all required params)
- Imports verified via `uv run python -c "from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET"`
- No Codecov or coverage upload service configured in CI — used static badge (99% coverage)
- "What Gets Encrypted" table preserved and verified against `encrypted_session.py` encrypt/decrypt call sites
- Docs link uses GitHub `docs/` tree view as interim; HTML comment breadcrumb for Story 2.2 MkDocs deployment
- All 7 pre-commit hooks pass: yamllint, actionlint, ruff-check, ruff-format, ty check, pytest, docvet
- 167 tests passing at 99.68% coverage — no regressions

### File List

- `README.md` — **REWRITTEN** — Compliance gateway positioning, badges, 60-line simplified structure with before/after quick-start
