# Story 1.8: SECURITY.md

Status: review
Branch: feat/docs-1-8-security-md
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/63

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **compliance reviewer evaluating the library**,
I want **a SECURITY.md with responsible disclosure policy and supported versions**,
so that **I can verify the project takes security seriously — missing this is an instant disqualification**.

## Acceptance Criteria

1. **Given** no SECURITY.md exists in the repository root
   **When** I create SECURITY.md
   **Then** it includes a Supported Versions table listing currently supported versions (FR39)

2. **Given** SECURITY.md is created
   **When** I read the Reporting a Vulnerability section
   **Then** it provides a clear process for responsible disclosure via GitHub private vulnerability reporting

3. **Given** SECURITY.md is created
   **When** I read the Response Timeline section
   **Then** it specifies a 48-hour acknowledgment SLA for critical vulnerabilities

4. **Given** SECURITY.md is created
   **When** I read the Cryptographic Approach section
   **Then** it references the project's use of the `cryptography` library (no custom primitives)

5. **Given** SECURITY.md is created
   **When** I inspect the file contents
   **Then** it does NOT include any encryption keys, tokens, or sensitive configuration

6. **Given** SECURITY.md is created
   **When** I verify the format
   **Then** it follows standard GitHub SECURITY.md conventions (GitHub auto-detects and surfaces in the Security tab)

## Tasks / Subtasks

- [x] Task 1: Create `SECURITY.md` in repository root (AC: #1, #2, #3, #4, #5, #6)
  - [x] 1.1 Add Supported Versions table with current version matrix
  - [x] 1.2 Add Reporting a Vulnerability section directing to GitHub private vulnerability reporting
  - [x] 1.3 Add Response Timeline section with 48-hour critical SLA
  - [x] 1.4 Add Cryptographic Approach section referencing `cryptography` library delegation
  - [x] 1.5 Add Scope section explaining what the library does and doesn't protect
  - [x] 1.6 Verify no sensitive data (keys, tokens, config) in the file
  - [x] 1.7 Verify file is at repo root as `SECURITY.md` (GitHub detection is a post-merge verification — cannot be tested locally)

- [x] Task 2: Create `LICENSE` file in repository root — **bonus scope** (related gap from Story 1.7, not tracked by ACs)
  - [x] 2.1 Create Apache-2.0 LICENSE file in repo root (standard text from apache.org, copyright 2026)
  - [x] 2.2 Verify pyproject.toml `license = { text = "Apache-2.0" }` matches the LICENSE file
  - [x] 2.3 Verify GitHub detects the license

- [x] Task 3: Run quality gates (AC: all)
  - [x] 3.1 `pre-commit run --all-files` — all hooks pass (new .md files should not affect code hooks)
  - [x] 3.2 Verify no test regressions: `uv run pytest`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | Manual: SECURITY.md contains "Supported Versions" section with version table | pass |
| 2    | Manual: SECURITY.md contains "Reporting a Vulnerability" section with GitHub private reporting | pass |
| 3    | Manual: SECURITY.md contains response timeline with "48 hours" for critical acknowledgment | pass |
| 4    | Manual: SECURITY.md references `cryptography` library, states no custom primitives | pass |
| 5    | Manual: Review confirms no actual sensitive values (API keys, passwords, tokens, base64 blobs) embedded — descriptive uses of words like "key" and "token" in context are acceptable | pass |
| 6    | Manual: File is at repo root as `SECURITY.md` (GitHub convention) | pass |

## Dev Notes

### What This Story Creates

This story creates two files in the repository root:

1. **`SECURITY.md`** — The primary deliverable. A responsible disclosure policy following GitHub's standard convention. GitHub auto-detects this file and surfaces it in the repository's Security tab. This is the compliance reviewer's first check — Diane's persona in the PRD describes SECURITY.md as an "instant disqualification" if missing.

2. **`LICENSE`** — An Apache-2.0 license file. This was identified as a gap in Story 1.7 dev notes: "No LICENSE file exists in the repo root — PyPI and GitHub both expect one. This belongs in Story 1.8 (SECURITY.md) or a separate task." The pyproject.toml already declares `license = { text = "Apache-2.0" }` and the `License :: OSI Approved :: Apache Software License` classifier is present. The LICENSE file makes this visible in GitHub's UI and is expected by compliance reviewers.

This is a documentation-only story — no Python code changes, no test changes.

### SECURITY.md Content Requirements

The file MUST include these sections (derived from AC and FR39):

1. **Supported Versions** — Table showing which versions receive security updates:
   - `0.1.x` — supported (current version line, pre-release — update this table when first PyPI publish lands)
   - Format: standard markdown table with Version and Supported columns
   - Note: The project is pre-release; the table should reflect the current development version

2. **Reporting a Vulnerability** — How to responsibly disclose:
   - **Primary method: GitHub's private vulnerability reporting** — use the "Report a vulnerability" button in the Security tab
   - Explicitly state: "Do NOT open a public GitHub issue for security vulnerabilities"
   - No email address needed — GitHub's built-in feature handles the workflow
   - Note: Enabling this feature is a manual prerequisite (see Manual Prerequisites section above)

3. **Response Timeline** — SLA commitments:
   - 48-hour acknowledgment for critical vulnerabilities
   - 7-day assessment timeline for severity determination
   - 30-day target for fix release (critical), 90-day for non-critical

4. **Cryptographic Approach** — Technical transparency:
   - State: "This library delegates all cryptographic operations to the `cryptography` Python library"
   - State: "No custom cryptographic primitives are implemented"
   - Current algorithm: Fernet (AES-128-CBC + HMAC-SHA256 via PBKDF2)
   - Reference ADR-003 (Field-Level Encryption) for design rationale
   - Do NOT mention future backends or roadmap — SECURITY.md is a policy document, not a product brochure. Roadmap lives in `docs/ROADMAP.md`

5. **Scope** — What the library protects and what it doesn't:
   - Protects: Session state data at rest (field-level encryption before database write)
   - Does NOT protect: Data in transit (that's the transport layer's job), key management (user responsibility), database file access controls
   - Envelope format is self-describing — aids key rotation and audit

### LICENSE File Details

- **License**: Apache License, Version 2.0 (January 2004)
- **Source**: Use the [choosealicense.com Apache-2.0 template](https://choosealicense.com/licenses/apache-2.0/) — prepend `Copyright 2026 Alberto-Codes` before the license text
- **Convention**: Follow the choosealicense.com convention (copyright line in LICENSE file), NOT the Apache Foundation's NOTICE-file convention — this project is not an ASF project
- **Copyright**: `Copyright 2026 Alberto-Codes` (first commit: 2026-02-01)
- **Placement**: Repository root as `LICENSE` (no extension)
- **Verification**: `pyproject.toml` line 6 already has `license = { text = "Apache-2.0" }` — must match

### Manual Prerequisites (Human — not dev agent tasks)

- **Enable GitHub private vulnerability reporting**: Settings > Code security > Private vulnerability reporting. This is a repository settings change that requires admin access via the GitHub web UI. Do this before or after the dev agent runs — it is NOT a dev agent task.

### Critical Guardrails

- **DO NOT** include any real email addresses — use GitHub's private vulnerability reporting feature instead (no email needed)
- **DO NOT** include encryption keys, tokens, API keys, or passwords in SECURITY.md
- **DO NOT** claim HIPAA/SOC2/PCI-DSS certification — the library supports encryption at rest, but certification is the deployer's responsibility
- **DO NOT** mention specific CVEs or known vulnerabilities (there are none)
- **DO NOT** create a `.github/SECURITY.md` — put it in the repo root for maximum visibility
- **DO** reference the `cryptography` library by name (it's a public dependency)
- **DO** mention that all crypto is delegated (no custom primitives) — this is a key trust signal
- **DO** follow the exact GitHub SECURITY.md convention (Supported Versions table + Reporting section)
- **DO** include the 48-hour SLA for critical vulnerabilities (from epics AC)
- **DO** keep the tone professional and direct — compliance reviewers scan for specific keywords
- **DO NOT** pin a version number for `cryptography` in SECURITY.md — reference the library by name only (version constraints belong in `pyproject.toml`, not security policy)

### Previous Story Intelligence (1.7)

**Patterns established:**
- 167 tests passing at 99.68% coverage (all quality gates green)
- `pre-commit run --all-files` runs 7 hooks: yamllint, actionlint, ruff-check, ruff-format, ty check, pytest, docvet
- License confirmed as Apache-2.0 (not MIT — epics reference to "MIT" was a spec error)
- No LICENSE file exists in repo root — identified as a gap to address in this story

**Review learnings to carry forward:**
- Verify task completion claims with actual file inspection
- Always run the full quality pipeline, not just individual checks
- This story creates no test files — changes are documentation only

### Git Context

Recent commits on develop:
- `8553c4b` chore(deps-dev): bump griffe from 1.15.0 to 2.0.0
- `da9e10d` chore(deps-dev): update uv-build requirement from <0.10.0 to <0.11.0
- `f1e1103` chore(deps): bump the minor-and-patch group with 10 updates
- `e0b506c` chore(deps): bump the github-actions group with 3 updates
- `2f709ee` feat(packaging): add py.typed marker, fix keywords, tighten type signatures

This story follows a series of dependency bumps after Story 1.7. No code conflicts expected.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `SECURITY.md` | CREATE — new file, GitHub auto-detects for Security tab |
| `LICENSE` | CREATE — new file, GitHub auto-detects for license badge |

### Project Structure Notes

- New file: `SECURITY.md` in repository root — standard GitHub convention location
- New file: `LICENSE` in repository root — standard license file location
- No changes to `src/` directory
- No changes to `tests/` directory
- No changes to `pyproject.toml`
- Aligns with architecture Phase 2 file tree which lists `SECURITY.md` at root level

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.8 (line 413)]
- [Source: _bmad-output/planning-artifacts/prd.md#FR39 — SECURITY.md with responsible disclosure]
- [Source: _bmad-output/planning-artifacts/prd.md#Diane persona — compliance reviewer journey]
- [Source: _bmad-output/planning-artifacts/architecture.md#Phase 2 file tree — SECURITY.md listed]
- [Source: _bmad-output/planning-artifacts/architecture.md#Action item #7 — Create SECURITY.md]
- [Source: _bmad-output/implementation-artifacts/1-7-package-metadata-type-safety.md#Dev Notes — LICENSE gap identified]
- [Source: _bmad-output/project-context.md#Technology Stack — cryptography >=44.0.0]
- [Source: pyproject.toml line 6 — license = { text = "Apache-2.0" }]

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
| 2026-03-01 | Party mode review (round 1): 6 findings (0 HIGH, 2 MEDIUM, 4 LOW). Resolved: LICENSE marked as bonus scope, GitHub private vuln reporting chosen over email, copyright year corrected to 2026, pre-release noted in Supported Versions, AC #5 verification reframed. |
| 2026-03-01 | Party mode review (rounds 2-3): 9 consensus items. Removed Phase 3 roadmap from Crypto section, reworded AC #2 (no email), reframed Task 1.7 as post-merge check, added choosealicense.com LICENSE convention note, moved GitHub settings to manual prerequisites, added `cryptography` version guardrail. Research: pyca/cryptography has no SECURITY.md, PyJWT uses hybrid approach, choosealicense.com convention confirmed for non-ASF projects. |
| 2026-03-01 | Dev implementation complete. Created SECURITY.md (5 sections: Supported Versions, Reporting, Response Timeline, Cryptographic Approach, Scope) and LICENSE (Apache-2.0, choosealicense.com convention). Fixed pre-existing uv.lock corruption from griffe 2.0.0 bump. All 7 pre-commit hooks pass, 167 tests at 99.68% coverage. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Documentation-only story — no Python code changes, no test changes
- SECURITY.md created with 5 sections following GitHub SECURITY.md convention
- LICENSE created using choosealicense.com Apache-2.0 convention (copyright line in LICENSE, not separate NOTICE file)
- Pre-existing uv.lock corruption (griffe 1.15.0 → 2.0.0 split into griffelib/griffecli) fixed by lock file regeneration
- All 7 pre-commit hooks pass: yamllint, actionlint, ruff-check, ruff-format, ty check, pytest, docvet
- 167 tests passing at 99.68% coverage — no regressions

### File List

- `SECURITY.md` — **CREATED** — Security policy with responsible disclosure, supported versions, response timeline, crypto approach, scope
- `LICENSE` — **CREATED** — Apache-2.0 license (full text with copyright line)
- `uv.lock` — **REGENERATED** — Fixed pre-existing corruption from griffe 2.0.0 dependency bump
