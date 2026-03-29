---
title: 'google-adk 1.28.0 compatibility — EncryptedStorageSession.get_update_marker()'
slug: 'adk-128-get-update-marker'
created: '2026-03-28'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['google-adk>=1.22.0', 'SQLAlchemy ORM models', 'pytest']
files_to_modify:
  - 'src/adk_secure_sessions/services/models.py'
  - 'tests/integration/test_adk_conformance.py'
  - 'tests/unit/test_models.py'
code_patterns:
  - 'Duck-typed StorageSession model with method forwarding'
  - 'ISO 8601 timestamp with microsecond precision'
test_patterns:
  - 'Sentinel tests for model method parity'
  - 'Integration tests for optimistic concurrency via append_event'
---

# Tech-Spec: google-adk 1.28.0 compatibility — get_update_marker()

**Created:** 2026-03-28

## Overview

### Problem Statement

`google-adk` 1.28.0 (released 2026-03-26, commit [`b8e7647`](https://github.com/google/adk-python/commit/b8e764715cb1cc7c8bc1de9aa94ca5f5271bb627), closes [google/adk-python#4751](https://github.com/google/adk-python/issues/4751)) introduces `get_update_marker()` on `StorageSession` — a string-based optimistic concurrency marker that replaces float timestamp comparison. `DatabaseSessionService.append_event()` now calls `storage_session.get_update_marker()` directly. Our `EncryptedStorageSession` does not implement this method, causing `AttributeError` at runtime. Additionally, the upstream `StorageSession.to_session()` now stamps the returned `Session` with `_storage_update_marker` (a Pydantic `PrivateAttr(default=None)` on the `Session` model) — our override of `to_session()` does not, so the improved concurrency detection path is bypassed (the old timestamp fallback still works, but sessions miss the marker-based stale check).

The upstream also has an `update_timestamp_tz` property on `StorageSession` (present since at least 1.22.0) that our `EncryptedStorageSession` has never implemented. This is a pre-existing parity gap that must be closed to enable a clean sentinel test.

### Solution

Add `get_update_marker()` to `EncryptedStorageSession` matching the upstream signature and behavior. Update `to_session()` to set `session._storage_update_marker`. Add sentinel tests that verify model method parity against ADK's `StorageSession` to catch future breakage earlier.

### Scope

**In Scope:**
- Add `get_update_marker() -> str` to `EncryptedStorageSession`
- Add `update_timestamp_tz` property to `EncryptedStorageSession` (pre-existing parity gap)
- Update `to_session()` to set `session._storage_update_marker`
- Add sentinel tests for model method parity (scoped to `StorageSession` only)
- Add unit tests for model method behavior
- Verify existing `append_event` integration tests pass with the fix

**Out of Scope:**
- Bumping the google-adk pin or lockfile (separate PR)
- CI matrix changes (separate issue)
- Changes to other model classes (`EncryptedStorageAppState`, `EncryptedStorageUserState`, `EncryptedStorageEvent`)

## Context for Development

### Codebase Patterns

- `EncryptedStorageSession` is defined inside `create_encrypted_models()` factory function (not at module level) — all changes go inside that factory
- The model duck-types ADK's `StorageSession` — it must have the same public method signatures
- `EncryptedSessionService` delegates all CRUD to `DatabaseSessionService` via inheritance — no method overrides needed; the parent calls methods on our model objects
- All datetime handling in the model uses `datetime` from stdlib with `timezone.utc` for SQLite compatibility

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/adk_secure_sessions/services/models.py` | `EncryptedStorageSession` — add `get_update_marker()`, update `to_session()` |
| `tests/integration/test_adk_conformance.py` | ADK conformance tests — add model method sentinel tests |
| `.venv/.../google/adk/sessions/schemas/v1.py` | Upstream `StorageSession.get_update_marker()` reference impl |
| `.venv/.../google/adk/sessions/database_session_service.py` | Upstream call sites in `append_event()` |

### Technical Decisions

1. **Match upstream implementation exactly** — `get_update_marker()` normalizes to UTC if timezone-aware, then formats as ISO 8601 with `timespec="microseconds"`. No deviation.
2. **Set `_storage_update_marker` in `to_session()`** — upstream declares this as a Pydantic `PrivateAttr(default=None)` on the `Session` model. `PrivateAttr` supports direct assignment and is stable Pydantic v2 API. Without it, sessions fall back to the old timestamp-based stale check; with it, they get the improved marker-based concurrency detection.
3. **Sentinel test approach** — import `StorageSession` directly via `from google.adk.sessions.schemas.v1 import StorageSession`. This is an internal module path (not `__all__`-exported), but it's stable across 1.22.0–1.28.0. Accept the coupling — if it breaks in a future version, the sentinel test itself will fail with `ImportError`, which is the correct failure mode. Scope sentinel introspection to `StorageSession` only — other model classes (`StorageEvent`, `StorageAppState`, `StorageUserState`) are explicitly out of scope.
4. **Testability split** — AC4 is split into AC4a (behavioral equivalence test against known inputs, testable against 1.26.0) and AC4b (end-to-end `append_event`, verified-on-upgrade when lockfile bumps to 1.28.0 in a separate PR). AC4a is NOT a tautology — it verifies our output matches the upstream formula for the same input.
5. **Task priority order** — T1 (critical, unblocks 1.28.0) > T4 (high, unblocks clean sentinel) > T2 (medium, enables improved concurrency) > T3 (medium, test coverage).
6. **Post-upgrade verification** — after the lockfile bump to 1.28.0 lands, diff our `get_update_marker()` against upstream's before marking AC4b as passed.

## Implementation Plan

### Tasks

#### Task 1: Add `get_update_marker()` to `EncryptedStorageSession` ✅

**File:** `src/adk_secure_sessions/services/models.py`
**Location:** Inside `EncryptedStorageSession` class (after `get_update_timestamp()`)

Add:

```python
def get_update_marker(self) -> str:
    """Return a stable revision marker for optimistic concurrency checks.

    Produces an ISO 8601 timestamp string with microsecond precision,
    matching the upstream ``StorageSession.get_update_marker()``
    contract introduced in google-adk 1.28.0.

    Returns:
        ISO 8601 formatted update time (UTC-normalized, microsecond
        precision).
    """
    update_time = self.update_time
    if update_time.tzinfo is not None:
        update_time = update_time.astimezone(timezone.utc)
    return update_time.isoformat(timespec="microseconds")
```

#### Task 2: Update `to_session()` to set `_storage_update_marker` ✅

**File:** `src/adk_secure_sessions/services/models.py`
**Location:** Inside `EncryptedStorageSession.to_session()`, after constructing the `Session` object

**Minimal edit** — add one line after the `Session(...)` constructor and before the `return`. Do NOT replace the full method. Preserve the existing docstring and update it to mention the marker:

Add after `session = Session(...)`:
```python
    session._storage_update_marker = self.get_update_marker()
```

Update the docstring `Returns:` section to:
```
Returns:
    ADK Session object with ``_storage_update_marker`` set for
    optimistic concurrency control.
```

#### Task 3: Add tests ✅

Tests are split across two files following project conventions:

**Unit tests** — `tests/unit/test_models.py` (new file)

Pure model-method tests that construct `EncryptedStorageSession` directly without touching a database:

```python
class TestGetUpdateMarker:
    """Unit tests for EncryptedStorageSession.get_update_marker()."""

    def test_naive_datetime_returns_iso_string(self, ...):
        """Verify get_update_marker() with naive datetime (SQLite primary path)."""
        # Given a known naive datetime, output must match the upstream formula:
        # dt.isoformat(timespec="microseconds")
        ...

    def test_tz_aware_datetime_normalizes_to_utc(self, ...):
        """Verify get_update_marker() normalizes tz-aware datetime to UTC."""
        ...

    def test_behavioral_equivalence_with_known_input(self, ...):
        """AC4a: Output matches the upstream formula for a known input."""
        dt = datetime(2026, 3, 28, 12, 0, 0, 123456)
        # model.update_time = dt
        assert model.get_update_marker() == dt.isoformat(timespec="microseconds")
        ...

class TestUpdateTimestampTz:
    """Unit tests for EncryptedStorageSession.update_timestamp_tz property."""

    def test_returns_float_timestamp(self, ...):
        """Verify update_timestamp_tz returns POSIX float."""
        ...

class TestToSessionMarker:
    """Unit tests for _storage_update_marker stamping in to_session()."""

    def test_to_session_sets_storage_update_marker(self, ...):
        """Verify to_session() sets _storage_update_marker on returned Session."""
        ...
```

**Integration tests** — `tests/integration/test_adk_conformance.py` (existing file)

Sentinel tests and round-trip tests that require the service or upstream imports:

```python
class TestStorageSessionMethodParity:
    """Sentinel tests: EncryptedStorageSession duck-types ADK's StorageSession."""

    def test_create_session_roundtrip_sets_storage_update_marker(
        self, encrypted_service, ...
    ):
        """AC5: _storage_update_marker is set after create_session() round-trip."""
        session = await encrypted_service.create_session(app_name=..., user_id=...)
        assert hasattr(session, '_storage_update_marker')
        assert session._storage_update_marker is not None
        ...

    def test_all_public_methods_present(self, ...):
        """AC6: Sentinel — all public methods on ADK StorageSession exist on EncryptedStorageSession."""
        from google.adk.sessions.schemas.v1 import StorageSession
        # Introspect StorageSession for public methods (not starting with _)
        # Assert each exists and is callable on EncryptedStorageSession
        # Scoped to StorageSession ONLY — other model classes are out of scope
        ...
```

#### Task 4: Add `update_timestamp_tz` property to `EncryptedStorageSession` ✅

**File:** `src/adk_secure_sessions/services/models.py`
**Location:** Inside `EncryptedStorageSession` class (after `get_update_timestamp()`, before `get_update_marker()`)
**Priority:** High — unblocks clean sentinel test (Task 3)

Add the property that upstream `StorageSession` has had since at least 1.22.0:

```python
@property
def update_timestamp_tz(self) -> float:
    """The update time as a POSIX timestamp (UTC, non-SQLite path).

    Compatibility alias matching upstream ``StorageSession``.
    Equivalent to ``get_update_timestamp(is_sqlite=False)``.
    """
    return self.get_update_timestamp(is_sqlite=False)
```

### Acceptance Criteria

**AC1: `get_update_marker()` with naive datetime returns correct format**
- **Given** an `EncryptedStorageSession` with a naive `update_time` (no tzinfo — the SQLite primary path)
- **When** `get_update_marker()` is called
- **Then** it returns an ISO 8601 string with microsecond precision matching the `update_time`

**AC2: `get_update_marker()` with timezone-aware datetime normalizes to UTC**
- **Given** an `EncryptedStorageSession` with a timezone-aware `update_time` (e.g., UTC+5)
- **When** `get_update_marker()` is called
- **Then** the returned string represents the time converted to UTC

**AC3: `to_session()` sets `_storage_update_marker`**
- **Given** an `EncryptedStorageSession`
- **When** `to_session()` is called
- **Then** the returned `Session` has `_storage_update_marker` set to the result of `get_update_marker()`

**AC4a: `get_update_marker()` produces behaviorally equivalent output (testable now, against 1.26.0)**
- **Given** an `EncryptedStorageSession` with a known `update_time` datetime
- **When** `get_update_marker()` is called
- **Then** the output matches `update_time.isoformat(timespec="microseconds")` exactly (not just "a string is returned" — behavioral equivalence with the upstream formula)

**AC4b: `append_event()` works end-to-end (verified-on-upgrade, requires google-adk >= 1.28.0)**
- **Given** an `EncryptedSessionService` with google-adk >= 1.28.0 installed
- **When** `append_event()` is called on a session
- **Then** no `AttributeError` is raised for `get_update_marker`
- **Note:** This AC is validated by the CI `latest` matrix variant after the lockfile is bumped in a separate PR. Not testable against 1.26.0.

**AC5: `_storage_update_marker` set after full service round-trip**
- **Given** an `EncryptedSessionService`
- **When** `create_session()` is called and the session is retrieved via `get_session()`
- **Then** the returned `Session` has `_storage_update_marker` set (not None)

**AC6: Sentinel test catches missing public methods**
- **Given** ADK's `StorageSession` (from `google.adk.sessions.schemas.v1`) has public methods
- **When** the sentinel test runs
- **Then** it verifies `EncryptedStorageSession` has all matching public methods (duck-type parity)
- **Note:** Sentinel scope is `StorageSession` only — other model classes are out of scope

**AC7: `update_timestamp_tz` property exists and returns correct value**
- **Given** an `EncryptedStorageSession` with a known `update_time`
- **When** `update_timestamp_tz` is accessed
- **Then** it returns the same float as `get_update_timestamp(is_sqlite=False)`

## Additional Context

### Dependencies

- `google-adk >= 1.22.0` (existing pin; the fix is forward-compatible — `get_update_marker()` is added to our model regardless of installed ADK version)
- No new runtime dependencies needed

### Testing Strategy

- **Unit tests** (`tests/unit/test_models.py`): Construct `EncryptedStorageSession` directly (via factory), test `get_update_marker()` with naive datetime (SQLite primary path) and tz-aware datetime (UTC normalization). Behavioral equivalence test against known inputs. Test `update_timestamp_tz` property. Test `to_session()` stamps `_storage_update_marker`.
- **Integration tests** (`tests/integration/test_adk_conformance.py`): Full round-trip through `EncryptedSessionService` — `create_session()`, verify `_storage_update_marker` is set on the returned Session. Sentinel test introspecting `StorageSession` from `google.adk.sessions.schemas.v1` for duck-type parity (scoped to `StorageSession` only).
- **Verified-on-upgrade (AC4b)**: Full `append_event()` end-to-end test requires google-adk >= 1.28.0. Validated by the CI `latest` matrix variant after the lockfile bump lands in a separate PR. Not testable in this PR against 1.26.0. After upgrade, diff our impl against upstream before marking as passed.

### Notes

- `session._storage_update_marker` is declared as `PrivateAttr(default=None)` on ADK's `Session` Pydantic model (stable Pydantic v2 API, not a dynamic `setattr` hack). It does not appear in `model_dump()`, JSON schema, or serialization — no impact on the encryption/serialization layer.
- The `get_update_marker()` method was added as a replacement for comparing `last_update_time` floats, which suffered from precision loss across DB backends. The ISO string with microsecond precision gives lossless comparison. Upstream commit: [`b8e7647`](https://github.com/google/adk-python/commit/b8e764715cb1cc7c8bc1de9aa94ca5f5271bb627).
- When `_storage_update_marker` is `None` (e.g., sessions created before 1.28.0), `append_event()` falls back to the old timestamp + event-ID check. So Task 2 is not strictly required for correctness — it enables the improved concurrency path.
- Future ADK versions may add more methods to `StorageSession` — the sentinel test (Task 3) is designed to catch these automatically. Scoped to `StorageSession` only.
- **Post-upgrade verification:** After bumping the lockfile to 1.28.0, diff our `get_update_marker()` implementation against upstream's before marking AC4b as passed.
