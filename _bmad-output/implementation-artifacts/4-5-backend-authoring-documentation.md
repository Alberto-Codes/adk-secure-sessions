# Story 4.5: Backend Authoring Documentation

Status: review
Branch: feat/docs-4-5-backend-authoring-guide
GitHub Issue:

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer creating a custom encryption backend**,
I want **comprehensive documentation with examples and a starter template for authoring backends**,
So that **I can implement a conformant backend without reading the library's source code**.

## Acceptance Criteria

1. **Given** the `EncryptionBackend` protocol defines the backend contract
   **When** a Backend Authoring Guide page is created in the docs site
   **Then** it includes (FR50):
     1. The protocol contract with each method explained (`encrypt`, `decrypt`, `sync_encrypt`, `sync_decrypt`, `backend_id`)
     2. A complete working example of a custom backend implementation
     3. Testing guidance: how to verify protocol conformance, round-trip correctness, and envelope compatibility
     4. Registration instructions: how to register a custom backend with the service
     5. A starter template (copy-paste ready) that a backend author can use as a starting point

2. **Given** the envelope format uses `backend_id` to dispatch decryption
   **When** the guide explains backend ID assignment
   **Then** it documents: how to choose a unique backend ID, the reserved range (`0x01`-`0x0F` for official backends), and the community range (`0x10`-`0xFF`)

3. **Given** encryption backends must satisfy both sync and async contracts
   **When** the guide covers common pitfalls
   **Then** it includes anti-patterns: nonce reuse, blocking the event loop with CPU-bound crypto, exposing key material in error messages, forgetting to implement sync methods for the TypeDecorator path

4. **Given** the docs site enforces quality via pre-commit hooks
   **When** the new documentation page is added
   **Then** `pre-commit run --all-files` passes (including docvet)

## Tasks / Subtasks

- [x] Task 1: Create `docs/how-to/backend-authoring.md` (AC: #1, #2, #3)
  - [x] 1.1 Write "When to Write a Custom Backend" opening section (3-4 bullet scenarios: KMS integrations, HSMs, custom algorithms, compliance-mandated ciphers)
  - [x] 1.2 Write "The Protocol Contract" section: table of all 5 members (`backend_id` property, `sync_encrypt`, `sync_decrypt`, `encrypt`, `decrypt`) with parameter types, return types, and purpose of each — explain why both sync and async exist (TypeDecorator path)
  - [x] 1.3 Write "Backend ID Assignment" section: reserved range `0x01`-`0x0F` (official), community range `0x10`-`0xFF`; decision table for choosing an ID; explain how IDs are used in the envelope header for dispatch
  - [x] 1.4 Write "Walkthrough: AesGcmBackend" section: annotated excerpts from `src/adk_secure_sessions/backends/aes_gcm.py` showing all 5 protocol members, `asyncio.to_thread()` delegation, nonce generation, and `DecryptionError` wrapping — use excerpts with `[Source: ...]` cross-links, do NOT copy-paste full source
  - [x] 1.5 Write "Starter Template" section: a `SkeletonBackend` class with all 5 protocol members, `asyncio.to_thread()` delegation in async methods, placeholder comments for encrypt/decrypt logic, `backend_id = 0x10` (community range start) — copy-paste ready
  - [x] 1.6 Write "Registering Your Backend" section with two-tier framing: (a) current approach — add to `BACKEND_REGISTRY` in `serialization.py`, pass to `EncryptedSessionService(backend=...)` or `additional_backends`; (b) future — entry-point discovery planned in Story 5.1. Include mkdocs admonition `!!! note "Registration will change"` callout
  - [x] 1.7 Write "Testing Checklist" section as a numbered table with 7 items and source references: (1) `isinstance` conformance, (2) round-trip correctness, (3) empty bytes edge case, (4) wrong-key raises `DecryptionError`, (5) ciphertext uniqueness / nonce uniqueness (note: only for nonce-based backends), (6) cross-backend confusion rejection, (7) error messages don't contain key material. Point to `test_aes_gcm_backend.py` as canonical reference, do NOT include a full test file template
  - [x] 1.8 Write "Common Pitfalls" section: 6 anti-patterns — nonce reuse (catastrophic for AEAD), blocking event loop (must use `asyncio.to_thread()`), key material in exceptions (NFR6), forgetting sync methods (TypeDecorator path), mutable state in backends, adding envelope framing (serialization layer handles this)
  - [x] 1.9 Write "Security Notes" section (key material safety, nonce requirements, `DecryptionError` wrapping)
  - [x] 1.10 Write "Related" section with cross-links: ADR-001 (Protocol-Based Interfaces), ADR-002 (Async-First Design), envelope-protocol page, AesGcmBackend API reference, key-rotation how-to, Roadmap (entry-point discovery)
  - [x] 1.11 Follow Diataxis How-To pattern throughout (goal → steps → result) and match `docs/how-to/key-rotation.md` style: decision tables, ✅/⚠️ trade-off markers, fenced code blocks with imports, cross-links

- [x] Task 2: Update `mkdocs.yml` navigation (AC: #4)
  - [x] 2.1 Add `Backend Authoring: how-to/backend-authoring.md` entry under `How-To Guides:` section (after `Key Rotation` entry)

- [x] Task 3: Validate documentation quality (AC: #4)
  - [x] 3.1 Run `pre-commit run --all-files` — verify docvet, yamllint, and all hooks pass
  - [x] 3.2 Run `uv run mkdocs build --strict` — verify docs site builds with zero warnings
  - [x] 3.3 Visually verify code examples render correctly with syntax highlighting

### Cross-Cutting Test Maturity (Standing Task)

<!-- Sourced from test-review.md recommendations. The create-story workflow
     picks the next unaddressed item and assigns it here. -->

**Test Review Item**: No pending items — identify one high-risk area lacking test coverage (outside story scope)
**Severity**: N/A
**Location**: Developer's choice

All test-review.md recommendations have been addressed. Pick a gap area not related to the story scope.

- [x] Identify one area outside story scope that lacks test coverage and add a test
- [x] Verify new/changed test(s) pass in CI
- [x] Mark item as done in `_bmad-output/test-artifacts/test-review.md`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `pre-commit run --all-files` (docvet) + `mkdocs build --strict` — all 10 sections present in guide | pass |
| 2    | Manual review: backend ID ranges `0x01-0x0F` (official) and `0x10-0xFF` (community) documented with decision table | pass |
| 3    | Manual review: 6 anti-patterns in Common Pitfalls section (nonce reuse, blocking event loop, key material in exceptions, forgetting sync methods, mutable state, envelope framing) | pass |
| 4    | `pre-commit run --all-files` exits 0 (yamllint, ruff, ty, pytest, docvet all pass) | pass |

## Dev Notes

### This Is a Documentation-Only Story

No source code changes in `src/`. No new test files (unless the cross-cutting task warrants one). The only code-adjacent change is the `mkdocs.yml` nav entry.

### The EncryptionBackend Protocol Contract (5 Members)

From `src/adk_secure_sessions/protocols.py`:

| Member | Type | Signature | Purpose |
|--------|------|-----------|---------|
| `backend_id` | `@property` | `-> int` | Unique byte for envelope header dispatch |
| `sync_encrypt` | method | `(self, plaintext: bytes) -> bytes` | Sync encryption for TypeDecorator path |
| `sync_decrypt` | method | `(self, ciphertext: bytes) -> bytes` | Sync decryption for TypeDecorator path |
| `encrypt` | `async def` | `(self, plaintext: bytes) -> bytes` | Async encryption for application code |
| `decrypt` | `async def` | `(self, ciphertext: bytes) -> bytes` | Async decryption for application code |

**Why both sync and async?** The TypeDecorator (`EncryptedJSON`) runs in SQLAlchemy's synchronous execution context via `process_bind_param`/`process_result_value`. These call `sync_encrypt`/`sync_decrypt` directly. The async methods exist for application-level usage and should delegate to the sync methods via `asyncio.to_thread()` to avoid blocking the event loop.

**Protocol is structural** (PEP 544): backends do NOT inherit from `EncryptionBackend`. Any class with matching method signatures conforms. `isinstance(MyBackend(), EncryptionBackend)` returns `True` at runtime (but only checks method existence, not signatures — use a static type checker for full validation).

### Backend ID Ranges

From the envelope protocol and epics specification:

- `0x01`-`0x0F`: Reserved for official backends (`0x01` = Fernet, `0x02` = AES-GCM)
- `0x10`-`0xFF`: Community/custom range

The `BACKEND_REGISTRY` in `serialization.py` maps IDs to names:
```python
BACKEND_REGISTRY: dict[int, str] = {
    BACKEND_FERNET: "Fernet",      # 0x01
    BACKEND_AES_GCM: "AES-GCM",   # 0x02
}
```

Custom backends must be added to `BACKEND_REGISTRY` to work with `encrypt_session`/`decrypt_session`. The guide must explain this registration step clearly — it's the most common "my custom backend doesn't work" mistake.

### Registration Path for Custom Backends (Party Mode Consensus)

**Decision: Two-tier framing — current manual process + future entry-point discovery with mkdocs admonition.**

There is currently **no dynamic registration API**. Backend authors must:
1. Choose a `backend_id` in the community range (`0x10`-`0xFF`)
2. Add their backend to `BACKEND_REGISTRY` in `serialization.py` (requires a source edit or a PR to the library)
3. Pass their backend to `EncryptedSessionService(backend=my_backend)` or use `additional_backends=[my_backend]`

The guide frames registration as two tiers:
- **Quick start (current):** "For development and testing, add your backend to `BACKEND_REGISTRY`" — clearly labeled as the current approach
- **Future (Story 5.1):** "Automatic registration via entry points is planned"

Include an mkdocs admonition callout:
```markdown
!!! note "Registration will change"
    The manual `BACKEND_REGISTRY` edit described here is the current process.
    A future release will introduce entry-point discovery (see [Roadmap](../ROADMAP.md)),
    allowing backends to register automatically via their package metadata.
```

This sets expectations without creating an implicit contract around the manual approach that would make Story 5.1's entry-point discovery feel like a breaking change.

### Guide Section Order (Party Mode Consensus)

Follow **Diataxis How-To pattern** (goal -> steps -> result) and match `key-rotation.md` style:

| # | Section | Purpose |
|---|---------|---------|
| 1 | **When to Write a Custom Backend** | 3-4 bullet scenarios (KMS, HSM, compliance ciphers) |
| 2 | **The Protocol Contract** | Table of 5 members with types and purpose |
| 3 | **Backend ID Assignment** | Reserved vs. community ranges, decision table |
| 4 | **Walkthrough: AesGcmBackend** | Annotated excerpts, not full source copy |
| 5 | **Starter Template** | `SkeletonBackend`, copy-paste ready |
| 6 | **Registering Your Backend** | Two-tier: current manual + future admonition |
| 7 | **Testing Checklist** | 7-item table with source references |
| 8 | **Common Pitfalls** | 6 anti-patterns from Dev Notes |
| 9 | **Security Notes** | Key material safety, nonce requirements |
| 10 | **Related** | ADR-001, ADR-002, envelope-protocol, API ref, key-rotation |

Style patterns from `key-rotation.md`:
- **Opening paragraph**: concise purpose statement
- **Decision table**: `| Scenario | ... | Path |` for choosing an approach
- **Code examples**: fenced ` ```python ` blocks with imports shown, comments inline
- **"How it works"**: explanation of mechanism after each code block
- **"Trade-offs"**: ✅ pros and ⚠️ cons markers
- **Security notes**: dedicated section near the end
- **Related**: cross-links to ADRs, API reference, other docs

### Target Audience (Party Mode Consensus)

**Primary audience**: Our own Epic 5 dev agents building KMS backends (AWS, GCP, Vault) — the guide should be **prescriptive and specific** with exact patterns to follow and exact test structures to copy.

**Secondary audience**: Community contributors adding custom backends — needs **explanatory context** about why decisions were made and how to navigate the codebase.

Lead with the prescriptive path (for Epic 5), include "Understanding the Design" context for community readers.

### Reference Implementations to Study

The guide should reference both official backends as examples:

1. **FernetBackend** (`src/adk_secure_sessions/backends/fernet.py`):
   - Backend ID `0x01`; passphrase-based with PBKDF2 + HKDF key derivation
   - More complex example: key derivation, backward compatibility, salt handling
   - Good example of: constructor validation, error wrapping with `DecryptionError`

2. **AesGcmBackend** (`src/adk_secure_sessions/backends/aes_gcm.py`):
   - Backend ID `0x02`; raw key, nonce-based AEAD
   - Simpler example: fixed-size key, random nonce per-operation
   - Good example of: `asyncio.to_thread()` delegation, proper nonce generation

### Pitfalls Section Must Cover

These are the known footguns from the codebase and review history:

1. **Nonce reuse** (AES-GCM catastrophic): if a backend uses a nonce-based cipher, reusing a nonce with the same key allows key recovery. Must generate fresh random nonce per-operation.
2. **Blocking the event loop**: all `cryptography` library calls are CPU-bound. Async methods MUST delegate via `asyncio.to_thread(self.sync_encrypt, plaintext)`.
3. **Key material in exceptions**: error messages must never contain passphrases, key bytes, or plaintext. Use `raise DecryptionError("decryption failed") from exc`.
4. **Forgetting sync methods**: if `sync_encrypt`/`sync_decrypt` are missing, the TypeDecorator path silently fails or errors at runtime. The `@runtime_checkable` check catches this at service init.
5. **Mutable state in backends**: backend instances may be shared across coroutines. Avoid mutable state unless protected by locks.
6. **Wrong ciphertext format**: the backend's `encrypt`/`decrypt` handle raw ciphertext only — the envelope (`version_byte + backend_id + ciphertext`) is managed by the serialization layer. Backends must NOT add their own envelope framing.

### Example Backend Strategy (Party Mode Consensus)

**Decision: Use annotated `AesGcmBackend` excerpts as the primary walkthrough, NOT a toy `XorBackend`.**

Rationale (from team debate):
- Backend authors are building production backends (KMS, Vault, HSMs) — showing XOR sends the wrong signal about security expectations and requires a "NOT FOR PRODUCTION" warning that clutters the guide
- `AesGcmBackend` (`src/adk_secure_sessions/backends/aes_gcm.py`) is the simpler of the two official backends (~90 lines, no key derivation, no backward compat) — ideal for annotation
- Use **annotated excerpts with `[Source: ...]` cross-links** to the API reference, not copy-pasted full source — avoids maintaining two copies since griffe auto-generates reference docs
- Pair with a **`SkeletonBackend` starter template** (all 5 members, placeholder comments, `asyncio.to_thread()` delegation, `backend_id = 0x10`) as the copy-paste artifact

The guide shows a real implementation AND gives a clean starting point — no fake crypto anywhere.

### Testing Checklist (Party Mode Consensus)

**Decision: Checklist format with source references, NOT a full test file template.**

The guide includes a 7-item testing checklist table. Point to `test_aes_gcm_backend.py` as the canonical reference implementation for test patterns.

| # | Test | Pattern Source | Notes |
|---|------|---------------|-------|
| 1 | `isinstance(MyBackend(...), EncryptionBackend)` is `True` | `test_protocols.py:27` | Protocol conformance |
| 2 | `encrypt(b"hello")` then `decrypt()` returns `b"hello"` | `test_fernet_backend.py:73` | Round-trip correctness |
| 3 | `encrypt(b"")` then `decrypt()` returns `b""` | `test_fernet_backend.py:82` | Empty bytes edge case |
| 4 | `decrypt(wrong_key_ciphertext)` raises `DecryptionError` | `test_aes_gcm_backend.py:95` | Wrong-key rejection |
| 5 | 100x `encrypt(same_plaintext)` produces 100 unique ciphertexts | `test_aes_gcm_backend.py:161` | Nonce-based backends only; KMS backends may be deterministic |
| 6 | Cross-backend: decrypt with wrong backend raises `DecryptionError` | `test_aes_gcm_backend.py:111` | Cross-backend confusion |
| 7 | Error messages don't contain key material | `test_adk_encryption.py` pattern | NFR6 safety |

**Note on test #5**: nonce uniqueness only applies to nonce-based backends (AES-GCM, ChaCha20). KMS backends with server-side encryption may produce deterministic ciphertext for the same plaintext+key — the guide should note this distinction.

### Web Research: Latest Technical Specifics

- **cryptography library**: Latest stable is 46.0.6 (March 2026). No breaking changes affecting Fernet or AES-GCM since 44.x. The guide should reference `cryptography>=44.0.0` as the project's pinned version. Notable: pyca/cryptography deprecated its own pluggable backend architecture (the `default_backend()` pattern) in favor of a unified OpenSSL backend — our project's "backend" concept is entirely different (encryption algorithm plugins, not crypto library backends). The guide should NOT reference pyca's deprecated backend pattern to avoid confusion.
- **PEP 544 Protocols**: `@runtime_checkable` checks method existence only, not signatures. This is a known limitation — the guide should mention using `mypy`/`pyright` for full static validation alongside `isinstance()` for runtime checks.
- **Diataxis framework**: The project's docs already follow Diataxis (How-To Guides, Reference, Architecture/Explanation). The new page is a How-To guide — the reader is *working* (building a backend), not *studying* (learning about encryption). Keep the tone task-oriented: "here's how to do X" not "here's how X works."

### Previous Story Intelligence (from Story 4.4)

Story 4.4 key patterns to carry forward:
- **Doc page style**: `key-rotation.md` established the how-to format — decision tables, trade-off markers, Related section
- **mkdocs.yml nav**: `How-To Guides:` section already exists; add the new entry after `Key Rotation`
- **ADR cross-linking**: link to ADR-001 (Protocol-Based Interfaces), ADR-002 (Async-First Design)
- **docvet validation**: run `pre-commit run --all-files` to catch any doc quality issues

From Story 4.4 dev agent record: `mkdocs.yml` was modified to add the How-To Guides nav section, ADR-009 entry, and fix missing ADR-008 entry. This nav structure is now in place.

### Blast Radius: Peripheral Config Files

- `mkdocs.yml`: Add `Backend Authoring` entry under `How-To Guides:` nav section
- **No changes to**: `pyproject.toml`, `.github/workflows/*.yml`, `sonar-project.properties`, `.pre-commit-config.yaml`, `release-please-config.json`, `src/adk_secure_sessions/__init__.py`
- This is a pure documentation addition — no code changes, no new dependencies, no CI changes

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `docs/how-to/backend-authoring.md` | New page: Backend Authoring Guide with protocol contract, examples, testing guidance, registration, pitfalls |
| `mkdocs.yml` | Add nav entry under `How-To Guides:` section |

### Project Structure Notes

New files to create:
- `docs/how-to/backend-authoring.md` — the Backend Authoring Guide

Modified files:
- `mkdocs.yml` — add nav entry

**Do NOT modify**:
- Any files in `src/` (no code changes in this story)
- Any existing test files (unless cross-cutting task warrants it)
- Any existing doc pages (no content changes to other guides)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` lines 853-871] — Story 4.5 acceptance criteria and FR50
- [Source: `src/adk_secure_sessions/protocols.py`] — `EncryptionBackend` protocol definition (5 members)
- [Source: `src/adk_secure_sessions/serialization.py:50-53`] — `BACKEND_REGISTRY` dict with ID-to-name mapping
- [Source: `src/adk_secure_sessions/backends/fernet.py`] — FernetBackend reference implementation (backend_id 0x01)
- [Source: `src/adk_secure_sessions/backends/aes_gcm.py`] — AesGcmBackend reference implementation (backend_id 0x02)
- [Source: `docs/how-to/key-rotation.md`] — Style reference for how-to page format
- [Source: `docs/envelope-protocol.md`] — Envelope wire protocol specification
- [Source: `docs/contributing/docstring-templates.md`] — Docstring templates for code examples
- [Source: `.claude/rules/conventions.md#Protocols Over Inheritance`] — Protocol design principle
- [Source: `.claude/rules/conventions.md#Async-First by Design`] — `asyncio.to_thread()` requirement
- [Source: `_bmad-output/project-context.md#Encryption Architecture`] — Data flow contract
- [Source: `tests/unit/test_protocols.py`] — Protocol conformance test patterns (positive + negative `isinstance` checks)

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only; no src changes expected)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage
- [x] `pre-commit run --all-files` -- all hooks pass (including docvet, yamllint)

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
| 2026-03-28 | Created Backend Authoring Guide (`docs/how-to/backend-authoring.md`) with all 10 sections per Dev Notes consensus. Added mkdocs.yml nav entry. Cross-cutting: added `__all__` alphabetical sort test, fixed root `__init__.py` sort order. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None — clean implementation with no debugging required.

### Completion Notes List

- Created `docs/how-to/backend-authoring.md` (10 sections, ~300 lines) following Diataxis How-To pattern and matching `key-rotation.md` style
- All sections follow the Party Mode consensus order from Dev Notes: When to Write, Protocol Contract, Backend ID Assignment, Walkthrough (AesGcmBackend excerpts), Starter Template (SkeletonBackend), Registering (two-tier with admonition), Testing Checklist (7-item table), Common Pitfalls (6 anti-patterns), Security Notes, Related
- Added `Backend Authoring` nav entry under `How-To Guides:` in mkdocs.yml
- Cross-cutting test maturity: added `TestAllAlphabeticallySorted` parametrized test class to `test_public_api.py` covering all 3 `__init__.py` files — immediately caught and fixed a sort order bug in root `__all__` (`EncryptedSessionService` was before `ENVELOPE_VERSION_1`)
- All quality gates pass: pre-commit (10/10 hooks), mkdocs build --strict (exit 0), 9/9 public API tests pass

### File List

- `docs/how-to/backend-authoring.md` — NEW: Backend Authoring Guide
- `mkdocs.yml` — MODIFIED: added `Backend Authoring` nav entry
- `tests/unit/test_public_api.py` — MODIFIED: added `TestAllAlphabeticallySorted` test class (cross-cutting)
- `src/adk_secure_sessions/__init__.py` — MODIFIED: fixed `__all__` alphabetical sort order (cross-cutting)
