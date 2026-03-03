# Story 2.5: FAQ Page

Status: review
Branch: feat/docs-2-5-faq-page
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/95

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer with common questions about the library**,
I want **a FAQ page answering key questions about algorithms, compliance, and architecture**,
so that **I don't need to read the full ADR trail to understand basic decisions**.

## Acceptance Criteria

1. **Given** the PRD and user journeys identify common evaluator questions
   **When** a FAQ page is created in the docs site
   **Then** it answers at minimum these 6 questions:
     1. "What algorithms does Fernet use?"
     2. "Is this HIPAA compliant?" — answer MUST use exact PRD positioning language: "Designed to support encryption-at-rest requirements for HIPAA, SOC 2, PCI-DSS, and GDPR regulated environments. Certification belongs to the deploying organization." Never claim certification.
     3. "Why Protocols not ABC?"
     4. "Can I use a different encryption backend?"
     5. "What happens if I use the wrong decryption key?" — explains DecryptionError, never silent corruption
     6. "Does this encrypt the entire database or just session data?" — explains field-level vs. full-DB
   **And** answers are concise (3-5 sentences each) with links to detailed docs where applicable
   **And** the page ends with a `## Related` section linking to sibling pages (matching the pattern in `algorithms.md` and `envelope-protocol.md`)

2. **Given** the FAQ page exists at `docs/faq.md`
   **When** the MkDocs site is built with `uv run mkdocs build --strict`
   **Then** the FAQ is accessible from the docs site navigation between Roadmap and Changelog
   **And** the build completes with zero errors and zero warnings
   **And** all cross-reference links in the FAQ resolve correctly
   **Note:** docvet pre-commit hook only checks `.py` files — `mkdocs build --strict` is the real validation gate for `.md` files

## Tasks / Subtasks

- [x] Task 1: Create `docs/faq.md` with 6 required FAQ entries (AC: #1)
  - [x] 1.1 Create `docs/faq.md` with page title `# Frequently Asked Questions`. Use `##` (H2) headings for each question — matches the heading pattern in `algorithms.md` and `envelope-protocol.md`. Each answer is a paragraph directly below its H2 heading.
  - [x] 1.2 Write Q1: "What algorithms does Fernet use?" — 3-5 sentences covering AES-128-CBC + HMAC-SHA256, PBKDF2 key derivation, and link to `algorithms.md` for full detail. Tone: confident and direct (technical audience).
  - [x] 1.3 Write Q2: "Is this HIPAA compliant?" — use **exact** PRD positioning language: "Designed to support encryption-at-rest requirements for HIPAA, SOC 2, PCI-DSS, and GDPR regulated environments. Certification belongs to the deploying organization." Link to `ROADMAP.md` for FIPS deployment guide (Phase 4). Never claim certification. Tone: precise with deliberate hedging (compliance audience).
  - [x] 1.4 Write Q3: "Why Protocols not ABC?" — explain PEP 544 structural subtyping, no inheritance needed for third-party backends, runtime validation via `isinstance()`. Link to `adr/ADR-001-protocol-based-interfaces.md`. Tone: confident and direct (technical audience).
  - [x] 1.5 Write Q4: "Can I use a different encryption backend?" — explain that any class conforming to the `EncryptionBackend` protocol works **today** (you don't need to wait for Phase 3). Mention Phase 3 AES-256-GCM and Phase 4 KMS backends as planned additions. Explain that the envelope protocol enables backend coexistence — old Fernet data (backend ID `0x01`) coexists with new backend data, so migration is zero-downtime. Link to `envelope-protocol.md` and `ROADMAP.md`. Tone: confident and direct (technical audience).
  - [x] 1.6 Write Q5: "What happens if I use the wrong decryption key?" — explain `DecryptionError` is always raised, never silent corruption or garbage data (FR22, NFR7). Link to API reference for exceptions. Tone: confident and direct (technical audience).
  - [x] 1.7 Write Q6: "Does this encrypt the entire database or just session data?" — explain field-level encryption: state values and event data are encrypted, while session metadata (session_id, app_name, user_id, timestamps) remains queryable. Link to `adr/ADR-003-field-level-encryption.md`. Tone: precise with deliberate hedging (compliance audience).
  - [x] 1.8 Add a `## Related` section at the end of the page linking to sibling docs: Algorithm Documentation, Envelope Protocol, Architecture Decisions, Roadmap. Matches the footer pattern in `algorithms.md` and `envelope-protocol.md`.
  - [x] 1.9 Verify each answer is 3-5 sentences with at least one cross-reference link to detailed docs

- [x] Task 2: Add FAQ to MkDocs site navigation (AC: #2)
  - [x] 2.1 Replace the placeholder comment `# Story 2.5 adds: - FAQ: faq.md` in `mkdocs.yml` (line 162) with the actual nav entry: `  - FAQ: faq.md` (2-space indent, matching sibling entries like `  - Roadmap: ROADMAP.md` and `  - Changelog: changelog.md`)
  - [x] 2.2 Place FAQ in nav between "Roadmap" and "Changelog" (preserving existing order)

- [x] Task 3: Run quality gates (AC: #1)
  - [x] 3.1 `uv run mkdocs build --strict` — zero warnings, zero errors, FAQ page renders correctly
  - [x] 3.2 `pre-commit run --all-files` — all hooks pass
  - [x] 3.3 `uv run ruff check .` — zero lint violations
  - [x] 3.4 `uv run pytest` — all tests pass (no regressions, documentation-only story)
  - [x] 3.5 Verify all 6 FAQ entries render with correct markdown formatting and working links

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `uv run mkdocs build --strict` renders `docs/faq.md`; page contains all 6 questions with concise answers (3-5 sentences), cross-reference links, and `## Related` footer | pass |
| 2    | `uv run mkdocs build --strict` zero errors; FAQ in nav between Roadmap and Changelog; all cross-reference links resolve; `pre-commit run --all-files` passes all hooks | pass |

## Dev Notes

### What This Story Does

This story creates a new `docs/faq.md` page and adds it to the MkDocs site navigation. The FAQ answers 6 specific questions identified in the PRD and user journeys, with concise answers and links to detailed documentation.

### FAQ Answer Tone Guidance

The FAQ serves two distinct audiences — tone should match:

- **Technical questions (Q1, Q3, Q4, Q5):** Confident and direct. Solo developers want quick, authoritative answers. No hedging on technical facts.
- **Compliance questions (Q2, Q6):** Precise with deliberate hedging. Compliance reviewers need defensible language. Use exact PRD positioning — never overclaim, never underclaim.

### What Already Exists (Do NOT Recreate)

| Component | Status | File |
|-----------|--------|------|
| MkDocs site with strict builds | Complete | `mkdocs.yml`, `.github/workflows/docs.yml` |
| Algorithm Documentation page (cross-ref target) | Complete | `docs/algorithms.md` |
| Envelope Protocol page (cross-ref target) | Complete | `docs/envelope-protocol.md` |
| ADR-001: Protocol-Based Interfaces (cross-ref target) | Complete | `docs/adr/ADR-001-protocol-based-interfaces.md` |
| ADR-003: Field-Level Encryption (cross-ref target) | Complete | `docs/adr/ADR-003-field-level-encryption.md` |
| Roadmap page (cross-ref target) | Complete | `docs/ROADMAP.md` |
| Nav placeholder for FAQ | Ready | `mkdocs.yml` line 162 (`# Story 2.5 adds: - FAQ: faq.md`) |
| API Reference (cross-ref target) | Complete | `docs/reference/` (auto-generated) |

### Compliance Language — CRITICAL

The answer to "Is this HIPAA compliant?" **MUST** use the exact PRD positioning language. Do NOT paraphrase:

> "Designed to support encryption-at-rest requirements for HIPAA, SOC 2, PCI-DSS, and GDPR regulated environments. Certification belongs to the deploying organization."

Never claim the library IS certified or compliant. The library enables compliance; certification is the deployer's responsibility.

[Source: `_bmad-output/planning-artifacts/prd.md` — Compliance Framework Mapping section]

### FAQ Content Sources

Each question maps to a specific source document:

| Question | Primary Source | Cross-Reference Link |
|----------|---------------|---------------------|
| Q1: What algorithms does Fernet use? | `docs/algorithms.md` | `[Algorithm Documentation](algorithms.md)` |
| Q2: Is this HIPAA compliant? | PRD — Compliance Framework Mapping | `[Roadmap](ROADMAP.md)` (FIPS guide in Phase 4) |
| Q3: Why Protocols not ABC? | `docs/adr/ADR-001-protocol-based-interfaces.md` | `[ADR-001](adr/ADR-001-protocol-based-interfaces.md)` |
| Q4: Can I use a different backend? | `docs/envelope-protocol.md`, `docs/ROADMAP.md` | `[Envelope Protocol](envelope-protocol.md)`, `[Roadmap](ROADMAP.md)` |
| Q5: Wrong decryption key? | FR22, NFR7, `src/adk_secure_sessions/exceptions.py` | API Reference for `DecryptionError` |
| Q6: Entire database or just session data? | `docs/adr/ADR-003-field-level-encryption.md` | `[ADR-003](adr/ADR-003-field-level-encryption.md)` |

### Cross-Reference Link Format

Use **relative paths from `docs/` root** for all cross-references:
- `[Algorithm Documentation](algorithms.md)` — NOT `[Algorithm Documentation](docs/algorithms.md)`
- `[ADR-001](adr/ADR-001-protocol-based-interfaces.md)` — include the `adr/` subdirectory
- `[Envelope Protocol](envelope-protocol.md)` — same level as `faq.md`

### FAQ Markdown Structure

Use `##` (H2) headings for each question, with the answer as a paragraph directly below. This matches the heading pattern in `algorithms.md` and `envelope-protocol.md`, is scannable, and works well with MkDocs search indexing.

End the page with a `## Related` section containing a bullet list of links to sibling docs — this is the established pattern across all standalone docs pages.

### Anti-Patterns to Avoid

- **DO NOT** create any source code files — this is a documentation-only story
- **DO NOT** modify any existing `.md` files other than `mkdocs.yml` — FAQ is a new page
- **DO NOT** add `@pytest.mark.asyncio` — project uses `asyncio_mode = "auto"`
- **DO NOT** claim HIPAA/SOC2/PCI-DSS certification — use exact PRD positioning language only
- **DO NOT** write long answers — each answer is 3-5 sentences max, with links to detailed docs
- **DO NOT** add a FAQ entry for questions not in the AC — stick to the 6 required questions (additional questions can be added in future stories)
- **DO NOT** use `::` directive for code examples — use fenced triple-backtick blocks (griffe/mkdocstrings requirement)

### Code Review Focus

This is a documentation-only story. Code review should focus on:
- **Content accuracy** — do FAQ answers match source documents (ADRs, algorithms.md, PRD)?
- **Compliance language precision** — does Q2 use the exact PRD positioning language?
- **Cross-reference link validity** — do all relative links resolve in `mkdocs build --strict`?
- **NOT** code patterns, test coverage, or source code style (no source code is modified)

### Docvet vs MkDocs Strict

docvet pre-commit hook only checks `.py` files (`types: [python]`), not `.md` files. For this documentation-only story, `uv run mkdocs build --strict` is the real validation gate — it catches broken links, invalid nav entries, and malformed markdown. Do not expect docvet to validate `docs/faq.md`.

### CI Constraint: Draft PRs Skip Docs Build

The `docs.yml` workflow only runs on non-draft PRs. Since project convention is always draft PRs, verify locally with `uv run mkdocs build --strict` during development.

### Previous Story Intelligence (2.4)

From Story 2.4 (Published Roadmap on Documentation Site):
- MkDocs strict builds enforce valid markdown links and nav entries — broken links fail the build
- `git-revision-date-localized-plugin` warnings for newly created files are expected and don't fail strict mode
- MkDocs Material prints a MkDocs 2.0 compatibility banner — visual only, does NOT fail `--strict`
- docvet only checks `.py` files (types: [python]), not `.md` — real markdown validation is `mkdocs build --strict`
- 174 tests pass, 9/9 pre-commit hooks pass, zero lint violations
- Use relative paths from `docs/` root for cross-references (e.g., `[Envelope Protocol](envelope-protocol.md)`)
- Story 2.4 added a public API surface guardrail test (`tests/unit/test_public_api.py`) — don't recreate
- Code review findings from 2.4: always verify quality gates actually pass before marking them `[x]`

### Git Intelligence

Recent commits on `main`:
- `1357afd` — `docs(roadmap): update completion status, add backend upgrade schedule (#94)` — Story 2.4 merge
- `f76555a` — `docs(architecture): add envelope protocol and algorithm specification pages (#92)` — Story 2.3 merge
- `cd3eca5` — `fix(release): guard fromJSON with short-circuit to prevent empty parse (#90)` — Release automation fix
- Codebase is stable post-Story 2.4. No active development branches.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/faq.md` | New — FAQ page with 6 questions and concise answers |
| `mkdocs.yml` | Modified — uncomment/add FAQ nav entry |

### Peripheral Config Impact

| File | Change | Reason |
|------|--------|--------|
| `docs/faq.md` | New file | Core deliverable |
| `mkdocs.yml` | Modified (line 162) | Replace comment placeholder with nav entry |
| `.github/workflows/docs.yml` | No changes | Already strict from Story 2.2 |
| `pyproject.toml` | No changes | No new deps |
| `.pre-commit-config.yaml` | No changes | docvet already configured |
| Source code (`src/`) | No changes | Documentation-only story |
| Tests (`tests/`) | No changes | No code changes to test |

### Project Structure Notes

- `docs/faq.md` goes in `docs/` root alongside `algorithms.md`, `envelope-protocol.md`, `ROADMAP.md` — consistent with existing flat structure for standalone pages
- No new directories created
- Nav position: between Roadmap and Changelog (matching the epics file's original nav plan)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5 — FAQ Page]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2 — Documentation & Compliance Credibility]
- [Source: _bmad-output/planning-artifacts/prd.md — Compliance Framework Mapping, positioning language]
- [Source: docs/algorithms.md — Fernet algorithm details, NIST/FIPS references]
- [Source: docs/envelope-protocol.md — Binary layout, backend coexistence]
- [Source: docs/adr/ADR-001-protocol-based-interfaces.md — Protocol vs ABC rationale]
- [Source: docs/adr/ADR-003-field-level-encryption.md — Field-level vs full-DB encryption]
- [Source: docs/ROADMAP.md — Phase timeline, FIPS deployment guide (Phase 4)]
- [Source: mkdocs.yml — Nav structure (line 162, FAQ placeholder)]
- [Source: _bmad-output/implementation-artifacts/2-4-published-roadmap-on-documentation-site.md — Previous story learnings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage
- [x] `pre-commit run --all-files` -- all hooks pass
- [x] `uv run mkdocs build --strict` -- zero errors, FAQ page renders correctly

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
| 2026-03-02 | Story created by create-story workflow. Documentation-only story: create `docs/faq.md` with 6 required FAQ entries (algorithms, compliance, protocols, backends, wrong key, field-level encryption), add to MkDocs nav. No source code changes. |
| 2026-03-02 | Party mode consensus (7 agents: Paige, Winston, John, Amelia, Bob, Murat, Quinn): 8 findings applied — (1) added FAQ markdown structure guidance (H2 headings matching sibling pages), (2) added `## Related` footer pattern, (3) enriched Q4 with protocol-works-today + envelope coexistence guidance, (4) added tone guidance (direct for tech Qs, precise for compliance Qs), (5) specified nav entry 2-space indentation, (6) split into 2 ACs for cleaner tracking, (7) added code review focus note (content accuracy, not code patterns), (8) clarified docvet doesn't check `.md` — mkdocs strict is the real gate. |
| 2026-03-02 | Implementation complete: created `docs/faq.md` with 6 FAQ entries, added nav entry in `mkdocs.yml` between Roadmap and Changelog. All quality gates pass (mkdocs strict, pre-commit 9/9, ruff, pytest 174 passed). |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Clean implementation.

### Completion Notes List

- Created `docs/faq.md` with 6 FAQ entries using H2 headings, matching the heading pattern in `algorithms.md` and `envelope-protocol.md`
- Q1 (algorithms): Covers AES-128-CBC + HMAC-SHA256 + PBKDF2, links to algorithms.md (5 sentences)
- Q2 (compliance): Uses exact PRD positioning language verbatim, links to ROADMAP.md for FIPS guide (5 sentences)
- Q3 (protocols): Explains PEP 544 structural subtyping + @runtime_checkable, links to ADR-001 (4 sentences)
- Q4 (backends): Emphasizes works-today + envelope coexistence for zero-downtime migration, links to envelope-protocol.md and ROADMAP.md (5 sentences)
- Q5 (wrong key): Explains DecryptionError always raised, never silent corruption, links to exceptions API reference (5 sentences)
- Q6 (field-level): Explains what's encrypted vs queryable, links to ADR-003 (4 sentences)
- Added `## Related` footer with links to Algorithm Documentation, Envelope Protocol, Architecture Decisions, Roadmap
- Replaced placeholder comment in `mkdocs.yml` with nav entry between Roadmap and Changelog
- All 11 cross-reference links use relative paths from docs/ root and resolve in strict build

### File List

- `docs/faq.md` — New: FAQ page with 6 questions, concise answers, cross-reference links, and Related footer
- `mkdocs.yml` — Modified: replaced placeholder comment with `- FAQ: faq.md` nav entry (line 162)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Modified: story status ready-for-dev → in-progress → review
- `_bmad-output/implementation-artifacts/2-5-faq-page.md` — Modified: task checkboxes, AC-to-Test, Quality Gates, Dev Agent Record, Change Log, Status
