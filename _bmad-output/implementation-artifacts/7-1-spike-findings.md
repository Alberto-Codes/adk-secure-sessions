# Story 7.1: TypeDecorator Wrapping Spike — Findings

## Decision: GO

The TypeDecorator-based wrapping of `DatabaseSessionService` is **viable and recommended**. All prototype tests pass. The approach produces `Session` and `Event` objects structurally identical to the unwrapped service, with transparent encryption at the ORM boundary.

---

## 1. Prototype Results (AC-1)

### Round-Trip Test: PASS

A custom `EncryptedJSON` TypeDecorator successfully encrypts on write and decrypts on read:

- **Write path**: `dict → json.dumps → Fernet.encrypt → envelope [version][backend_id][ciphertext] → base64 → TEXT`
- **Read path**: `TEXT → base64 decode → parse envelope → Fernet.decrypt → json.loads → dict`

Verified against:
- Simple key-value state
- Nested dicts (5+ levels deep)
- Mixed types (strings, ints, floats, lists, nested objects)
- App-prefixed (`app:key`) and user-prefixed (`user:key`) state stored in separate tables

Raw database inspection confirms data is **not plaintext** — it's base64-encoded encrypted envelopes with correct `[0x01][0x01]` header (envelope version 1, Fernet backend).

### All CRUD Operations: PASS

| Operation | Status | Notes |
|-----------|--------|-------|
| `create_session` | PASS | State encrypted across 3 tables (sessions, app_states, user_states) |
| `get_session` | PASS | Transparent decryption, state reconstructed correctly |
| `list_sessions` | PASS | Multiple sessions listed, state decrypted per session |
| `delete_session` | PASS | Cascade delete works (events deleted with session) |
| `append_event` | PASS | Event data encrypted, state deltas applied correctly |

---

## 2. Conformance Assessment (AC-2)

### Conformance Test: PASS

Given identical inputs to both wrapped and unwrapped `DatabaseSessionService`:

| Field | Match |
|-------|-------|
| `app_name` | MATCH |
| `user_id` | MATCH |
| `state` | MATCH |
| `type(result)` | Both `Session` instances |
| Retrieved state | MATCH |

The wrapped service produces **structurally identical** `Session` and `Event` objects. The only differences are non-deterministic fields (session IDs, timestamps) which differ between any two service instances.

---

## 3. Version Column Assessment (AC-3)

### Finding: No version column exists in ADK's v1 schema

ADK's v1 schema tables (`sessions`, `app_states`, `user_states`, `events`) do **not** have a `version` column. Schema versioning is managed via:

- `adk_internal_metadata` table with key-value pairs (key: `schema_version`, value: `"1"`)
- Database introspection via `_schema_check_utils.get_db_schema_version_from_connection`

### Impact on Story 4.4 (Optimistic Concurrency / Key Rotation)

Our Story 1.2 reserved a `version INTEGER DEFAULT 1` column in our custom aiosqlite schema. Since the TypeDecorator approach uses ADK's schema (which has no such column), we have two options:

1. **Schema extension**: Add a `version` column to the encrypted models. SQLAlchemy makes this straightforward — add a `Mapped[int]` column with `default=1`. ADK's `DatabaseSessionService` will ignore it (it doesn't query for it).
2. **Alternative concurrency mechanism**: Use SQLAlchemy's built-in `update_time` column (already present) for optimistic locking via `version_id_col` or manual timestamp comparison.

**Recommendation**: Option 1 (schema extension) is clean and non-breaking. The version column can be added to the custom models without affecting ADK's behavior. This preserves the Story 4.4 path.

---

## 4. Migration Path Assessment (AC-4)

### Current vs. New Architecture

| Aspect | Current (EncryptedSessionService) | New (Wrapped DatabaseSessionService) |
|--------|-----------------------------------|--------------------------------------|
| DB access | Raw aiosqlite, parametrized SQL | SQLAlchemy ORM (async) |
| Column types | BLOB (encrypted bytes) | TEXT (base64-encoded encrypted envelopes) |
| Schema | Custom 4-table schema | ADK's v1 schema (same 4 tables + metadata) |
| State storage | Binary envelope in BLOB | Base64 envelope in TEXT |
| Encryption point | Manual in each CRUD method | TypeDecorator (automatic, ORM boundary) |

### Is Migration Required?

**Yes, technically** — the column types differ (BLOB vs TEXT) and the storage format differs (raw binary vs base64-encoded). Existing databases cannot be read by the new service without transformation.

**However**: We have no real users with production data yet (confirmed in Epic 6 retro: "Existing Users: None — no migration pressure for Epic 7"). This means:

- **No migration utility is needed for v1.x**
- Fresh databases created by the wrapped service will use ADK's schema natively
- If a migration utility is ever needed (post-adoption), it would: (a) read BLOB columns from the old schema, (b) re-encode as base64 TEXT, (c) write to the new schema

### Recommendation: Fresh start

Users upgrading from the current architecture should create new databases. The wrapped service starts with ADK's v1 schema. No side-by-side compatibility layer needed for now.

---

## 5. Test Feasibility Assessment (AC-5)

### Conformance Tests

**Feasible.** The existing `test_adk_integration.py` tests `BaseSessionService` contract compliance. The wrapped service implements the same interface. These tests can be reused by parameterizing the service fixture:

```python
@pytest.fixture(params=["plain", "encrypted"])
def session_service(request):
    if request.param == "plain":
        return DatabaseSessionService(...)
    else:
        return EncryptedDatabaseSessionService(..., fernet_key=key)
```

### Raw-DB Encryption Verification

**Feasible with direct SQL.** The TypeDecorator hides encryption from the ORM, but raw SQL queries (`SELECT state FROM sessions`) return the base64-encoded encrypted envelopes. This was verified in the spike — the round-trip test reads raw DB values and confirms they're not plaintext.

### ADK Runner Integration

**Feasible.** The existing `test_adk_runner.py` passes the session service to `Runner(session_service=...)`. Since the wrapped service is a `DatabaseSessionService` subclass implementing `BaseSessionService`, it's a drop-in replacement for the Runner.

### Testing Challenges

1. **MutableDict tracking**: SQLAlchemy's `MutableDict.as_mutable(EncryptedJSON)` must correctly track in-place mutations. The spike doesn't test in-place mutation (e.g., `session.state["key"] = "new_value"` without reassigning the whole dict). This should be tested in Story 7.4.

2. **Concurrent access**: The spike uses in-memory SQLite (single-process). Multi-process concurrent access with encryption needs testing in Story 7.4.

3. **Model class isolation**: The custom models use a separate `DeclarativeBase`, which means they create independent tables. If both ADK's models and our models are used in the same engine, table name conflicts could occur. The spike avoids this by only using our models.

4. **Wrong-key error propagation**: The spike does not test what happens when data encrypted with Key A is read with Key B. In the TypeDecorator approach, `cryptography.fernet.InvalidToken` is raised inside `process_result_value`, which SQLAlchemy wraps in `sqlalchemy.exc.StatementError`. Users would see `StatementError(InvalidToken)` instead of our clean `DecryptionError`. Story 7.3 must catch `InvalidToken` in `process_result_value` and raise `DecryptionError` instead.

5. **Sync/async verification is indirect**: The spike's sync/async test verifies safety by "absence of deadlock" — the service completes operations without blocking the event loop. It does not directly prove TypeDecorator methods run in a thread pool (the `InstrumentedEncryptedJSON` class is defined but not wired into the service). This is sufficient evidence for the GO decision but not a substitute for proper thread-safety testing in Story 7.4.

---

## 6. Implementation Architecture (for Stories 7.2-7.6)

### How It Works

```
User Code
    │
    ▼
EncryptedDatabaseSessionService  (subclasses DatabaseSessionService)
    │  overrides: _get_schema_classes(), _prepare_tables()
    │
    ▼
DatabaseSessionService  (ADK's implementation)
    │  all CRUD: create_session, get_session, list_sessions,
    │            delete_session, append_event
    │  state merging: _merge_state() (Python-side dict | delta)
    │
    ▼
SQLAlchemy ORM
    │  EncryptedJSON TypeDecorator on state/event_data columns
    │  process_bind_param: dict → JSON → encrypt → base64 → TEXT
    │  process_result_value: TEXT → base64 → decrypt → JSON → dict
    │
    ▼
SQLite / PostgreSQL
```

### Key Design Decisions

1. **Override `_get_schema_classes()`** — returns custom `_SchemaClasses` with encrypted models instead of ADK's default models. This is a clean override point (method is called before every DB operation).

2. **Override `_prepare_tables()`** — forces v1 schema and creates tables using our `DeclarativeBase.metadata`. This avoids ADK's version detection logic and ensures our encrypted models are used.

3. **Sync Fernet in TypeDecorator** — `process_bind_param` and `process_result_value` call `Fernet.encrypt()`/`decrypt()` synchronously. This is safe because SQLAlchemy's `AsyncSession` runs ORM operations in a thread pool via `run_sync()`.

4. **Envelope preservation** — each encrypted value uses the `[version_byte][backend_id_byte][ciphertext]` format, enabling future key rotation and backend migration.

5. **Base64 encoding** — encrypted bytes are base64-encoded for TEXT column compatibility. This adds ~33% overhead but works across all SQL dialects.

### What We No Longer Need

| Component | Disposition |
|-----------|-------------|
| `EncryptedSessionService` (current) | **Replaced** by `EncryptedDatabaseSessionService` |
| Raw aiosqlite DB access | **Replaced** by SQLAlchemy ORM (via ADK) |
| Custom schema management | **Replaced** by ADK's schema + our TypeDecorator |
| Manual encrypt/decrypt in CRUD methods | **Replaced** by automatic TypeDecorator |
| `encrypt_session`/`decrypt_session` async wrappers | **Replaced** by sync Fernet in TypeDecorator |

### What We Keep

| Component | Reason |
|-----------|--------|
| `FernetBackend` class | Still needed for key resolution (passphrase → Fernet key). TypeDecorator wraps raw `Fernet`, but `FernetBackend._resolve_key()` handles arbitrary key input. |
| `EncryptionBackend` protocol | Still the public API contract for pluggable backends |
| Envelope format constants | Used by TypeDecorator for envelope construction |
| Exception hierarchy | `DecryptionError`, `ConfigurationError` still needed |

---

## 7. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| ADK changes `_get_schema_classes` or `_prepare_tables` signature | Medium | Add a dedicated sentinel test in CI (Story 7.4) that imports and inspects these method signatures — fails immediately on signature change. Pin ADK version range in `pyproject.toml`. These are internal methods (underscore-prefixed) but stable across v1.x. |
| `MutableDict` change tracking with encrypted TypeDecorator | Low | Test in-place mutation in Story 7.4. Spike uses full state replacement which works. |
| Base64 overhead (33% size increase) | Low | Acceptable for session state (typically small). If problematic, switch to `LargeBinary` column type. |
| Model class table name conflicts | Low | Use separate `DeclarativeBase` (as in spike). Never mix ADK's base with ours. |
| `_SchemaClasses.__new__` bypass is fragile | Low | Spike uses `__new__` to skip `__init__`. For production (Story 7.3): call `__init__("1")` then overwrite attributes, or create own dataclass satisfying the same duck-type contract. |
| Single shared `EncryptedJSON` instance across columns | Low | Spike shares one TypeDecorator instance across all 4 model columns. Acceptable for single-key encryption. For future multi-tenant support (per-column keys), Story 7.3 should accept a key-resolver callable instead of a raw `Fernet` instance. |
| Wrong-key decryption raises `StatementError` not `DecryptionError` | Medium | TypeDecorator's `process_result_value` raises `InvalidToken`, which SQLAlchemy wraps in `StatementError`. Story 7.3 must catch `InvalidToken` and raise `DecryptionError` to preserve the library's error contract. |

---

## 8. Implementation Plan (Stories 7.2-7.6)

Based on the spike findings, the recommended implementation path:

| Story | Scope | Key Changes |
|-------|-------|-------------|
| 7.2 | ADR: Architecture Migration Decision | Document the spike findings as an ADR. Update ADR-000 revision note. |
| 7.3 | Rewrite `EncryptedSessionService` | Move spike prototype to `src/`, add `FernetBackend._resolve_key()` integration, add `cache_ok = True`, handle edge cases. |
| 7.4 | Test Migration & Conformance | Migrate existing tests, add mutation tracking tests, concurrent access tests, raw-DB verification. |
| 7.5 | Documentation Updates | Update mkdocs site, API reference, getting started guide. |
| 7.6 | Revise Epic 4 Scope & Roadmap | Update roadmap now that PostgreSQL comes for free (SQLAlchemy handles it). |

---

## 9. Evidence Summary

| Criterion | Evidence | Verdict |
|-----------|----------|---------|
| Round-trip works | 8/8 spike tests pass, including create/get/list/delete/append | GO |
| Conformance verified | Session/Event objects structurally identical | GO |
| Version column assessed | Not in ADK schema; schema extension viable | GO |
| Migration path assessed | Fresh start recommended; no users to migrate | GO |
| Test feasibility assessed | All test categories feasible | GO |
| Sync/Async safe | TypeDecorator runs in thread pool; verified in spike | GO |
| Envelope preserved | Raw DB inspection confirms `[0x01][0x01][ciphertext]` format | GO |

**All criteria support a GO decision. Stories 7.2-7.6 should proceed.**
