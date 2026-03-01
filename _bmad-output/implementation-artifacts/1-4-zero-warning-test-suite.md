# Story 1.4: Zero-Warning Test Suite

Status: done
Branch: feat/test-1-4-zero-warning-suite
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/48

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer evaluating the library**,
I want **`uv run pytest` to produce zero warnings and clean output**,
so that **running the test suite doesn't undermine confidence in the library's quality**.

## Acceptance Criteria

1. **Given** the current test suite produces intermittent warnings
   **When** I run `uv run pytest`
   **Then** the output shows zero warnings (FR32, NFR16)

2. **Given** the dependency chain includes google-adk, pydantic, aiosqlite
   **When** I run `uv run pytest`
   **Then** no deprecation warnings from dependencies appear

3. **Given** aiosqlite uses background threads for database connections
   **When** I run `uv run pytest`
   **Then** no `PytestUnraisableExceptionWarning` or `PytestUnhandledThreadExceptionWarning` or async cleanup warnings appear

4. **Given** the test suite currently has >= 90% coverage
   **When** I apply warning fixes
   **Then** code coverage remains >= 90% (NFR18)

5. **Given** the test suite is stable
   **When** I run the test suite 5 times sequentially on the same commit
   **Then** all 5 runs pass with zero warnings to verify no flaky tests (NFR17)
   **And** results are documented in this story's Dev Agent Record

## Tasks / Subtasks

- [x] Task 1: Audit and fix the aiosqlite thread cleanup warning (AC: #1, #3)
  - [x] 1.1 Run `uv run pytest -W all --tb=short` multiple times (3-5x) to reproduce the intermittent `PytestUnhandledThreadExceptionWarning` from `_connection_worker_thread`
  - [x] 1.2 Read the aiosqlite source code for `Connection.close()` — determine whether it joins `_connection_worker_thread` or just sends a sentinel and returns. This determines whether a fixture-level fix is possible or the race is inherent to aiosqlite's architecture
  - [x] 1.3 **Decision tree based on 1.2 findings:**
    - **If `close()` joins the thread:** The warning is a pytest timing issue. Fix in test fixtures (e.g., `tests/conftest.py`) by ensuring `await svc.close()` fully completes before pytest's thread handler runs. Remove the aiosqlite filter from pyproject.toml.
    - **If `close()` does NOT join the thread (likely):** The filter IS the correct solution, not a workaround. Keep the narrow filter in pyproject.toml, add a comment explaining it's an upstream aiosqlite limitation (`# aiosqlite.Connection.close() does not join _connection_worker_thread — race is inherent`), and consider opening an upstream aiosqlite issue if one doesn't already exist.
  - [x] 1.4 Whichever path: verify the warning no longer appears in 5+ consecutive runs

- [x] Task 2: Clean up stale warning filters in pyproject.toml (AC: #1, #2)
  - [x] 2.1 Remove stale Pydantic filters that no longer fire with current dependency versions:
    - `"ignore:.*PydanticDeprecatedSince20.*:DeprecationWarning"` — stale
    - `"ignore:.*Pydantic.*serialization.*:UserWarning"` — stale
    - `"ignore:.*Pydantic.*:UserWarning"` — stale
    - `"ignore:^deprecated$:DeprecationWarning:pydantic.*"` — stale
  - [x] 2.2 Remove stale ClientSession filter: `"ignore:Inheritance class.*from ClientSession is discouraged:DeprecationWarning"` — stale
  - [x] 2.3 Prove filters are truly stale: temporarily set `filterwarnings = ["error"]` with NO ignore filters and run `uv run pytest`. If all tests pass, the filters are confirmed stale. If any test fails with a warning-turned-error, identify which dependency emits it and at what version.
  - [x] 2.4 If any removed filter is actually still needed (regression), re-add it with an inline comment explaining which dependency emits it, the version range, and the upstream issue URL if applicable

- [x] Task 3: Fix ty type checker diagnostic (AC: #1)
  - [x] 3.1 Fix `tests/unit/test_encrypted_session_service.py:1071` — `len(rows)` where `rows` is typed as `Iterable[Row]` by aiosqlite stubs but is actually `list[Row]` at runtime
  - [x] 3.2 Use `rows = list(await cursor.fetchall())` to satisfy `Sized` protocol — this preserves the length assertion for AC-to-test traceability (do NOT use `assert rows` truthy check, which only proves non-empty, not the expected count)
  - [x] 3.3 Run `uv run ty check` to confirm zero diagnostics — note: ty runs on `src/` only in CI, but this diagnostic is in `tests/`. Fix it anyway for code quality consistency (NFR16 spirit), even though it won't fail CI

- [x] Task 4: Verify clean state and run flaky test check (AC: #1, #4, #5)
  - [x] 4.1 Run `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` — all tests pass, >= 90% coverage, zero warnings
  - [x] 4.2 Run the test suite 5 times sequentially: `for i in $(seq 1 5); do echo "--- Run $i ---"; uv run pytest -q --tb=short 2>&1; echo "Exit code: $?"; done` — all 5 must pass with zero warnings
  - [x] 4.3 Document each run's output in Dev Agent Record: run number, test count, pass/fail, warning count, exit code. This is a one-time pre-release gate (NFR17), not an ongoing CI requirement. All 5 runs must show 0 warnings.

- [x] Task 5: Run full quality pipeline (AC: #1-#5)
  - [x] 5.1 Run `uv run ruff check .` — zero violations
  - [x] 5.2 Run `uv run ruff format --check .` — zero format issues
  - [x] 5.3 Run `uv run ty check` — zero diagnostics
  - [x] 5.4 Run `pre-commit run --all-files` — all hooks pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | Full suite: `uv run pytest` output shows 0 warnings; 157 passed, 0 warnings | pass |
| 2    | Full suite: stale Pydantic/ClientSession filters removed; `filterwarnings=["error"]` proves no dependency deprecation warnings fire | pass |
| 3    | Full suite: aiosqlite thread warning suppressed by narrow filter with explanatory comment; `close()` does NOT join thread (verified via source review) | pass |
| 4    | `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` — 99.68% coverage | pass |
| 5    | 5 sequential runs documented in Dev Agent Record — all pass with 0 warnings | pass |

## Dev Notes

### What This Story Changes

**pyproject.toml warning filters + possibly test fixtures.** This story cleans up the pytest `filterwarnings` configuration by removing 5 stale filters that no longer fire with current dependency versions, fixes the root cause of an intermittent aiosqlite thread warning (or validates the existing narrow filter), and fixes a ty type diagnostic in a test file. No production code changes.

### Current Warning State (as of 2026-02-28)

**pyproject.toml filterwarnings (line 109-117):**
```toml
filterwarnings = [
    "error",
    "ignore:.*PydanticDeprecatedSince20.*:DeprecationWarning",        # STALE — no longer fires
    "ignore:.*Pydantic.*serialization.*:UserWarning",                  # STALE — no longer fires
    "ignore:.*Pydantic.*:UserWarning",                                 # STALE — no longer fires
    "ignore:^deprecated$:DeprecationWarning:pydantic.*",               # STALE — no longer fires
    "ignore:Inheritance class.*from ClientSession is discouraged:DeprecationWarning",  # STALE — no longer fires
    "ignore:Exception in thread.*_connection_worker_thread.*:pytest.PytestUnhandledThreadExceptionWarning",  # ACTIVE — aiosqlite race
]
```

- The `"error"` directive promotes all unfiltered warnings to test failures — this is the desired final state
- Filters 2-6 were needed for older google-adk/pydantic versions and no longer emit warnings
- Filter 7 (aiosqlite thread) is the only active filter — it suppresses an intermittent race condition in aiosqlite's `_connection_worker_thread` during fixture teardown

**ty diagnostic:**
- `tests/unit/test_encrypted_session_service.py:1071` — `len(rows)` on `Iterable[Row]` (aiosqlite stub types `fetchall()` as returning `Iterable[Row]`, but it's actually `list[Row]` at runtime)

### Exact Change Locations

**File 1:** `pyproject.toml` (lines 109-117)
- Remove 5 stale filters (lines 111-115)
- Keep `"error"` (line 110) and the aiosqlite thread filter (line 116) unless root cause is fixed
- Target state: either `["error"]` alone (if thread issue fixed) or `["error", "<narrow aiosqlite filter>"]`

**File 2:** `tests/unit/test_encrypted_session_service.py` (line ~1071)
- Fix `rows = await cursor.fetchall()` → `rows = list(await cursor.fetchall())` to satisfy `Sized` protocol for `len()` — preserves the count assertion needed for AC-to-test traceability

**File 3 (conditional — only if aiosqlite `close()` joins its thread):** `tests/conftest.py` or individual test files
- Add teardown synchronization in async generator fixtures that yield services with DB connections
- Only apply if source code review (Task 1.2) confirms a fixture-level fix is possible

### Investigating the aiosqlite Thread Warning

The intermittent `PytestUnhandledThreadExceptionWarning` occurs because:
1. aiosqlite uses a background thread (`_connection_worker_thread`) to run synchronous SQLite operations
2. When `svc.close()` is called in fixture teardown, it closes the aiosqlite connection
3. The background thread may still be processing when pytest's thread exception handler runs
4. If the thread raises after the test but before cleanup completes, pytest captures it as an unhandled thread exception

**Investigation approach (source-first, not guess-first):**
1. **Read aiosqlite source** — specifically `Connection.close()` and `_connection_worker_thread`. Determine if `close()` calls `thread.join()` on the worker thread or just sends a sentinel value to the queue and returns without waiting.
2. **If `close()` joins the thread:** The race is a pytest timing issue. Adding `await asyncio.sleep(0)` or an explicit yield point after `svc.close()` in fixtures may resolve it. Remove the filter from pyproject.toml.
3. **If `close()` does NOT join the thread (most likely):** The race is inherent to aiosqlite's architecture. The narrow `ignore` filter is the *correct* permanent solution, not a workaround. Keep it, add an explanatory comment, and optionally open an upstream aiosqlite issue. Do not spend hours chasing an upstream race condition.
4. Do NOT guess with `asyncio.sleep(0)` hacks before reading the source.

### Previous Story Intelligence (1.3)

**Patterns established:**
- `from __future__ import annotations` as first import in every file
- Absolute imports only
- Google-style docstrings with `Examples:` using fenced code blocks
- `pytestmark = pytest.mark.unit` at module level
- Shared fixtures in `tests/conftest.py`: `encrypted_service`, `fernet_backend`, `db_path`, `encryption_key`
- Async generator fixture pattern: `yield svc; await svc.close()`
- No `@pytest.mark.asyncio` — `asyncio_mode = "auto"`
- 154 tests passing at 99.68% coverage (after story 1.3)
- Exception message pattern: `msg = "..."; raise SomeError(msg)`

**Review learnings to carry forward:**
- Always add `pytestmark` to test files
- Use standard backticks in docstrings, not RST notation
- The `perf(test): skip PBKDF2 derivation in test fixtures (#47)` commit already optimized test performance — don't undo it

### Critical Guardrails

- **DO NOT** modify any production code in `src/` — this story is test infrastructure only
- **DO NOT** add new test files — only modify existing configuration and fixtures
- **DO NOT** weaken the `"error"` filterwarnings directive — it must remain as the first entry
- **DO NOT** add broad `ignore` filters — any remaining filters must be as narrow as possible with comments explaining the source
- **DO** remove stale filters before adding new ones
- **DO** attempt to fix root causes before resorting to filters
- **DO** verify with 5 sequential runs that warnings are truly eliminated, not just intermittent
- **DO** preserve all existing test functionality — zero regressions allowed

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| None | No user-facing changes — internal test infrastructure cleanup |

### Project Structure Notes

- All changes are in project root (`pyproject.toml`) and `tests/` directory
- No new files created
- No production source code changes
- Aligned with existing project structure — no variances

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- [Source: _bmad-output/project-context.md#Testing Rules]
- [Source: pyproject.toml#tool.pytest.ini_options (lines 99-117)]
- [Source: tests/unit/test_encrypted_session_service.py:1071 (ty diagnostic)]
- [Source: _bmad-output/implementation-artifacts/1-3-configurationerror-startup-validation.md#Previous Story Intelligence]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, 99.68% coverage
- [x] `pre-commit run --all-files` -- all 7 hooks pass

## Code Review

- **Reviewer:** Code Review Workflow (adversarial, 2026-02-28)
- **Outcome:** Approved with minor fix

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | MEDIUM | Sprint-status.yaml File List description did not enumerate out-of-scope 1-2/1-3 status corrections | Fixed — File List updated to document all three transitions |
| 2 | LOW (nit) | aiosqlite filter comment lacks upstream issue URL | Accepted — existing comment is self-contained and durable; upstream reference is nice-to-have |
| 3 | NIT | Debug log could label separate test sessions more clearly | Accepted — evidence is complete and correct; formatting is adequate |

### Verification

- [x] All HIGH findings resolved (none found)
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-02-28 | Removed 5 stale warning filters (4 Pydantic, 1 ClientSession) from pyproject.toml; validated aiosqlite thread filter as correct permanent solution with explanatory comment; fixed ty diagnostic in test_encrypted_session_service.py:1070; all quality gates pass |
| 2026-02-28 | Code review: 0 HIGH, 1 MEDIUM (File List description fix applied), 1 LOW + 1 NIT accepted. Story approved. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- aiosqlite source review: `.venv/lib/python3.12/site-packages/aiosqlite/core.py` — `Connection.close()` (lines 199-214) and `stop()` (lines 116-132) confirmed: no `thread.join()` call exists. The `_connection_worker_thread` may still be alive after `close()` returns.
- Intermittent thread race reproduced: 3/5 runs failed with `PytestUnhandledThreadExceptionWarning` when all filters removed. Root cause: event loop closed by pytest-asyncio before worker thread processes the `_STOP_RUNNING_SENTINEL`, causing `RuntimeError("Event loop is closed")` in `call_soon_threadsafe()`.
- Stale filter proof: with `filterwarnings = ["error"]` and NO ignore filters, 10 consecutive runs passed (Pydantic/ClientSession warnings confirmed stale). The aiosqlite thread race only manifested on run 9 of 20, confirming its intermittent nature.

### Completion Notes List

- Removed 5 stale warning filters from `pyproject.toml` filterwarnings: 4 Pydantic filters and 1 ClientSession filter that no longer fire with current dependency versions (google-adk >=1.22.0, pydantic v2 current)
- Validated the aiosqlite `_connection_worker_thread` filter as the correct permanent solution (not a workaround). Added a 4-line explanatory comment documenting the upstream limitation.
- Fixed ty type diagnostic: `rows = await cursor.fetchall()` changed to `rows = list(await cursor.fetchall())` at `test_encrypted_session_service.py:1070` to satisfy `Sized` protocol for `len()` call
- Final filter state: `["error", "<narrow aiosqlite filter>"]` — the "error" directive promotes all unfiltered warnings to test failures; only the inherent aiosqlite race is suppressed
- All quality gates verified: ruff check, ruff format, ty check, pytest (157 tests, 99.68% coverage), pre-commit (7 hooks)

### Flaky Test Check (5 Sequential Runs)

| Run | Tests | Result | Warnings | Exit Code |
|-----|-------|--------|----------|-----------|
| 1   | 157   | passed | 0        | 0         |
| 2   | 157   | passed | 0        | 0         |
| 3   | 157   | passed | 0        | 0         |
| 4   | 157   | passed | 0        | 0         |
| 5   | 157   | passed | 0        | 0         |

### File List

- `pyproject.toml` — removed 5 stale filterwarnings entries, added explanatory comment to aiosqlite filter
- `tests/unit/test_encrypted_session_service.py` — line 1070: `rows = list(await cursor.fetchall())` to fix ty diagnostic
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — updated 1-4 status (backlog -> review); also corrected stale statuses for 1-2 and 1-3 (review -> done, both already merged to develop)
- `_bmad-output/implementation-artifacts/1-4-zero-warning-test-suite.md` — story file updated with task completions, AC mapping, dev agent record
