# Story 3.4: Published Performance Benchmarks

Status: review
Branch: feat/bench-3-4-published-benchmarks
GitHub Issue:

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer evaluating the library**,
I want **published benchmark results documenting actual overhead per operation across representative payload sizes**,
so that **I can make an informed decision about which backend to use based on real performance data**.

## Acceptance Criteria

1. **Given** both Fernet and AES-256-GCM backends are available, **when** benchmark tests are run across representative payload sizes (empty dict, 1KB, 10KB, 100KB), **then** results document actual overhead per operation: encrypt, decrypt, and full round-trip (NFR4)
2. Results are published in the documentation site as a Benchmarks page (`docs/benchmarks.md`)
3. Benchmark tests are marked with `@pytest.mark.benchmark` (already configured in `pyproject.toml`)
4. The benchmarks page includes methodology section explaining hardware-independent relative comparisons (not absolute times)
5. The page documents the performance characteristics of each backend with a comparison table
6. `docvet` pre-commit hook passes on all new documentation files

## Tasks / Subtasks

- [x] Task 1: Expand benchmark test infrastructure (AC: 1, 3)
  - [x] 1.1 Add payload generator fixtures for multiple sizes (empty dict, 1KB, 10KB, 100KB) in `tests/benchmarks/conftest.py`
  - [x] 1.2 Add AES-256-GCM backend fixture and AES-GCM-backed `encrypted_service` fixture to `tests/benchmarks/conftest.py`
  - [x] 1.3 Parameterize existing round-trip overhead test over both backends (Fernet, AES-256-GCM) and all payload sizes — **assertive** (`< 1.20x` threshold, CI warns / local fails)
  - [x] 1.4 Ensure existing single-backend overhead test behavior is preserved (backward compat)
- [x] Task 2: Create per-operation benchmark tests (AC: 1)
  - [x] 2.1 Add `test_encrypt_only` — measures raw `backend.encrypt(payload)` cost across payload sizes and backends. **Informational only — no threshold assertion.** Logs timing data for docs.
  - [x] 2.2 Add `test_decrypt_only` — pre-encrypts, then measures raw `backend.decrypt(ct)` cost. **Informational only — no threshold assertion.** Logs timing data for docs.
  - [x] 2.3 Add `test_backend_comparison` — side-by-side Fernet vs. AES-256-GCM relative overhead ratio for all operations and sizes. Logs comparison ratios for docs.
- [x] Task 3: Create documentation page (AC: 2, 4, 5)
  - [x] 3.1 Create `docs/benchmarks.md` with five sections: (1) Why Benchmarks — what NFR1 means, (2) Methodology — `time.perf_counter()`, 20 iterations, median, CI vs local, (3) Backend Comparison — table of stable overhead ratios (not raw ms), (4) How to Run — `uv run pytest tests/benchmarks/ -m benchmark -v`, (5) Interpreting Results — backend selection guidance
  - [x] 3.2 Add benchmarks page to `mkdocs.yml` nav as **top-level** entry between Roadmap and FAQ
- [x] Task 4: Validate quality gates (AC: 6)
  - [x] 4.1 Run `pre-commit run --all-files` — all hooks pass including docvet
  - [x] 4.2 Run `uv run pytest tests/benchmarks/ -m benchmark -v` — all benchmark tests pass
  - [x] 4.3 Run `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` — coverage maintained

### Cross-Cutting Test Maturity (Standing Task)

<!-- Sourced from test-review.md recommendations. The create-story workflow
     picks the next unaddressed item and assigns it here. -->

**Test Review Item**: Consider adding DontWrapMixin test coverage
**Severity**: P3 (Low)
**Location**: `tests/unit/test_encrypted_session_service.py:220-259`

The `test_wrong_key_error_not_wrapped_in_statement_error` test is excellent but could be complemented by a unit-level test in `test_exceptions.py` verifying `DontWrapMixin` is present on all three exception classes (`EncryptionError`, `DecryptionError`, `SerializationError`).

- [x] Implement the test review recommendation above
- [x] Verify new/changed test(s) pass in CI
- [x] Mark item as done in `_bmad-output/test-artifacts/test-review.md`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1    | `test_fernet_round_trip_overhead[*]`, `test_aesgcm_round_trip_overhead[*]`, `test_encrypt_only[*]`, `test_decrypt_only[*]`, `test_backend_comparison` | pass |
| 2    | `docs/benchmarks.md` exists, docvet passes | pass |
| 3    | `pytestmark = pytest.mark.benchmark` in `test_encryption_overhead.py` | pass |
| 4    | `docs/benchmarks.md` Methodology section | pass |
| 5    | `docs/benchmarks.md` Backend Comparison table | pass |
| 6    | `pre-commit run --all-files` passes (docvet included) | pass |

## Dev Notes

### Existing Benchmark Infrastructure

The project already has a working benchmark framework in `tests/benchmarks/`:

- **`test_encryption_overhead.py`** (171 lines) — Single test measuring encrypted vs. unencrypted round-trip overhead for Fernet at ~10KB payload. Uses `time.perf_counter()`, median-based comparison, CI/local mode switching.
- **`conftest.py`** (122 lines) — Provides `benchmark_state` (~10KB dict), `baseline_conn` (raw aiosqlite connection with minimal schema), `baseline_db_path`.
- **`pyproject.toml`** — `@pytest.mark.benchmark` marker defined; default addopts excludes benchmarks (`-m 'not benchmark'`).
- **Existing `encrypted_service` fixture** in `tests/conftest.py` — uses FernetBackend only.

### What Needs to Change

The existing infrastructure measures only:
- One backend (Fernet)
- One payload size (~10KB)
- One operation type (full round-trip: create + get + delete)

This story expands to:
- Two backends (Fernet + AES-256-GCM)
- Four payload sizes (empty dict, 1KB, 10KB, 100KB)
- Three operation types (encrypt-only, decrypt-only, full round-trip)

### Architecture Patterns to Follow

- **`time.perf_counter()`** for wall-clock timing — do NOT adopt `pytest-benchmark` (async incompatibility: its `benchmark` fixture expects sync callables, requiring ugly `run_until_complete()` wrappers that add measurement artifacts)
- **N_ITERATIONS = 20** with median-based comparison for all payload sizes including 100KB (established pattern, runtime is acceptable)
- **CI mode**: `os.environ.get("CI")` — emit `UserWarning` on threshold breach, don't fail
- **Local mode**: `pytest.fail()` on threshold breach for developer feedback
- **Overhead threshold**: `1.20x` (NFR1: <20% encryption overhead) — **applies to round-trip tests only**
- **Per-operation tests (encrypt-only, decrypt-only)**: **Informational only — no threshold assertion.** These measure raw backend cost for comparison, not overhead vs. baseline. Log results for docs.
- **Parameterization**: `@pytest.mark.parametrize` over backends and payload sizes
- **Constants with rationale docstrings** (pattern from Story 3.3)
- **1MB payload**: Explicitly out of scope. 100KB is 10x realistic session size — sufficient upper bound.

### Benchmark Test Design

**Two categories of benchmarks with different assertion strategies:**

**Category A — Overhead tests (assertive, `< 1.20x`):**
Round-trip overhead: encrypted service vs. raw SQL baseline. Parameterized over backends and payload sizes. This validates NFR1.

**Category B — Per-operation tests (informational, no assertion):**

*Encrypt-only:*
Measure raw `backend.encrypt(payload)` cost across backends and sizes. No baseline comparison — encrypting is always more expensive than not encrypting. Log timing data.

*Decrypt-only:*
Pre-encrypt data, then measure raw `backend.decrypt(ciphertext)` cost. Log timing data.

*Backend comparison:*
Compute Fernet-vs-AES-256-GCM ratio for each operation and size. These ratios are hardware-stable and go into the docs page.

**Payload generation:**
- Empty dict: `{}`
- 1KB: Sized dict with conversation entries
- 10KB: Existing `benchmark_state` fixture
- 100KB: Extended version with more conversation history

### Documentation Approach

The docs page presents **methodology and stable ratios**, not raw timing numbers. Readers run benchmarks on their own hardware for absolute values.

**Page structure (5 sections):**
1. **Why Benchmarks** — what NFR1 means, why overhead matters for ADK agents
2. **Methodology** — `time.perf_counter()`, 20 iterations, median, CI vs local mode, no `pytest-benchmark` (async incompatibility)
3. **Backend Comparison** — table of stable overhead ratios (Fernet vs AES-256-GCM), not raw milliseconds. Ratios are hardware-independent.
4. **How to Run** — `uv run pytest tests/benchmarks/ -m benchmark -v`, interpreting logger output
5. **Interpreting Results** — what the ratios mean, how to choose a backend based on security requirements vs. performance

### AES-256-GCM Backend Reference

- **Module**: `src/adk_secure_sessions/backends/aes_gcm.py`
- **Class**: `AesGcmBackend`
- **Key format**: Raw 256-bit key from `AESGCM.generate_key(bit_length=256)`
- **Backend ID**: `0x02`
- **Constructor**: `AesGcmBackend(key=AESGCM.generate_key(bit_length=256))`
- **Import**: `from adk_secure_sessions import AesGcmBackend` (not yet in conftest.py)

### Previous Story Intelligence (Story 3-3)

- Constants at module top with rationale docstrings (follow `N_ITERATIONS`, `_OVERHEAD_THRESHOLD` pattern)
- Factory pattern for multi-variant fixtures
- `additional_backends` parameter on `EncryptedSessionService` for multi-backend scenarios
- All pre-commit hooks pass at 98.78% coverage, 246 tests
- `EncryptedJSON` TypeDecorator handles dispatch by backend_id in the envelope header

### Git Intelligence

Recent commits (all Epic 3):
- `c971d33` feat(serialization): add multi-backend coexistence and dispatch (#144)
- `64f2a76` feat(backend): add per-key random salt key derivation to FernetBackend (#143)
- `9ea7881` feat(backend): add AES-256-GCM encryption backend (#141)

Files relevant to this story:
- `tests/benchmarks/test_encryption_overhead.py` — expand
- `tests/benchmarks/conftest.py` — expand
- `docs/benchmarks.md` — create
- `mkdocs.yml` — add nav entry

### Documentation Impact

| Page | Nature of Update | Status |
|------|-----------------|--------|
| `docs/benchmarks.md` | New page — 5-section structure: Why Benchmarks, Methodology, Backend Comparison (stable ratios), How to Run, Interpreting Results | Done |
| `mkdocs.yml` | Add `Benchmarks: benchmarks.md` as **top-level** nav entry between Roadmap and FAQ | Done |

### Peripheral Config Impact

- **`mkdocs.yml`** — Add benchmarks page to nav structure
- **No `pyproject.toml` changes** — benchmark marker already defined, no new dependencies
- **No CI/CD changes** — benchmarks excluded from default test run via addopts
- **No `.pre-commit-config.yaml` changes** — docvet already validates docs/

### Project Structure Notes

- Benchmark tests stay in `tests/benchmarks/` (established location)
- Documentation goes in `docs/benchmarks.md` (standard docs location)
- No new source modules — this story only adds tests and documentation
- Alignment with unified project structure confirmed

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 3, Story 3.4]
- [Source: _bmad-output/planning-artifacts/architecture.md - NFR1, NFR4, Benchmark Specifics]
- [Source: _bmad-output/planning-artifacts/prd.md - FR46, NFR4]
- [Source: tests/benchmarks/test_encryption_overhead.py - existing benchmark infrastructure]
- [Source: tests/benchmarks/conftest.py - existing benchmark fixtures]
- [Source: ADR-001: Protocol-Based Interfaces - EncryptionBackend protocol]
- [Source: ADR-002: Async-First Design - asyncio.to_thread requirements]
- [Source: _bmad-output/implementation-artifacts/3-3-multi-backend-coexistence-dispatch.md - previous story learnings]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- all tests pass, >=90% coverage (98.78%, 251 passed)
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
| 2026-03-08 | Story created by SM agent — ultimate context engine analysis completed |
| 2026-03-08 | Party mode consensus: assertion scope (round-trip assertive, per-op informational), cut 1MB payload, stay with perf_counter (no pytest-benchmark — async incompatibility), docs top-level nav, methodology+ratios approach |
| 2026-03-08 | Implementation complete: expanded benchmark infrastructure (4 payload sizes, 2 backends), 17 benchmark tests, docs/benchmarks.md, DontWrapMixin tests added |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

- Expanded `tests/benchmarks/conftest.py` with payload generators (empty, 1KB, 10KB, 100KB), AES-GCM backend/service fixtures, and `benchmark_payloads` fixture with size validation
- Rewrote `tests/benchmarks/test_encryption_overhead.py` with 17 benchmark tests: 8 round-trip overhead tests (4 sizes x 2 backends, assertive), 8 per-operation tests (4 sizes x encrypt/decrypt, informational), 1 backend comparison test
- Extracted `_measure_overhead` and `_assert_overhead` helpers to reduce duplication across parameterized round-trip tests
- Created `docs/benchmarks.md` with 5 sections: Why Benchmarks, Methodology, Backend Comparison (ratio table), How to Run, Interpreting Results
- Added benchmarks page to `mkdocs.yml` nav between Roadmap and FAQ
- Added 5 DontWrapMixin tests in `test_exceptions.py` (3 positive for EncryptionError/DecryptionError/SerializationError, 2 negative for SecureSessionError/ConfigurationError)
- Updated test-review.md: marked DontWrapMixin recommendation as DONE
- All pre-commit hooks pass, 251 tests, 98.78% coverage

### File List

| Action | File |
|--------|------|
| Modified | `tests/benchmarks/conftest.py` |
| Modified | `tests/benchmarks/test_encryption_overhead.py` |
| Created | `docs/benchmarks.md` |
| Modified | `mkdocs.yml` |
| Modified | `tests/unit/test_exceptions.py` |
| Modified | `_bmad-output/test-artifacts/test-review.md` |
| Modified | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Modified | `_bmad-output/implementation-artifacts/3-4-published-performance-benchmarks.md` |
