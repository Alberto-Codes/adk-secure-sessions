# Story 2.1: Docstring Examples on All Public APIs

Status: review
Branch: feat/docs-2-1-docstring-examples
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/81

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer reading API documentation or IDE tooltips**,
I want **every public function and class to have an `Examples:` section with fenced code blocks**,
so that **I can see real usage patterns without leaving my editor or the API reference page**.

## Acceptance Criteria

1. **Given** 13 public symbols exported from `__init__.py`
   **When** all public API docstrings are reviewed
   **Then** every public class and function has at least one working code example in its docstring (FR41)
   **And** examples use Google-style docstring format with **fenced code blocks** (` ```python `) — NOT `::` indented style or `>>>` doctest style

2. **Given** the docstring template guidance in `docs/contributing/docstring-templates.md`
   **When** examples are added or converted
   **Then** example depth matches the symbol type:
   - `EncryptedSessionService`: full lifecycle example (instantiate, create session, get session, close)
   - `FernetBackend`: standalone instantiation example
   - `encrypt_session` / `decrypt_session`: round-trip example
   - Exception classes: try/except example showing when raised
   - `EncryptionBackend` protocol: custom backend implementation example

3. **Given** some existing docstrings use `::` indented-code style (module-level AND class-level)
   **When** these are discovered in files being modified
   **Then** ALL `::` blocks are converted to fenced ` ```python ` blocks — including module-level docstrings

4. **Given** all docstring changes are complete
   **When** the quality pipeline runs
   **Then** `interrogate` reports >= 95% docstring coverage
   **And** `griffe` parses all docstrings without errors
   **And** `docvet` pre-commit hook passes on all modified files with fail-on enforcement
   **And** `pre-commit run --all-files` passes

5. **Given** any inconsistencies between docstrings and actual signatures discovered during example writing
   **When** the inconsistency is identified
   **Then** the docstring is fixed to match the actual code signature (code is source of truth)

6. **Given** the dual-convention guidance in `docs/contributing/docstring-templates.md` and `_bmad-output/project-context.md`
   **When** the convention is updated to fenced-blocks-everywhere
   **Then** `docstring-templates.md` is updated to prescribe fenced ` ```python ` blocks for ALL docstrings (module, class, and function) — removing the `::` directive guidance
   **And** `project-context.md` module docstring rule is updated to use fenced blocks instead of `Typical usage::`

7. **Given** docvet enforcement is currently warn-only (no `[tool.docvet]` config)
   **When** `pyproject.toml` is updated
   **Then** `[tool.docvet]` section is added with `fail-on = ["enrichment", "freshness", "coverage", "griffe"]` to match docvet's own enforcement level

## Tasks / Subtasks

- [x] Task 1: Convert `fernet.py` module docstring from `::` to fenced blocks (AC: #3)
  - [x] 1.1 Convert `Examples:` section in `backends/fernet.py:17-24` from `Basic usage::` to fenced ` ```python ` block
  - [x] 1.2 Verify the example code is accurate (imports, await usage)

- [x] Task 2: Convert `FernetBackend` class docstring from `::` to fenced blocks (AC: #1, #3)
  - [x] 2.1 Convert `Examples:` section in `backends/fernet.py:52-62` from `::` indented style to ` ```python ` fenced blocks
  - [x] 2.2 Verify the examples are accurate against the actual `__init__` signature: `FernetBackend(key: str | bytes)`

- [x] Task 3: Convert `encrypted_session.py` module docstring from `::` to fenced blocks (AC: #3)
  - [x] 3.1 Convert `Examples:` section in `services/encrypted_session.py:6-22` from `Basic usage with FernetBackend::` to fenced ` ```python ` block
  - [x] 3.2 Verify the example code is accurate (imports, async with pattern)

- [x] Task 4: Convert `EncryptedSessionService` class docstring from `::` to fenced blocks (AC: #1, #3)
  - [x] 4.1 Convert `Examples:` section in `services/encrypted_session.py:119-135` from `::` indented style to ` ```python ` fenced blocks
  - [x] 4.2 The existing example shows the `async with` pattern — keep that, but wrap in fenced block

- [x] Task 5: Add `Examples:` to `create_session` (AC: #1, #2)
  - [x] 5.1 Add fenced-block example to `services/encrypted_session.py:222` (after the `Raises:` section, before closing `"""`)
  - [x] 5.2 Example must show: keyword-only args `app_name`, `user_id`, optional `state` dict, returned `Session` object

- [x] Task 6: Add `Examples:` to `get_session` (AC: #1, #2)
  - [x] 6.1 Add fenced-block example to `services/encrypted_session.py:381` (after the `Raises:` section)
  - [x] 6.2 Example must show: retrieving a session by ID, handling `None` return (session not found)

- [x] Task 7: Add `Examples:` to `list_sessions` (AC: #1, #2)
  - [x] 7.1 Add fenced-block example to `services/encrypted_session.py:441` (after the `Raises:` section)
  - [x] 7.2 Example must show: listing sessions for an app/user, accessing `response.sessions`

- [x] Task 8: Add `Examples:` to `delete_session` (AC: #1, #2)
  - [x] 8.1 Add fenced-block example to `services/encrypted_session.py:499` (after the `Note:` section)
  - [x] 8.2 Example must show: deleting by app_name, user_id, session_id

- [x] Task 9: Add `Examples:` to `append_event` (AC: #1, #2)
  - [x] 9.1 Add fenced-block example to `services/encrypted_session.py:681` (after the `Note:` section)
  - [x] 9.2 Example must show: creating an `Event` and appending it to a session

- [x] Task 10: Update `docstring-templates.md` — eliminate dual convention (AC: #6)
  - [x] 10.1 Remove all `::` directive guidance from the module template and any prose
  - [x] 10.2 Change module template `Typical usage::` to use fenced ` ```python ` block
  - [x] 10.3 Add a clear rule: "All `Examples:` and `Typical usage:` sections use fenced ` ```python ` blocks. No `::` directive, no `>>>` doctest."
  - [x] 10.4 Update `See Also:` examples to use shorter `[`module`][]` auto-link syntax (docvet pattern)

- [x] Task 11: Update `project-context.md` — align module docstring rule (AC: #6)
  - [x] 11.1 Change the "Module docstrings" bullet from `Typical usage::` block (uses `::` directive)` to fenced ` ```python ` block
  - [x] 11.2 Update the "Docstring Examples" bullet to remove any mention of `::` as acceptable

- [x] Task 12: Add `[tool.docvet]` fail-on config to `pyproject.toml` (AC: #7)
  - [x] 12.1 Add `[tool.docvet]` section with `fail-on = ["enrichment", "freshness", "coverage", "griffe"]`
  - [x] 12.2 Verify `pre-commit run --all-files` still passes with the stricter enforcement

- [x] Task 13: Run quality gates and verify (AC: #4, #5)
  - [x] 13.1 Run `pre-commit run --all-files` — all hooks pass with docvet fail-on enforcement
  - [x] 13.2 Run `uv run pytest` — all tests still pass (docstring changes must not break imports or test fixtures)
  - [x] 13.3 Verify `uv run interrogate src/` reports >= 95%
  - [x] 13.4 Verify no signature/docstring mismatches were introduced

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1 | Visual inspection: all public symbols in fernet.py + encrypted_session.py have fenced `Examples:` | pass |
| 2 | Visual inspection: example depth matches symbol type (lifecycle for ESS, standalone for FernetBackend, round-trip methods, etc.) | pass |
| 3 | `grep '::\s*$'` on modified source files returns zero matches | pass |
| 4 | `pre-commit run --all-files` passes (all 9 hooks incl. docvet fail-on); interrogate removed from project — docvet covers coverage | pass |
| 5 | Visual inspection: all examples use correct keyword-only args matching actual signatures | pass |
| 6 | `docstring-templates.md` updated: fenced-blocks-only rule added, `See Also:` uses `[][]` syntax; `project-context.md` updated | pass |
| 7 | `[tool.docvet]` added to pyproject.toml; `pre-commit run --all-files` passes with fail-on enforcement | pass |

## Dev Notes

### What This Story Does

This story adds or converts `Examples:` sections in docstrings to use **fenced code blocks** (` ```python `) and standardizes the project convention to fenced-blocks-everywhere. It also promotes docvet from warn-only to fail-on enforcement.

### Why Fenced Blocks Everywhere (No Dual Convention)

Research into docvet's source code revealed that the `::` indented-code style in module-level docstrings was **an inconsistency in docvet itself, not an intentional convention.** docvet's `prefer-fenced-code-blocks` rule only detects `>>>` doctest patterns — it does not flag `::` blocks. The module-level `::` blocks in docvet's own source pass the rule because the rule has a detection gap.

**mkdocs-material rendering difference:**
- `::` indented blocks: plain unstyled preformatted text — **no syntax highlighting, no copy button, no language tag**
- Fenced ` ```python ` blocks: full syntax highlighting, copy button, language indicator

There is zero benefit to `::` in mkdocs-material. Our previous dual convention (module = `::`, class/function = fenced) was based on mimicking docvet's accidental pattern. This story eliminates it.

**Reference:** See docvet API reference pages for the visual difference — e.g., `https://alberto-codes.github.io/docvet/reference/config/` shows `::` at module level (unstyled) and fenced blocks in class docstrings (highlighted). The `cli`, `discovery`, and `reporting` module pages show the same contrast.

### Current Docstring Audit (Pre-Implementation)

**Already compliant (12 symbols with fenced `Examples:`):**
- `EncryptionBackend` class + `encrypt` + `decrypt` methods (protocols.py)
- `SecureSessionError`, `EncryptionError`, `DecryptionError`, `SerializationError`, `ConfigurationError` (exceptions.py)
- `encrypt_session`, `decrypt_session`, `encrypt_json`, `decrypt_json` (serialization.py)
- `FernetBackend.encrypt`, `FernetBackend.decrypt` methods (backends/fernet.py)

**Needs conversion from `::` to fenced blocks (4 docstrings in 2 files):**
- `backends/fernet.py` module docstring — line 17-24
- `FernetBackend` class docstring — line 52-62
- `services/encrypted_session.py` module docstring — line 6-22
- `EncryptedSessionService` class docstring — line 119-135

**Needs new `Examples:` sections (5 public methods):**
- `EncryptedSessionService.create_session` — `services/encrypted_session.py:222`
- `EncryptedSessionService.get_session` — `services/encrypted_session.py:381`
- `EncryptedSessionService.list_sessions` — `services/encrypted_session.py:441`
- `EncryptedSessionService.delete_session` — `services/encrypted_session.py:499`
- `EncryptedSessionService.append_event` — `services/encrypted_session.py:681`

**Not in scope for `::` conversion (files not being modified):**
- `__init__.py` module docstring — has `::` but not touched in this story
- `protocols.py` module docstring — has `::` but not touched in this story
- `serialization.py` module docstring — has `::` but not touched in this story
- These can be converted opportunistically in future stories that touch those files

**Excluded from Examples scope (deliberate):**
- `BACKEND_FERNET` and `ENVELOPE_VERSION_1` — module-level constants; examples don't apply
- `EncryptedSessionService.close` — covered by the class-level `async with` example
- `FernetBackend.__init__` — `ignore-init-method = true` in interrogate; class example covers it

### Files to Modify

| File | Changes |
|------|---------|
| `src/adk_secure_sessions/backends/fernet.py` | Convert module + class docstring `::` to fenced blocks |
| `src/adk_secure_sessions/services/encrypted_session.py` | Convert module + class docstring `::` to fenced blocks + add 5 method `Examples:` sections |
| `docs/contributing/docstring-templates.md` | Eliminate dual convention — fenced blocks everywhere; update `See Also:` syntax |
| `_bmad-output/project-context.md` | Update module docstring rule to fenced blocks |
| `pyproject.toml` | Add `[tool.docvet]` fail-on config |

**Total: 5 files modified.** No new files created.

### Docstring Format Rules (Post-Update)

After this story, the single convention is:
- **All** `Examples:` and `Typical usage:` sections use fenced ` ```python ` blocks
- No `::` directive anywhere in docstrings
- No `>>>` doctest format anywhere in docstrings
- `See Also:` cross-references use `[`module`][]` auto-link syntax
- Section order: summary -> description -> Args -> Returns -> Raises -> Yields -> Examples -> See Also -> Note -> Warning

### Method Signatures Reference

The dev agent must use these exact signatures when writing examples:

```python
# create_session
async def create_session(
    self,
    *,
    app_name: str,
    user_id: str,
    state: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> Session:

# get_session
async def get_session(
    self,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
    config: GetSessionConfig | None = None,
) -> Session | None:

# list_sessions
async def list_sessions(
    self,
    *,
    app_name: str,
    user_id: str | None = None,
) -> ListSessionsResponse:

# delete_session
async def delete_session(
    self,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
) -> None:

# append_event
async def append_event(
    self,
    session: Session,
    event: Event,
) -> Event:
```

All methods use **keyword-only args** (after `*`), except `append_event` which takes positional `session` and `event`.

### Example Style Guide

All examples must follow these patterns:

1. **Use `await`** — all public methods are async
2. **Assume the service is already instantiated** — don't repeat the `async with` setup in every method example (class docstring covers that)
3. **Show realistic values** — use `"my-agent"` for app_name, `"user-123"` for user_id, meaningful state dicts
4. **Keep examples short** — 3-8 lines per example, focused on the specific method
5. **Use fenced blocks** — ` ```python ` everywhere, no exceptions
6. **No imports needed in method examples** — the class example shows the imports

Example of the target format for a method:
```
    Examples:
        Create a session with initial state:

        ```python
        session = await service.create_session(
            app_name="my-agent",
            user_id="user-123",
            state={"preference": "dark-mode"},
        )
        ```
```

### Anti-Patterns to Avoid

- **DO NOT** use `>>>` doctest format — fenced blocks only
- **DO NOT** use `::` indented-code — fenced blocks only, at ALL levels (module, class, function)
- **DO NOT** add imports to method examples — they're redundant within the class
- **DO NOT** include error-handling in basic examples unless the method's primary purpose involves error handling
- **DO NOT** modify any function signatures, test files, or non-docstring code (except `pyproject.toml` for docvet config)
- **DO NOT** add `@pytest.mark.asyncio` to any file — project uses `asyncio_mode = "auto"`
- **DO NOT** convert `::` blocks in files NOT being modified (e.g., `__init__.py`, `protocols.py`, `serialization.py`) — those are future cleanup

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| docs/reference/ (auto-generated) | Examples render with syntax highlighting via mkdocstrings — auto-updated |
| docs/contributing/docstring-templates.md | Eliminate dual convention — fenced blocks everywhere |
| _bmad-output/project-context.md | Align module docstring rule to fenced blocks |

### Project Structure Notes

- Source code lives under `src/adk_secure_sessions/`
- 2 source files + 1 docs file + 1 project-context file + 1 config file = 5 files total
- No CI workflow changes, no pre-commit config changes, no mkdocs.yml changes (mkdocs config alignment is Story 2.2)

### Peripheral Config: pyproject.toml

Adding `[tool.docvet]` section only. No changes to:
- `[project]` metadata
- `[tool.ruff]` config
- `[tool.pytest]` config
- `[tool.interrogate]` config
- Any other existing sections

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1 — Docstring Examples on All Public APIs]
- [Source: docs/contributing/docstring-templates.md — Docstring format templates and conventions]
- [Source: _bmad-output/project-context.md#Docstring Requirements — Google-style with fenced blocks]
- [Source: src/adk_secure_sessions/__init__.py — 13 public symbols in __all__]
- [Source: FR41 — Docstring examples with fenced code blocks for all public API functions and classes]
- [Source: docvet source — prefer-fenced-code-blocks rule only flags >>>, not :: (detection gap)]
- [Source: https://alberto-codes.github.io/docvet/reference/config/ — visual proof of :: vs fenced rendering]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest` -- 167 passed, 0 failed
- [x] `pre-commit run --all-files` -- all 9 hooks pass (with docvet fail-on enforcement)

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
| 2026-03-01 | Story created by create-story workflow. Comprehensive docstring audit completed — 12/13+ symbols already compliant, 2 need `::` conversion, 5 need new `Examples:` sections. |
| 2026-03-01 | Party mode research: Investigated docvet source code and mkdocs patterns. Found `::` blocks in docvet module docstrings are an inconsistency (prefer-fenced-code-blocks rule only flags `>>>`, not `::`). mkdocs-material renders `::` without syntax highlighting or copy buttons. Eliminated dual convention — fenced blocks everywhere. Added: module-level `::` conversion (Tasks 1, 3), docstring-templates.md update (Task 10), project-context.md update (Task 11), `[tool.docvet]` fail-on config (Task 12). Scope: 2 files -> 5 files. |
| 2026-03-02 | Implementation complete. All 13 tasks done: 4 `::` to fenced conversions, 5 new `Examples:` sections, docstring-templates.md and project-context.md aligned, `[tool.docvet]` fail-on config added. All quality gates pass. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — no errors encountered during implementation.

### Completion Notes List

- Converted 4 `::` indented-code blocks to fenced ` ```python ` blocks (2 in fernet.py, 2 in encrypted_session.py)
- Added 5 new `Examples:` sections to public methods: create_session, get_session, list_sessions, delete_session, append_event
- Updated docstring-templates.md: replaced "Prefer fenced" with explicit "no `::`, no `>>>`" rule; updated See Also to `[][]` auto-link syntax
- Updated project-context.md: aligned module docstring rule and docstring examples bullet to fenced-blocks-only
- Added `[tool.docvet]` section to pyproject.toml with fail-on enforcement
- All quality gates pass: ruff check, ruff format, ty check, pytest (167 passed), pre-commit (9/9 hooks pass including docvet)
- Note: interrogate was previously removed from the project (commit 230973c); docvet now handles docstring coverage checks

### File List

- `src/adk_secure_sessions/backends/fernet.py` — converted module + class docstring `::` to fenced blocks
- `src/adk_secure_sessions/services/encrypted_session.py` — converted module + class docstring `::` to fenced blocks; added 5 method `Examples:` sections
- `docs/contributing/docstring-templates.md` — eliminated dual convention, updated See Also syntax
- `_bmad-output/project-context.md` — aligned module docstring rule to fenced blocks
- `pyproject.toml` — added `[tool.docvet]` fail-on config
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status tracking updates
- `_bmad-output/implementation-artifacts/2-1-docstring-examples-on-all-public-apis.md` — story file tracking
