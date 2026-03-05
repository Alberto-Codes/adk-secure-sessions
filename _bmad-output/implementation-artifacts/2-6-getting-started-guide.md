# Story 2.6: Getting Started Guide

Status: done
Branch: feat/docs-2-6-getting-started-guide
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/100

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer adding encrypted sessions to an existing ADK agent**,
I want **a Getting Started guide with a full working example and verification steps**,
so that **I can go from install to encrypted sessions in under 5 minutes with confidence that it's working**.

## Acceptance Criteria

1. **Given** the README provides a 5-line quick-start swap
   **When** a Getting Started guide page is created at `docs/getting-started.md`
   **Then** it includes:
     1. Install command (`pip install adk-secure-sessions`)
     2. Full working agent example with encrypted sessions (complete runnable code, not just the swap)
     3. Verification step: how to confirm sessions are encrypted (e.g., inspect SQLite file)
     4. "What's next?" links to API Reference, Architecture Decisions, and FAQ
   **And** the guide supports NFR28: a developer can go from install to encrypted sessions in under 5 minutes
   **And** the example uses realistic session state (not empty dict or trivial placeholder)

2. **Given** the Getting Started page exists at `docs/getting-started.md`
   **When** the MkDocs site is built with `uv run mkdocs build --strict`
   **Then** the Getting Started page is accessible from the docs site navigation
   **And** the build completes with zero errors and zero warnings
   **And** all cross-reference links resolve correctly
   **Note:** docvet pre-commit hook only checks `.py` files — `mkdocs build --strict` is the real validation gate for `.md` files

## Tasks / Subtasks

- [x] Task 1: Create `docs/getting-started.md` (AC: #1)
  - [x] 1.1 Create `docs/getting-started.md` with page title `# Getting Started`
  - [x] 1.2 Write **Prerequisites** section: Python 3.12+, an existing ADK agent or willingness to create a minimal one
  - [x] 1.3 Write **Installation** section with `pip install adk-secure-sessions` (and `uv add adk-secure-sessions` alternative)
  - [x] 1.4 Write **Quick Start** section showing the import swap pattern (from README) as a bridge, then a full working async example below
  - [x] 1.5 Write **Full Working Example** section: a complete, runnable async script that creates an `EncryptedSessionService` with `FernetBackend`, creates a session with realistic state, retrieves it, and closes. Use `asyncio.run()` entry point so users can copy-paste and run directly
  - [x] 1.6 Write **Verify Encryption** section: show how to inspect the SQLite database file to confirm session state is stored as opaque encrypted bytes (not plaintext JSON). Suggest `sqlite3 sessions.db "SELECT hex(state) FROM sessions LIMIT 1;"` or Python snippet
  - [x] 1.7 Write **What's Next?** section with links to: API Reference (`reference/index.md`), Architecture Decisions (`adr/index.md`), FAQ (`faq.md`), Envelope Protocol (`envelope-protocol.md`)
  - [x] 1.8 Add a `## Related` section at the end linking to sibling pages — matches footer pattern in `algorithms.md`, `envelope-protocol.md`, and `faq.md`

- [x] Task 2: Add Getting Started to MkDocs site navigation and landing page (AC: #2)
  - [x] 2.1 Replace the placeholder comment `# Story 2.6 adds: - Getting Started: getting-started.md` in `mkdocs.yml` (line 144) with the actual nav entry: `  - Getting Started: getting-started.md` (2-space indent, matching sibling entries)
  - [x] 2.2 Place Getting Started in nav as the first content item after Home (before API Reference) — this is the natural entry point for new users
  - [x] 2.3 Add a Getting Started grid card to `docs/index.md` Quick Links section as the **first** card (before API Reference). Use `:material-rocket-launch:` icon and a one-line description like "Install, integrate, and verify encryption in under 5 minutes." This is the highest-traffic entry point — a prominent CTA here drives adoption

- [x] Task 3: Fix `BACKEND_REGISTRY` global mutation in integration test (test review P1)
  - [x] 3.1 In `tests/integration/test_adk_integration.py`, replace the `try/finally` cleanup of `BACKEND_REGISTRY` in `test_works_with_custom_backend` (~line 322) with `monkeypatch.setitem(BACKEND_REGISTRY, ...)` — pytest auto-reverts on teardown, eliminating the risk of dirty global state on crash/interrupt. Add `monkeypatch` to the test's parameter list and remove the `try/finally` block.

- [x] Task 4: Run quality gates (AC: #1, #2)
  - [x] 4.1 `uv run mkdocs build --strict` — zero warnings, zero errors, Getting Started page renders correctly
  - [x] 4.2 `pre-commit run --all-files` — all hooks pass
  - [x] 4.3 `uv run ruff check .` — zero lint violations
  - [x] 4.4 `uv run pytest` — all tests pass (no regressions, docs + test fix)
  - [x] 4.5 Verify all cross-reference links in the Getting Started page resolve in strict build

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `uv run mkdocs build --strict` renders `docs/getting-started.md`; page contains install command, full async example with realistic state, verification step, What's Next links, and Related footer | pass |
| 2    | `uv run mkdocs build --strict` zero errors; Getting Started in nav; all cross-reference links resolve; `pre-commit run --all-files` passes all hooks | pass |

## Dev Notes

### What This Story Does

Creates a new `docs/getting-started.md` page and adds it to the MkDocs site navigation. The guide takes a developer from `pip install` to verified encrypted sessions in under 5 minutes (NFR28). This is more detailed than the README's 5-line swap — it includes a full runnable example, verification steps, and next-step links.

### What Already Exists (Do NOT Recreate)

| Component | Status | File |
|-----------|--------|------|
| MkDocs site with strict builds | Complete | `mkdocs.yml`, `.github/workflows/docs.yml` |
| README quick-start swap example | Complete | `README.md` (lines 29-43) |
| `docs/index.md` with Basic Usage example | Complete | `docs/index.md` |
| FAQ page (cross-ref target) | Complete | `docs/faq.md` |
| Algorithm Documentation (cross-ref target) | Complete | `docs/algorithms.md` |
| Envelope Protocol (cross-ref target) | Complete | `docs/envelope-protocol.md` |
| ADR index (cross-ref target) | Complete | `docs/adr/index.md` |
| API Reference (cross-ref target) | Complete | `docs/reference/index.md` |
| Nav placeholder for Getting Started | Ready | `mkdocs.yml` line 144 (`# Story 2.6 adds: - Getting Started: getting-started.md`) |

### Differentiation from Existing Content

The Getting Started guide must add value beyond what exists:

| Existing Page | What It Provides | What Getting Started Adds |
|---------------|-----------------|--------------------------|
| README | 5-line swap snippet | Full runnable script with `asyncio.run()` |
| `docs/index.md` (Basic Usage) | Async context manager pattern | Verification step (inspect SQLite), realistic state, next-step links |
| FAQ | Q&A format | Linear tutorial flow: install → code → verify → explore |

Do NOT duplicate the README swap example verbatim — reference it briefly, then provide the full example. Do NOT repeat the `docs/index.md` Basic Usage code — go deeper with verification and realistic state.

### Full Example Requirements

The example MUST:
- Use `asyncio.run()` as entry point (copy-paste runnable)
- Import from `adk_secure_sessions` (NOT from submodules)
- Use `FernetBackend` with a realistic key (use `cryptography.fernet.Fernet.generate_key()` to show proper key generation)
- Create a session with **realistic state** — e.g., `{"user_preferences": {"theme": "dark", "language": "en"}, "cart_items": [{"id": "prod-1", "name": "Widget", "qty": 2}], "last_active": "2026-03-04T10:30:00Z"}`
- Call `create_session`, `get_session`, and `close`
- Show that retrieved state matches original state
- Use `db_path` with a temp file or `"getting_started.db"` for easy cleanup

The example MUST NOT:
- Use `@pytest.mark.asyncio` — this is user code, not test code
- Import from `google.adk.sessions` for the basic example — keep it self-contained with just `adk_secure_sessions`
- Use environment variables for the key (keep the example simple; mention env vars as a production best practice after the example)

### Constructor Pattern

From architecture analysis, the `EncryptedSessionService` constructor takes:
- `backend`: A configured `EncryptionBackend` instance (e.g., `FernetBackend("your-key")`)
- `backend_id`: The backend identifier constant (e.g., `BACKEND_FERNET`)
- `db_path`: SQLite database path (default: `"sessions.db"`)

```python
from adk_secure_sessions import EncryptedSessionService, FernetBackend, BACKEND_FERNET

service = EncryptedSessionService(
    db_path="sessions.db",
    backend=FernetBackend("your-secret-key"),
    backend_id=BACKEND_FERNET,
)
```

**IMPORTANT**: Check the actual constructor signature in `src/adk_secure_sessions/services/encrypted_session.py` before writing the example. The architecture doc describes the pattern, but the actual implementation is the source of truth.

### Verification Section

Show users how to confirm encryption works by inspecting the SQLite file:

```bash
sqlite3 getting_started.db "SELECT hex(substr(state, 1, 20)) FROM sessions LIMIT 1;"
```

This shows encrypted bytes (hex), not readable JSON. Explain that:
- The first byte is the envelope version (`01`)
- The second byte is the backend ID (`01` for Fernet)
- The rest is encrypted ciphertext
- Session metadata (session_id, app_name, user_id) remains queryable in plaintext

### Cross-Reference Link Format

Use **relative paths from `docs/` root** (established pattern):
- `[API Reference](reference/index.md)`
- `[Architecture Decisions](adr/index.md)`
- `[FAQ](faq.md)`
- `[Envelope Protocol](envelope-protocol.md)`
- `[Algorithm Documentation](algorithms.md)`
- `[Roadmap](ROADMAP.md)`

### Page Structure

```
# Getting Started
## Prerequisites
## Installation
## Quick Start (brief swap pattern, link to full example below)
## Full Working Example (complete runnable async script)
## Verify Encryption (inspect SQLite to confirm)
## What's Next? (links to API Ref, ADRs, FAQ, Envelope Protocol)
## Related (footer links matching sibling pages)
```

### Anti-Patterns to Avoid

- **DO NOT** create any source code files — this is a documentation-only story
- **DO NOT** modify any existing `.md` files other than `mkdocs.yml` — Getting Started is a new page
- **DO NOT** duplicate README swap example verbatim — reference it, then go deeper
- **DO NOT** duplicate `docs/index.md` Basic Usage — differentiate with verification and realistic state
- **DO NOT** show synchronous code patterns — all examples use `async/await`
- **DO NOT** hardcode encryption keys in production advice — show `Fernet.generate_key()` for the example, then advise env vars for production
- **DO NOT** add entries to `__all__` or modify `__init__.py` — no API changes in this story
- **DO NOT** use `>>>` doctest style — use fenced triple-backtick blocks

### CI Constraint: Draft PRs Skip Docs Build

The `docs.yml` workflow only runs on non-draft PRs. Since project convention is always draft PRs, verify locally with `uv run mkdocs build --strict` during development.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/getting-started.md` | New — Getting Started tutorial with install, full example, verification, and next steps |
| `mkdocs.yml` | Modified — replace comment placeholder with nav entry |
| `docs/index.md` | Modified — add Getting Started grid card to Quick Links (first position) |

### Peripheral Config Impact

| File | Change | Reason |
|------|--------|--------|
| `docs/getting-started.md` | New file | Core deliverable |
| `mkdocs.yml` | Modified (line 144) | Replace comment placeholder with nav entry |
| `docs/index.md` | Modified | Add Getting Started grid card to Quick Links |
| `.github/workflows/docs.yml` | No changes | Already strict from Story 2.2 |
| `pyproject.toml` | No changes | No new deps |
| `.pre-commit-config.yaml` | No changes | docvet already configured |
| Source code (`src/`) | No changes | Documentation-only story |
| Tests (`tests/`) | Modified | `test_adk_integration.py`: replace `try/finally` BACKEND_REGISTRY cleanup with `monkeypatch.setitem()` (test review P1) |

### Project Structure Notes

- `docs/getting-started.md` goes in `docs/` root alongside `faq.md`, `algorithms.md`, `envelope-protocol.md` — consistent with existing flat structure for standalone pages
- No new directories created
- Nav position: first content item after Home, before API Reference (natural onboarding flow)

### Previous Story Intelligence (2.5)

From Story 2.5 (FAQ Page):
- MkDocs strict builds enforce valid markdown links and nav entries — broken links fail the build
- `git-revision-date-localized-plugin` warnings for newly created files are expected and don't fail strict mode
- docvet only checks `.py` files — real markdown validation is `mkdocs build --strict`
- Use relative paths from `docs/` root for cross-references
- Draft PRs skip docs build — verify locally
- End pages with `## Related` footer linking to sibling docs (established pattern)
- Use `##` (H2) headings for main sections — matches heading pattern across docs site
- Code review focus for docs-only stories: content accuracy, link validity, NOT code patterns

### Git Intelligence

Recent commits on `main`:
- `92ab2a2` — `chore(docs): add Ruff badge and fix CI badge label (#98)`
- `cf932e8` — `fix(ci): replace TestPyPI gate with local wheel smoke test (#97)`
- `f3e7ade` — `docs(faq): add FAQ page with 6 required entries and nav integration (#96)` — Story 2.5
- `1357afd` — `docs(roadmap): update completion status, add backend upgrade schedule (#94)` — Story 2.4
- Codebase is stable post-Story 2.5. No active development branches.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6 — Getting Started Guide]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2 — Documentation & Compliance Credibility]
- [Source: _bmad-output/planning-artifacts/architecture.md — Configuration Patterns, Data Flow, Contributor Setup Tiers]
- [Source: README.md — Quick-start swap example (lines 29-43)]
- [Source: docs/index.md — Basic Usage section]
- [Source: docs/faq.md — FAQ structure pattern, Related footer]
- [Source: mkdocs.yml — Nav structure (line 144, Getting Started placeholder)]
- [Source: _bmad-output/implementation-artifacts/2-5-faq-page.md — Previous story learnings]
- [Source: src/adk_secure_sessions/__init__.py — 14 public API exports]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage
- [x] `pre-commit run --all-files` -- all hooks pass
- [x] `uv run mkdocs build --strict` -- zero errors, Getting Started page renders correctly

## Code Review

- **Reviewer:** Code Review Workflow (adversarial) + Party Mode consensus (Paige, Amelia, Murat)
- **Outcome:** Approved with 1 fix applied

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| M1 | MEDIUM | Verification step requires `sqlite3` CLI not listed in Prerequisites | Fixed — added Python-first verification snippet as primary method, sqlite3 CLI as alternative |
| L1 | LOW | Quick Start swap lacks `async with` cleanup reminder | Dropped — deliberate pedagogical progression, mirrors README |
| L2 | LOW | Demo script missing `if __name__ == "__main__":` guard | Dropped — tutorial convention for standalone scripts, not a library module |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-04 | Story created by create-story workflow. Primary: create `docs/getting-started.md` with install, full async example, verification step, What's Next links. Add to MkDocs nav + index.md grid card. Bonus: fix test review P1 — `BACKEND_REGISTRY` monkeypatch in `test_adk_integration.py`. |
| 2026-03-04 | Implementation complete. Created Getting Started guide with Prerequisites, Installation, Quick Start swap pattern, Full Working Example (asyncio.run, FernetBackend, realistic state), Verify Encryption (sqlite3 hex inspection + envelope table), What's Next links, and Related footer. Added nav entry in mkdocs.yml and grid card in docs/index.md. Fixed BACKEND_REGISTRY try/finally to monkeypatch.setitem in test_adk_integration.py. All quality gates pass. |
| 2026-03-04 | Code review complete. 1 MEDIUM finding (sqlite3 CLI prerequisite gap) fixed — added Python-first verification snippet. 2 LOW findings dropped by party mode consensus (L1: pedagogical progression by design; L2: tutorial convention). All quality gates re-verified. Status → done. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — clean implementation with no blocking issues.

### Completion Notes List

- Created `docs/getting-started.md` with all required sections: Prerequisites, Installation, Quick Start (swap pattern bridge), Full Working Example (asyncio.run, Fernet.generate_key(), realistic shopping cart state), Verify Encryption (sqlite3 hex + envelope byte table), What's Next (4 links), Related footer (4 links)
- Full example differentiates from README (full runnable script vs 5-line swap) and docs/index.md (verification step + realistic state vs basic usage)
- Replaced mkdocs.yml placeholder comment with actual nav entry, positioned after Home before API Reference
- Added Getting Started grid card as first card in docs/index.md Quick Links with :material-rocket-launch: icon
- Fixed test_works_with_custom_backend: replaced try/finally BACKEND_REGISTRY cleanup with monkeypatch.setitem for crash-safe teardown
- All quality gates pass: mkdocs build --strict, pre-commit run --all-files (ruff, ty, pytest, docvet, yamllint)

### File List

- `docs/getting-started.md` (new) — Getting Started tutorial page
- `mkdocs.yml` (modified) — replaced nav placeholder with Getting Started entry
- `docs/index.md` (modified) — added Getting Started grid card to Quick Links
- `tests/integration/test_adk_integration.py` (modified) — monkeypatch.setitem replacing try/finally for BACKEND_REGISTRY
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — status updated
- `_bmad-output/implementation-artifacts/2-6-getting-started-guide.md` (modified) — story tracking
