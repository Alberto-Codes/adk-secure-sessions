# Story 1.6a: ADK Runner Integration Test

Status: review
Branch: feat/integration-1-6a-adk-runner-test
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/52

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **library maintainer**,
I want **an integration test proving EncryptedSessionService works as an ADK drop-in**,
so that **I can ship with confidence that the library satisfies the BaseSessionService contract in a real ADK pipeline**.

## Acceptance Criteria

1. **Given** an `EncryptedSessionService` instance configured with a FernetBackend
   **When** an ADK `Runner` accepts it as the `session_service` parameter (where it expects `BaseSessionService`)
   **Then** the `Runner` instantiates without error and is ready to execute agent turns (NFR20)

2. **Given** the `Runner` is configured with the `EncryptedSessionService` and a callback-based test agent (no real LLM)
   **When** a complete session lifecycle executes through the Runner (create session, run agent turn, get session, delete session)
   **Then** all operations succeed end-to-end, events are persisted, and session state is retrievable with correct values

3. **Given** the test verifies the ADK drop-in contract
   **When** I inspect the test implementation
   **Then** it uses **actual execution** through `Runner.run_async()`, not just `isinstance(service, BaseSessionService)` checks

4. **Given** the integration test exists
   **When** I check its pytest markers
   **Then** the test is marked with `@pytest.mark.integration`

5. **Given** the integration test creates database connections and services
   **When** the test completes (pass or fail)
   **Then** all database connections are properly closed via async generator fixtures with `yield svc; await svc.close()`

## Tasks / Subtasks

- [x] Task 1: Create the ADK Runner integration test (AC: #1, #2, #3, #4)
  - [x] 1.1 Create `tests/integration/test_adk_runner.py` with `pytestmark = pytest.mark.integration`
  - [x] 1.2 Implement a `before_agent_callback` that returns a `types.Content` response (short-circuits LLM, no API keys needed)
  - [x] 1.3 Create an `LlmAgent` with the callback — model string can be any valid model name since it won't be called
  - [x] 1.4 Create a `Runner(agent=agent, app_name=..., session_service=encrypted_service)` using the shared `encrypted_service` fixture
  - [x] 1.5 Test the full lifecycle: `create_session` → `Runner.run_async()` → `get_session` → verify events persisted → raw-DB encryption assertion → `delete_session` → verify deletion
  - [x] 1.6 Assert retrieved session has the correct state, events include the agent's response, raw DB contains ciphertext (not plaintext), and session is fully deletable
  - [x] 1.7 Ensure `await runner.close()` is called in teardown (Runner holds plugin manager resources)

- [x] Task 2: Add state delta verification through Runner turn (AC: #2)
  - [x] 2.1 Create a callback that also sets state via `callback_context.state` (e.g., `callback_context.state["agent_response_count"] = 1`)
  - [x] 2.2 After `Runner.run_async()`, retrieve session and verify the state delta was persisted and encrypted
  - [x] 2.3 Verify the state is correctly decrypted on retrieval (not raw ciphertext)

- [x] Task 3: Add multi-turn conversation test (AC: #2, #3)
  - [x] 3.1 Run two sequential agent turns through `Runner.run_async()` on the same session
  - [x] 3.2 After both turns, retrieve session and verify exactly **4 events** (2 user + 2 agent), present and ordered
  - [x] 3.3 Verify conversation history accumulates correctly: each `run_async()` yields 1 event to the caller but creates 2 in the session (user message + agent response). After 2 turns: `assert len(retrieved.events) == 4`

- [x] Task 4: Verify fixture teardown and connection cleanup (AC: #5)
  - [x] 4.1 Ensure the `encrypted_service` fixture from `tests/conftest.py` handles cleanup (it already does via async generator)
  - [x] 4.2 Verify no leaked database connections by confirming the test passes `pre-commit run --all-files` cleanly

- [x] Task 5: Run quality gates (AC: all)
  - [x] 5.1 `uv run ruff check .` — zero violations
  - [x] 5.2 `uv run ruff format --check .` — zero format issues
  - [x] 5.3 `uv run ty check` — zero type errors (src/ only)
  - [x] 5.4 `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` — all tests pass, >= 90% coverage
  - [x] 5.5 `pre-commit run --all-files` — all hooks pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_runner_accepts_encrypted_service` | pass |
| 2    | `test_full_lifecycle_through_runner`, `test_state_delta_persists_through_runner`, `test_state_delta_is_encrypted_in_database`, `test_two_turns_produce_four_events`, `test_state_accumulates_across_turns` | pass |
| 3    | `test_full_lifecycle_through_runner`, `test_two_turns_produce_four_events` (both use actual `Runner.run_async()`) | pass |
| 4    | Module-level `pytestmark = pytest.mark.integration` verified | pass |
| 5    | `encrypted_service` fixture uses async generator with `yield svc; await svc.close()`; runner fixtures use `yield r; await r.close()`; `pre-commit run --all-files` passes cleanly | pass |

## Dev Notes

### What This Story Creates

A new integration test at `tests/integration/test_adk_runner.py` that proves `EncryptedSessionService` works as a genuine ADK drop-in by passing it to an actual `Runner` instance and executing agent turns. This is the definitive NFR20 verification — not just an `isinstance` check, but real execution through the ADK pipeline.

**No production code changes.** This story creates test files only.

### ADK Runner Integration Pattern

The key insight is using `before_agent_callback` to short-circuit the LLM, allowing real `Runner` execution without API keys:

```python
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.genai import types

async def echo_callback(callback_context):
    """Short-circuit LLM — returns content directly."""
    return types.Content(parts=[types.Part(text="Agent response")])

agent = LlmAgent(
    name="test_agent",
    model="gemini-2.0-flash",  # Never called — callback intercepts
    before_agent_callback=echo_callback,
)

runner = Runner(
    agent=agent,
    app_name="test_app",
    session_service=encrypted_service,  # Our EncryptedSessionService
)
```

**Why this works:** `Runner.__init__` accepts `session_service: BaseSessionService`. Since `EncryptedSessionService` extends `BaseSessionService`, the Runner accepts it. The `before_agent_callback` returns a `Content` object, which the Runner processes as the agent's response — creating events and calling `session_service.append_event()`. This exercises the full ADK pipeline:

1. `Runner.run_async()` calls `session_service.get_session()` to load the session
2. Runner creates user message event via `session_service.append_event()`
3. Runner calls `before_agent_callback` (our mock) which returns content
4. Runner creates agent response event via `session_service.append_event()`
5. All events flow through `encrypt → DB write → DB read → decrypt` via our service

**Callback signature:** `async def callback(callback_context)` — the parameter MUST be named `callback_context` (ADK passes it as a keyword argument). It receives a `CallbackContext` instance. Return `types.Content` to short-circuit the LLM.

**State deltas:** To test state persistence through Runner turns, use `callback_context.state["key"] = value` inside the callback. The Runner will persist this via `session_service.append_event()` with state delta extraction.

### Runner Constructor Signature (google-adk 1.23.0)

```python
Runner(
    self,
    *,
    app: Optional[App] = None,
    app_name: Optional[str] = None,
    agent: Optional[BaseAgent] = None,
    plugins: Optional[List[BasePlugin]] = None,
    artifact_service: Optional[BaseArtifactService] = None,
    session_service: BaseSessionService,  # REQUIRED — our integration point
    memory_service: Optional[BaseMemoryService] = None,
    credential_service: Optional[BaseCredentialService] = None,
    plugin_close_timeout: float = 5.0,
    auto_create_session: bool = False,
)
```

The `session_service` is the only required parameter (besides `agent`). Pass `app_name` as a string instead of an `App` instance for testing.

### Runner.run_async() Signature

```python
async def run_async(
    self,
    *,
    user_id: str,
    session_id: str,
    invocation_id: Optional[str] = None,
    new_message: Optional[types.Content] = None,
    state_delta: Optional[dict[str, Any]] = None,
    run_config: Optional[RunConfig] = None,
) -> AsyncGenerator[Event, None]
```

Call pattern:
```python
message = types.Content(parts=[types.Part(text="Hello")])
events = []
async for event in runner.run_async(
    user_id="test_user",
    session_id=session.id,
    new_message=message,
):
    events.append(event)
```

### Exact File Locations

| File | Action | Purpose |
|------|--------|---------|
| `tests/integration/test_adk_runner.py` | CREATE | ADK Runner integration test |

### Fixture Reuse Strategy

Reuse from `tests/conftest.py`:
- `fernet_backend` — pre-generated Fernet key, skips PBKDF2 derivation
- `fernet_key_bytes` — raw key bytes
- `db_path` — temp SQLite path from `tmp_path`
- `encrypted_service` — initialized `EncryptedSessionService` with cleanup

The `encrypted_service` fixture already does `await svc._init_db()` and `await svc.close()` — use it directly. No additional fixtures needed in `tests/integration/conftest.py` (it already exists and is empty aside from a docstring).

### Test Structure

```python
# tests/integration/test_adk_runner.py

APP_NAME = "test_app"  # Shared constant — Runner and create_session MUST match

@pytest.fixture
async def runner(encrypted_service):
    """Runner with callback agent, properly cleaned up."""
    agent = LlmAgent(name="test_agent", model="gemini-2.0-flash", before_agent_callback=echo_callback)
    r = Runner(agent=agent, app_name=APP_NAME, session_service=encrypted_service)
    yield r
    await r.close()

class TestADKRunnerIntegration:
    """T049: EncryptedSessionService as ADK Runner drop-in."""

    async def test_runner_accepts_encrypted_service(self, encrypted_service):
        """Runner instantiates with EncryptedSessionService."""
        # AC #1: Runner accepts our service

    async def test_full_lifecycle_through_runner(self, runner, encrypted_service, db_path):
        """Create → run turn → get → raw-DB encryption check → delete."""
        # AC #2, #3: Full lifecycle via actual Runner execution + encryption verification

    async def test_state_delta_persists_through_runner(self, runner, encrypted_service):
        """State changes via callback_context.state persist encrypted."""
        # AC #2: State delta verification

    async def test_multi_turn_conversation(self, runner, encrypted_service):
        """Two sequential turns produce exactly 4 events (2 user + 2 agent)."""
        # AC #2, #3: Multi-turn via actual Runner execution
```

### Critical Guardrails

- **DO NOT** add any new dependencies — `google-adk` (which includes `Runner`, `LlmAgent`, `types`) is already in the project's dependencies
- **DO NOT** use real LLM API calls — always use `before_agent_callback` to short-circuit
- **DO NOT** modify any production code in `src/` — this story creates test files only
- **DO NOT** duplicate fixtures from `tests/conftest.py` — reuse them via pytest's fixture discovery
- **DO** use `@pytest.mark.integration` marker (already via module-level `pytestmark`)
- **DO** name the callback parameter `callback_context` exactly (ADK passes it as keyword arg)
- **DO** use `from __future__ import annotations` as first import
- **DO** use `types.Content(parts=[types.Part(text=...)])` for creating messages — this is the ADK convention
- **DO NOT** use `@pytest.mark.asyncio` — `asyncio_mode = "auto"` handles it
- **DO** verify events are persisted by calling `get_session` after `run_async` completes
- **DO** test deletion after the full lifecycle to verify cascade cleanup works through the Runner path
- **DO** use the **same `app_name` string** for `Runner(app_name=...)` and `svc.create_session(app_name=...)` — Runner resolves sessions by `app_name`, mismatches silently fail
- **DO** call `await runner.close()` in test teardown — Runner holds a plugin manager that needs cleanup. Use a local fixture or `try/finally`
- **DO** add one raw-DB read assertion in the lifecycle test to confirm data written through the Runner path is encrypted (e.g., `assert b"agent_ran" not in raw_state_blob`)

### ADK Version Compatibility

The `Runner` class and `before_agent_callback` pattern have been verified on google-adk 1.23.0 (currently installed). The CI matrix tests against `1.22.0` and `latest`. Key compatibility notes:

- `Runner` accepts `session_service: BaseSessionService` since at least 1.22.0
- `before_agent_callback` with `callback_context` keyword parameter is stable
- `types.Content` and `types.Part` are from `google.genai.types` (transitive dep of google-adk)

If the callback signature changes between ADK versions, the test will fail with a clear `TypeError` — this is desirable behavior for a compatibility test.

### Previous Story Intelligence (1.5)

**Patterns established:**
- `from __future__ import annotations` as first import in every file
- `pytestmark = pytest.mark.integration` at module level (use `integration` not `benchmark`)
- Shared fixtures in `tests/conftest.py`: `encrypted_service`, `fernet_backend`, `db_path`, `fernet_key_bytes`
- Async generator fixture pattern: `yield svc; await svc.close()`
- No `@pytest.mark.asyncio` — `asyncio_mode = "auto"` handles it
- 157 tests passing at 99.68% coverage (+ 1 benchmark deselected)
- Exception message pattern: `msg = "..."; raise SomeError(msg)`

**Review learnings to carry forward:**
- Always add `pytestmark` to test files
- Use standard backticks in docstrings, not RST notation
- Pre-generated Fernet keys skip PBKDF2 derivation (~0.5s per call) — use `fernet_backend` fixture
- The `addopts = "-m 'not benchmark'"` in pyproject.toml means integration tests DO run by default
- Code review caught dead `TYPE_CHECKING` blocks and inaccurate task completion claims — verify everything

### Git Context

Recent commits on develop:
- `4561a99` test(benchmark): add encryption overhead benchmark and modernize CI
- `7cf58d8` test(warnings): remove stale filters and fix ty diagnostic
- `a7e3a34` perf(test): skip PBKDF2 derivation in test fixtures (#47)
- `4156996` feat(exceptions): add ConfigurationError and startup validation (#45)
- `83f44b5` feat(schema): reserve version column for optimistic concurrency (#43)

The `test(benchmark)` commit (4561a99) is the most recent — story 1.5. The current story adds a new test file in `tests/integration/` alongside the existing `test_adk_integration.py`.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| None | No user-facing changes — internal integration test verifying NFR20 |

### Project Structure Notes

- New file: `tests/integration/test_adk_runner.py` — alongside existing `test_adk_integration.py`
- The `integration` marker is already registered in `pyproject.toml` (added in story 1.1)
- Integration tests run by default (`addopts` only excludes `benchmark`)
- No production source code changes
- No new dependencies

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6a (line 364)]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR20 (line 830)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Test Fixture Naming (line 538-544)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Test Organization (line 887)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure - tests/integration/ (line 631-634)]
- [Source: tests/integration/test_adk_integration.py — existing integration test patterns]
- [Source: tests/conftest.py — shared fixtures]
- [Source: _bmad-output/implementation-artifacts/1-5-encryption-overhead-benchmark.md — previous story learnings]
- [Source: google.adk.runners.Runner — constructor accepts session_service: BaseSessionService]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 163 pass, 1 deselected, 99.68% coverage
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
| 2026-02-28 | Story created by create-story workflow — comprehensive developer guide |
| 2026-02-28 | Party mode review (SM + Architect + Dev + TEA): 2 MEDIUM (`runner.close()` teardown, explicit 4-event count in multi-turn), 1 LOW (raw-DB encryption assertion on Runner path), 1 LOW (`app_name` consistency guardrail). All 4 applied. |
| 2026-02-28 | Implementation complete — 6 integration tests, 3 test classes, 3 callback functions, 3 Runner fixtures. Added pydantic DeprecationWarning filter for upstream google-adk RunConfig issue. All quality gates pass. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- google-adk `RunConfig.save_input_blobs_as_artifacts` deprecated field triggers `DeprecationWarning` from pydantic internals; resolved by adding warning filter to `pyproject.toml` scoped to `google.adk.*`

### Completion Notes List

- Created `tests/integration/test_adk_runner.py` with 6 integration tests across 3 test classes (TestADKRunnerIntegration, TestStateDeltas, TestMultiTurnConversation)
- Implemented 3 callback functions (`echo_callback`, `stateful_callback`, `counting_callback`) to short-circuit LLM via `before_agent_callback`
- Created 3 Runner fixtures (`runner`, `stateful_runner`, `counting_runner`) with proper `await runner.close()` teardown
- Added pydantic DeprecationWarning filter to `pyproject.toml` for upstream google-adk `RunConfig` issue
- All 163 tests pass (6 new + 157 existing), 99.68% coverage, all 7 pre-commit hooks pass

### File List

| File | Action |
|------|--------|
| `tests/integration/test_adk_runner.py` | CREATE |
| `pyproject.toml` | MODIFY (added pydantic DeprecationWarning filter for google-adk Runner) |
