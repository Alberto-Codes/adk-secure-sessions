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
   **When** a Getting Started guide page is created in the docs site
   **Then** it includes:
     1. Install command (`pip install adk-secure-sessions`)
     2. Full working agent example with encrypted sessions (complete runnable code, not just the swap)
     3. Verification step: how to confirm sessions are encrypted (e.g., inspect SQLite file)
     4. "What's next?" links to API Reference, Architecture Decisions, and FAQ
   **And** the guide supports NFR28: a developer can go from install to encrypted sessions in under 5 minutes
   **And** the example uses realistic session state (not empty dict or trivial placeholder)

2. **Given** the Getting Started page exists at `docs/getting-started.md`
   **When** the MkDocs site is built with `uv run mkdocs build --strict`
   **Then** the Getting Started page is accessible from the docs site navigation between Home and API Reference
   **And** the build completes with zero errors and zero warnings
   **And** all cross-reference links in the guide resolve correctly
   **Note:** docvet pre-commit hook only checks `.py` files — `mkdocs build --strict` is the real validation gate for `.md` files

## Tasks / Subtasks

- [x] Task 1: Create `docs/getting-started.md` with all required sections (AC: #1)
  - [x] 1.1 Create `docs/getting-started.md` with page title `# Getting Started`. Use `##` (H2) headings for each section — matches the heading pattern in `algorithms.md`, `envelope-protocol.md`, and `faq.md`.
  - [x] 1.2 Write `## Installation` section with both `pip install adk-secure-sessions` and `uv add adk-secure-sessions` commands. Note the 3 direct runtime dependencies (google-adk, cryptography, aiosqlite). Include verification commands: `python -c "import adk_secure_sessions; print('OK')"` for install check and `python -c "from importlib.metadata import version; print(version('adk-secure-sessions'))"` for version check. **NOTE**: The package does NOT export `__version__` — do NOT use `adk_secure_sessions.__version__` (it will raise `AttributeError`).
  - [x] 1.3 Write `## Quick Start` section with the minimal 3-import swap from README (show before/after ADK default vs encrypted). This bridges from the README — users who arrived from GitHub already saw this, docs site users may not have.
  - [x] 1.4 Write `## Full Working Example` section with a complete runnable async Python script that:
    - Creates a `FernetBackend` with a passphrase
    - Uses `EncryptedSessionService` as an async context manager
    - Creates a session with realistic state (e.g., `{"patient_name": "Jane Doe", "diagnosis_code": "J06.9", "api_key": "sk-secret-key-12345"}`)
    - Retrieves the session and prints decrypted state
    - Lists sessions for the app/user
    - Optionally deletes the session
    - Uses `asyncio.run()` as the entry point so the script is copy-paste runnable
    - **CRITICAL**: All API calls use keyword-only arguments (e.g., `app_name="my-agent"`, `user_id="user-123"`, `session_id=session.id`) — this matches the `EncryptedSessionService` signature where `create_session`, `get_session`, `list_sessions`, `delete_session` all use `*` to enforce keyword-only args
  - [x] 1.4a Add a `!!! warning` admonition box after the `FernetBackend` instantiation line in the Full Working Example: "In production, load your passphrase from an environment variable or secret manager (`os.environ["ENCRYPTION_KEY"]`). Never hardcode secrets in source code." This follows the admonition pattern already used in `docs/algorithms.md` (line 40: `!!! note`).
  - [x] 1.4b Verify the full example script executes successfully in a clean temp directory (`python script.py`). The Getting Started example is the first code every new user runs — a broken example invalidates the entire NFR28 promise.
  - [x] 1.5 Write `## Verify Encryption` section showing how to inspect the SQLite file directly to confirm data is encrypted using BOTH approaches:
    - Show the `sqlite3` CLI approach: `sqlite3 sessions.db "SELECT hex(state) FROM sessions LIMIT 1;"` (shortest path for developers with CLI available)
    - Show the Python `sqlite3` stdlib approach: `import sqlite3; conn = sqlite3.connect("sessions.db"); ...` (universally available, no CLI dependency)
    - Show that `state` column contains binary/encrypted data (not readable JSON)
    - Contrast with what unencrypted ADK `DatabaseSessionService` would store (plaintext JSON)
    - This is the "confidence" step from the AC — the user can SEE encryption working
  - [x] 1.6 Write `## Error Handling` section briefly covering:
    - `ConfigurationError` — raised if backend doesn't conform to protocol (caught at init)
    - `DecryptionError` — raised if wrong key is used (never silent corruption)
    - Show a try/except pattern for graceful error handling
  - [x] 1.7 Write `## What's Next?` section with links to:
    - [API Reference](reference/index.md) — full module documentation
    - [Architecture Decisions](adr/index.md) — design rationale
    - [FAQ](faq.md) — common questions answered
    - [Envelope Protocol](envelope-protocol.md) — how encryption envelopes work
    - [Algorithm Documentation](algorithms.md) — cryptographic details
  - [x] 1.8 Add a `## Related` section at the end with links to sibling docs — matches the footer pattern in `algorithms.md`, `envelope-protocol.md`, and `faq.md`

- [x] Task 2: Add Getting Started to MkDocs site navigation (AC: #2)
  - [x] 2.1 Replace the placeholder comment `# Story 2.6 adds: - Getting Started: getting-started.md` in `mkdocs.yml` (line 144) with the actual nav entry: `  - Getting Started: getting-started.md` (2-space indent, matching sibling entries)
  - [x] 2.2 Place Getting Started in nav between "Home" and "API Reference" (natural onboarding flow: Home → Getting Started → API Reference)

- [x] Task 3: Run quality gates (AC: #1, #2)
  - [x] 3.1 `uv run mkdocs build --strict` — zero warnings, zero errors, Getting Started page renders correctly
  - [x] 3.2 `pre-commit run --all-files` — all hooks pass
  - [x] 3.3 `uv run ruff check .` — zero lint violations
  - [x] 3.4 `uv run pytest` — all tests pass (no regressions, documentation-only story)
  - [x] 3.5 Verify all cross-reference links in Getting Started page resolve correctly in strict build

- [x] Task 4: Living Documentation Smoke Test (scope add — cross-cutting test maturity)
  - [x] 4.1 Add sentinel comment `<!-- test:exec:getting-started-full-example -->` before the Full Working Example code block in `docs/getting-started.md`
  - [x] 4.2 Create `tests/integration/test_docs_examples.py` with `test_full_example_runs_successfully` — extracts code via sentinel regex, execs in isolated `tmp_path`, validates example completes without error
  - [x] 4.3 Verify test passes and full suite remains green (176 passed, 9/9 hooks pass)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `uv run mkdocs build --strict` renders `docs/getting-started.md`; page contains install commands, full working example with realistic state, verification section, and What's Next links; `test_docs_examples.py::test_full_example_runs_successfully` validates example executes end-to-end | pass |
| 2    | `uv run mkdocs build --strict` zero errors; Getting Started in nav between Home and API Reference; all cross-reference links resolve; `pre-commit run --all-files` passes 9/9 hooks; `uv run pytest` 176 passed | pass |

## Dev Notes

### What This Story Does

Creates a new `docs/getting-started.md` page and adds it to the MkDocs site navigation. The guide takes developers from `pip install` to a working encrypted session in under 5 minutes (NFR28), with a verification step to confirm encryption is actually working.

### Audience and Tone

The Getting Started guide serves developers who already have an ADK agent and want to add encryption. Tone should be:
- **Confident and direct** — this is a technical tutorial, not marketing
- **Action-oriented** — each section leads to a concrete result
- **Copy-paste friendly** — code examples should be complete and runnable

### Content Architecture: How This Relates to Existing Docs

| Existing Content | Location | Relationship |
|-----------------|----------|-------------|
| 5-line quick-start swap | `README.md` Quick Start | Getting Started EXPANDS this with full context |
| Basic Usage snippet | `docs/index.md` | Getting Started provides DEEPER walkthrough with verification |
| FAQ answers | `docs/faq.md` | Getting Started links TO FAQ for common questions |
| API Reference | `docs/reference/` | Getting Started links TO API Reference for full details |
| Algorithm Documentation | `docs/algorithms.md` | Getting Started links TO this for crypto details |

**Key distinction**: README is for GitHub visitors (quick scan). `docs/index.md` is the docs homepage (feature overview). Getting Started is the **tutorial path** (step-by-step from zero to working encryption).

### What Already Exists (Do NOT Recreate)

| Component | Status | File |
|-----------|--------|------|
| MkDocs site with strict builds | Complete | `mkdocs.yml`, `.github/workflows/docs.yml` |
| FAQ page (cross-ref target) | Complete | `docs/faq.md` |
| Algorithm Documentation (cross-ref target) | Complete | `docs/algorithms.md` |
| Envelope Protocol page (cross-ref target) | Complete | `docs/envelope-protocol.md` |
| ADR index (cross-ref target) | Complete | `docs/adr/index.md` |
| API Reference (cross-ref target) | Complete | `docs/reference/` (auto-generated) |
| Nav placeholder for Getting Started | Ready | `mkdocs.yml` line 144 (`# Story 2.6 adds: - Getting Started: getting-started.md`) |
| README quick-start | Complete | `README.md` |
| docs/index.md Basic Usage | Complete | `docs/index.md` |

### EncryptedSessionService API — Exact Signatures

The Getting Started example code MUST use keyword-only arguments (enforced by `*` in all public methods):

```python
# Constructor
EncryptedSessionService(db_path: str, backend: EncryptionBackend, backend_id: int)

# create_session — keyword-only after *
await service.create_session(
    app_name="my-agent",
    user_id="user-123",
    state={"key": "value"},       # optional
    session_id="custom-id",       # optional
)

# get_session — keyword-only after *
await service.get_session(
    app_name="my-agent",
    user_id="user-123",
    session_id=session.id,
)

# list_sessions — keyword-only after *
await service.list_sessions(
    app_name="my-agent",
    user_id="user-123",
)

# delete_session — keyword-only after *
await service.delete_session(
    app_name="my-agent",
    user_id="user-123",
    session_id=session.id,
)
```

**CRITICAL**: Never use positional arguments in the example code. All `create_session`, `get_session`, `list_sessions`, and `delete_session` use `*` to enforce keyword-only arguments. Using positional args will raise `TypeError`.

**`list_sessions` return type**: Returns `ListSessionsResponse`, NOT a plain list. Access sessions via `response.sessions`:

```python
response = await service.list_sessions(app_name="my-agent", user_id="user-123")
for session in response.sessions:
    print(session.id)
```

Do NOT write `sessions = await service.list_sessions(...)` and iterate it directly — that will fail.

### Realistic Session State

The AC requires "realistic session state (not empty dict or trivial placeholder)". Use healthcare-adjacent data to reinforce the compliance value proposition:

```python
state = {
    "patient_name": "Jane Doe",
    "diagnosis_code": "J06.9",
    "api_key": "sk-secret-key-12345",
}
```

This demonstrates WHY encryption matters — the state contains PII and secrets that must be protected at rest.

### Key Management Admonition

The Full Working Example section MUST include a `!!! warning` admonition box immediately after the `FernetBackend("your-secret-passphrase")` line. This follows the admonition pattern already used in `docs/algorithms.md` (line 40). Content:

```markdown
!!! warning "Never hardcode secrets in production"

    In production, load your passphrase from an environment variable or secret
    manager (`os.environ["ENCRYPTION_KEY"]`). Never hardcode secrets in source
    code.
```

This is duty-of-care for a security library's Getting Started guide — two sentences that prevent the most common mistake new users make.

### Verification Section — How to Confirm Encryption

The verification step should show the developer inspecting the raw SQLite database:

```bash
sqlite3 sessions.db "SELECT hex(state) FROM sessions LIMIT 1;"
```

This returns hex-encoded binary data (the encrypted envelope), NOT readable JSON. Contrast with unencrypted ADK storage where `SELECT state FROM sessions` returns plaintext JSON. This is the "seeing is believing" moment.

### Cross-Reference Link Format

Use **relative paths from `docs/` root** for all cross-references:
- `[API Reference](reference/index.md)` — NOT `docs/reference/index.md`
- `[FAQ](faq.md)` — same level as `getting-started.md`
- `[Architecture Decisions](adr/index.md)` — include the `adr/` subdirectory
- `[Envelope Protocol](envelope-protocol.md)` — same level
- `[Algorithm Documentation](algorithms.md)` — same level

### Markdown Structure

Use `##` (H2) headings for each section, matching the pattern in `algorithms.md`, `envelope-protocol.md`, and `faq.md`. End with a `## Related` section containing a bullet list of links to sibling docs.

### Anti-Patterns to Avoid

- **DO NOT** create any source code files — this is a documentation-only story
- **DO NOT** modify any existing `.md` files other than `mkdocs.yml` — Getting Started is a new page
- **DO NOT** add `@pytest.mark.asyncio` — project uses `asyncio_mode = "auto"`
- **DO NOT** show `Runner` or `LlmAgent` usage — "Full working example" per the AC means a complete, standalone `asyncio.run()` script demonstrating the `EncryptedSessionService` CRUD lifecycle (create, get, list, delete), not an LLM agent pipeline. Including `Runner`/`LlmAgent` would require a Gemini API key, violating NFR28's "under 5 minutes" guarantee since key provisioning alone exceeds that. The README swap and index.md already establish the "drop-in replacement" narrative.
- **DO NOT** include key generation or rotation — that's Phase 3/4 scope
- **DO NOT** write overly long explanations — each section should be concise and action-oriented
- **DO NOT** duplicate FAQ content — link to FAQ instead of re-answering the same questions
- **DO NOT** use `::` directive for code examples — use fenced triple-backtick blocks (griffe/mkdocstrings requirement)
- **DO NOT** show `from __future__ import annotations` in the Getting Started example — it's confusing for tutorial code and not needed in standalone scripts
- **DO NOT** use `ENVELOPE_VERSION_1` in the Getting Started example — it's an internal constant, not needed for basic usage

### Code Review Focus

This is a documentation-only story. Code review should focus on:
- **Content accuracy** — does the example code actually work? Are the API signatures correct?
- **NFR28 compliance** — can a developer actually complete the guide in under 5 minutes?
- **Cross-reference link validity** — do all relative links resolve in `mkdocs build --strict`?
- **Realistic state** — does the example use meaningful, compliance-relevant state data?
- **NOT** code patterns, test coverage, or source code style (no source code is modified)

### Docvet vs MkDocs Strict

docvet pre-commit hook only checks `.py` files (`types: [python]`), not `.md` files. For this documentation-only story, `uv run mkdocs build --strict` is the real validation gate — it catches broken links, invalid nav entries, and malformed markdown.

### CI Constraint: Draft PRs Skip Docs Build

The `docs.yml` workflow only runs on non-draft PRs. Since project convention is always draft PRs, verify locally with `uv run mkdocs build --strict` during development.

### Previous Story Intelligence (2.5)

From Story 2.5 (FAQ Page):
- MkDocs strict builds enforce valid markdown links and nav entries — broken links fail the build
- `git-revision-date-localized-plugin` warnings for newly created files are expected and don't fail strict mode
- docvet only checks `.py` files (types: [python]), not `.md` — real markdown validation is `mkdocs build --strict`
- Use relative paths from `docs/` root for cross-references (e.g., `[FAQ](faq.md)`)
- Code review findings from 2.5: always verify quality gates actually pass before marking them `[x]`
- 175 tests pass, 9/9 pre-commit hooks pass, zero lint violations (as of Story 2.5 completion)

### Git Intelligence

Recent commits on `main`:
- `60c310b` — `chore(docvet): enforce presence check with 100% threshold (#99)` — docvet strictness
- `92ab2a2` — `chore(docs): add Ruff badge and fix CI badge label (#98)` — badge updates
- `cf932e8` — `fix(ci): replace TestPyPI gate with local wheel smoke test (#97)` — CI fix
- `f3e7ade` — `docs(faq): add FAQ page with 6 required entries and nav integration (#96)` — Story 2.5 merge
- `1357afd` — `docs(roadmap): update completion status, add backend upgrade schedule (#94)` — Story 2.4 merge
- Codebase is stable post-Story 2.5. No active development branches.

### Peripheral Config Impact

| File | Change | Reason |
|------|--------|--------|
| `docs/getting-started.md` | New file | Core deliverable |
| `mkdocs.yml` | Modified (line 144) | Replace comment placeholder with nav entry |
| `.github/workflows/docs.yml` | No changes | Already strict from Story 2.2 |
| `pyproject.toml` | No changes | No new deps |
| `.pre-commit-config.yaml` | No changes | docvet already configured |
| Source code (`src/`) | No changes | Documentation-only story |
| Tests (`tests/`) | No changes | Documentation-only story |

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/getting-started.md` | New — Getting Started tutorial with install, full example, verification, and next steps |
| `mkdocs.yml` | Modified — replace comment placeholder with Getting Started nav entry |

### Project Structure Notes

- `docs/getting-started.md` goes in `docs/` root alongside `faq.md`, `algorithms.md`, `envelope-protocol.md` — consistent with existing flat structure for standalone pages
- No new directories created
- Nav position: between Home and API Reference (natural onboarding flow)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6 — Getting Started Guide]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2 — Documentation & Compliance Credibility]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR28: 5-minute onboarding from install to encrypted session]
- [Source: README.md — Quick Start swap pattern (Before/After)]
- [Source: docs/index.md — Basic Usage code snippet]
- [Source: docs/faq.md — FAQ structure and Related footer pattern]
- [Source: docs/algorithms.md — Heading and footer patterns]
- [Source: docs/envelope-protocol.md — Heading and footer patterns]
- [Source: src/adk_secure_sessions/__init__.py — 14 public exports]
- [Source: src/adk_secure_sessions/services/encrypted_session.py — EncryptedSessionService API signatures]
- [Source: tests/integration/test_adk_runner.py — Runner + LlmAgent integration pattern (reference only)]
- [Source: mkdocs.yml — Nav structure (line 144, Getting Started placeholder)]
- [Source: _bmad-output/implementation-artifacts/2-5-faq-page.md — Previous story learnings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage (175 passed)
- [x] `pre-commit run --all-files` -- all 9/9 hooks pass
- [x] `uv run mkdocs build --strict` -- zero errors, Getting Started page renders correctly

## Code Review

- **Reviewer:** Adversarial code review (Claude Opus 4.6) + Party mode consensus (3 agents: Paige, Amelia, Murat)
- **Outcome:** Approved with 2 fixes applied

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| M1 | MEDIUM | `sessions.db` not in `.gitignore` — Getting Started example creates SQLite artifact in CWD | Fixed: added `sessions.db` to `.gitignore` |
| M2 | MEDIUM | Dead `TYPE_CHECKING` block in `test_docs_examples.py` (lines 15-20) — empty conditional imports nothing | Fixed: removed dead `TYPE_CHECKING` import and empty block |
| L1 | LOW | Error Handling section oversimplifies `ConfigurationError` triggers | Dropped: intentional tutorial simplification; API Reference covers full detail |
| L2 | LOW | Living documentation test lacks output assertions | Dropped: test correctly scoped as drift detector; unit tests cover business logic |

### Verification

- [x] All HIGH findings resolved (none found)
- [x] All MEDIUM findings resolved or accepted (M1, M2 fixed)
- [x] Tests pass after review fixes (176 passed, 1 deselected)
- [x] Quality gates re-verified (ruff check clean, mkdocs build --strict clean)

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-03 | Story created by create-story workflow. Documentation-only story: create `docs/getting-started.md` with install, full working example, verification step, and What's Next links; add to MkDocs nav. No source code changes. |
| 2026-03-03 | Party mode consensus (5 agents: Paige, Bob, Amelia, Winston, Murat): 6 findings applied — (1) fixed `__version__` verification to use `importlib.metadata` (no `__version__` attribute exported), (2) added `!!! warning` admonition subtask for key management in Full Working Example, (3) added subtask to verify example script runs end-to-end, (4) updated Task 1.5 to show both CLI and Python sqlite3 verification approaches, (5) clarified "full working example" anti-pattern with NFR28/Gemini API key rationale, (6) added `ListSessionsResponse` return type pattern to dev notes. Item rejected: marking Task 1.6 (Error Handling) as enhancement — team consensus is error handling is table stakes for a getting started guide. |
| 2026-03-03 | Implementation complete. Created `docs/getting-started.md` with 8 sections (Installation, Quick Start, Full Working Example, Verify Encryption, Error Handling, What's Next, Related). Replaced nav placeholder in `mkdocs.yml`. Full example script verified end-to-end. All quality gates pass: `mkdocs build --strict` zero errors, 9/9 pre-commit hooks pass, 175 tests pass, zero lint violations. |
| 2026-03-03 | Scope add (approved): Living Documentation Smoke Test. Party mode consensus (7 agents: Murat, Amelia, Quinn, Paige, Winston, Bob, John) — added `tests/integration/test_docs_examples.py` with sentinel-based extraction (`<!-- test:exec:getting-started-full-example -->`), `exec()` in isolated `tmp_path`, validates Full Working Example runs without error. Catches API drift before users do. 176 tests pass. |
| 2026-03-03 | Code review complete. Adversarial review + party mode consensus (Paige, Amelia, Murat): 4 findings — 2 accepted and fixed (M1: added `sessions.db` to `.gitignore`; M2: removed dead `TYPE_CHECKING` block from `test_docs_examples.py`), 2 dropped (L1: intentional tutorial simplification; L2: test correctly scoped as drift detector). All ACs verified, all tasks confirmed done, all factual claims validated against source code. 176 tests pass, ruff clean, mkdocs strict clean. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — clean implementation with no debugging required.

### Completion Notes List

- Created `docs/getting-started.md` with 8 H2 sections following established pattern from `algorithms.md`, `faq.md`, and `envelope-protocol.md`
- Installation section includes both pip and uv commands, 3 runtime deps note, and `importlib.metadata` version check (avoids `__version__` AttributeError)
- Quick Start section shows before/after ADK swap pattern from README
- Full Working Example: complete `asyncio.run()` script with realistic healthcare state (`patient_name`, `diagnosis_code`, `api_key`), keyword-only args, `ListSessionsResponse.sessions` access pattern, and `async with` context manager
- Warning admonition for production key management placed after code block
- Verify Encryption section shows both `sqlite3` CLI and Python stdlib approaches with contrast to unencrypted ADK storage
- Error Handling section covers `ConfigurationError` and `DecryptionError` with try/except pattern
- What's Next and Related sections with relative links to API Reference, ADR index, FAQ, Envelope Protocol, and Algorithm Documentation
- Replaced `mkdocs.yml` nav placeholder comment with actual `Getting Started: getting-started.md` entry between Home and API Reference
- Full example script verified end-to-end: creates session with realistic state, retrieves with decrypted state, lists sessions via `response.sessions`, deletes session
- All cross-reference links resolve in `mkdocs build --strict`
- **Scope add (approved)**: Created `tests/integration/test_docs_examples.py` — living documentation smoke test that extracts the Full Working Example via `<!-- test:exec:getting-started-full-example -->` sentinel, executes it in isolated `tmp_path` via `exec()`, and validates it completes without error. Catches API drift before users encounter broken examples. Pattern scales to future doc pages via the `test:exec:<name>` sentinel convention.

### File List

- `docs/getting-started.md` — New: Getting Started tutorial page (+ sentinel comment for test extraction)
- `mkdocs.yml` — Modified: replaced line 144 comment placeholder with nav entry
- `tests/integration/test_docs_examples.py` — New: Living documentation smoke test (sentinel-based example extraction + exec); review fix: removed dead `TYPE_CHECKING` block
- `.gitignore` — Modified: added `sessions.db` to prevent accidental commits of Getting Started example artifact
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Modified: story status `ready-for-dev` → `review`
- `_bmad-output/implementation-artifacts/2-6-getting-started-guide.md` — Modified: task checkboxes, AC-to-Test Mapping, Quality Gates, Dev Agent Record, Change Log, Status, Code Review
