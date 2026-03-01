---
project_name: 'adk-secure-sessions'
user_name: 'Alberto-Codes'
date: '2026-02-28'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 91
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Core Runtime
- **Python** `>=3.12,<3.13` — single-version band; use 3.12 syntax only
- **google-adk** `>=1.22.0` — upstream integration surface; extends `BaseSessionService`, uses `Session` and `Event` models. Never override ADK base methods without checking upstream signatures. CI tests against `1.22.0` and `latest` — maintain compat across that range.
- **aiosqlite** `>=0.19.0` — async SQLite driver; all DB access uses raw parametrized SQL (`await conn.execute("...", (params,))`), NOT SQLAlchemy ORM patterns despite SQLAlchemy being in deps
- **SQLAlchemy** `>=2.0.0` — present in deps for async engine support, not for ORM usage
- **cryptography** `>=44.0.0` — Fernet symmetric encryption

### Build & Tooling
- **uv** — package manager, build backend (`uv_build`), task runner. ALWAYS use `uv run` (e.g., `uv run pytest`, `uv run ruff`), never bare `python`, `pip`, or `pytest`
- **ruff** `>=0.13.0` — linter + formatter (line-length 88, Google docstring convention)
- **ty** `>=0.0.1a20` — type checker (runs on `src/` only)
- **pytest** `>=8.4.2` — `asyncio_mode = "auto"` (do NOT add `@pytest.mark.asyncio` — it's redundant)
- **Enforced quality gates:** 90% test coverage (`--cov-fail-under=90`), 95% docstring coverage (interrogate)

### CI Matrix
- Python 3.12 + google-adk version matrix (`1.22.0`, `latest`)
- Pipeline: lint → format check → type check → tests with coverage

## Critical Implementation Rules

### Language-Specific Rules (Python)

- **`from __future__ import annotations`** — required as first import in every module; enables PEP 604 `X | Y` unions and is required for `@runtime_checkable` Protocol `isinstance()` checks to work correctly
- **Type hints mandatory** on all function signatures; use modern syntax (`dict[str, Any]`, `str | None`) not `typing.Optional` or `typing.Dict`
- **All public APIs are `async def`** — no synchronous public functions
- **`asyncio.to_thread()`** — any call into the `cryptography` library (Fernet encrypt/decrypt) MUST go through `asyncio.to_thread()` to avoid blocking the event loop
- **Absolute imports only** — `from adk_secure_sessions.protocols import EncryptionBackend`, never relative (`from .protocols import ...`)
- **`__all__` in every `__init__.py`** — alphabetically sorted, explicitly listing every public symbol. This defines the public API surface.
- **F-strings** for all string interpolation; no `.format()` or `%` formatting
- **None checks** use `is` / `is not`, never `==` / `!=`
- **No mutable defaults** — use `def func(x: list[str] | None = None)` with `x = x or []` inside
- **Exception messages** assigned to `msg` variable before `raise`: `msg = "..."; raise SomeError(msg)` — enforced by ruff `TRY003`
- **Exception chaining** — always use `from exc` (or `from None` to suppress) when re-raising
- **Never expose sensitive data** (keys, plaintext, ciphertext) in error messages
- **Constants** — module-level, `ALL_CAPS_WITH_UNDERSCORES`, with type annotation and docstring
- **PEP 544 Protocols only** — use `@runtime_checkable` `Protocol` for contracts; NEVER use `ABC` or `abstractmethod`
- **`TYPE_CHECKING` guard** — use `if TYPE_CHECKING:` block for imports only needed by type checkers
- **Docstring Examples** — use fenced code blocks (triple backticks), NOT `::` directive; griffe/mkdocstrings require fenced blocks for the docs site

### Framework-Specific Rules (Google ADK + Encryption)

#### ADK Integration
- **Extend `BaseSessionService`** — `EncryptedSessionService` inherits from ADK's `BaseSessionService`; override only the documented public methods (`create_session`, `get_session`, `list_sessions`, `delete_session`)
- **Session/Event models are ADK's** — never redefine `Session` or `Event` classes; import from `google.adk.sessions`
- **State is a `dict[str, Any]`** — session state is a plain dict that must be JSON-serializable; no custom objects in state

#### Encryption Architecture
- **Data flow is inviolable** — write path: `state dict → JSON serialize → encrypt → store`; read path: `fetch → decrypt → JSON deserialize → state dict`. Every path to/from the database MUST go through the serialization layer. An unencrypted data path is a security defect, not a TODO.
- **`EncryptionBackend` Protocol** — all backends conform to `protocols.EncryptionBackend` (two methods: `encrypt(bytes) -> bytes`, `decrypt(bytes) -> bytes`)
- **Envelope format** — serialized data is `[version_byte][backend_id_byte][ciphertext]`; this is a binary wire protocol. The header exists for key rotation and audit — never strip or shortcut it.
- **Backend registry** — `BACKEND_FERNET = 0x01`; new backends get the next integer ID and must be added to `BACKEND_REGISTRY`
- **Serialization functions are module-level** — `encrypt_session()`, `decrypt_session()`, `encrypt_json()`, `decrypt_json()` are stateless functions, not methods

#### Database Layer
- **Own schema, independent of ADK** — we manage our own SQLite tables (`sessions`, `events`), not ADK's internal schema
- **`PRAGMA foreign_keys = ON`** — always enabled at connection init
- **Parametrized queries only** — `await conn.execute("... WHERE id = ?", (value,))`, never f-string SQL
- **Lazy connection** — DB connection created on first use via `_get_connection()` → `_init_db()`. Always call `await self._get_connection()`, NEVER access `self._connection` directly.
- **Async context manager** — `EncryptedSessionService` supports `async with` for connection lifecycle. `close()` must be called to release resources. Test fixtures must `yield svc` then `await svc.close()`.

#### Testing Boundaries
- **Unit tests** — mock the `EncryptionBackend` to isolate persistence logic, OR mock the DB to isolate encryption logic. Never mock both or neither.
- **Integration tests** — use real `FernetBackend` + real SQLite (via `tmp_path`). No mocks.

### Testing Rules

#### Structure & Organization
- **Test file naming** — `test_<module>.py` mirroring source module (e.g., `test_serialization.py` tests `serialization.py`)
- **Test classes** — `class Test<Feature>:` groups related tests; no `__init__` method
- **Test method naming** — `test_<what>_<condition>_<expected_result>` (e.g., `test_decrypt_with_wrong_key_raises_decryption_error`)
- **Module-level marker** — every test file starts with `pytestmark = pytest.mark.unit` (or `integration`)
- **Section headers** — group tests by user story with `# --- US1: Description ---` comments
- **Task IDs in docstrings** — `"""T005: Encrypt then decrypt returns original plaintext."""`

#### Fixtures
- **Function scope** (default) for maximum isolation — every test gets a fresh instance
- **Async generators** for resources needing cleanup: `async def service() -> AsyncGenerator[...]: yield svc; await svc.close()`
- **`tmp_path`** for any test needing filesystem (SQLite databases, temp files)
- **Factory fixtures** for parametrizable test data: `def make_backend(): def _make(...): return ...; return _make`

#### Assertions & Mocking
- **Plain `assert`** — pytest introspection handles the rest; no `self.assertEqual`
- **One assertion concept per test** — test one behavior, not multiple
- **Exception testing** — `with pytest.raises(SomeError, match="expected message"):`
- **MUST use `pytest-mock`** (`mocker` fixture) — NEVER `unittest.mock`, `Mock()`, or `patch()` directly
- **`mocker.AsyncMock()`** for async methods
- **Patch at usage site** — `mocker.patch("adk_secure_sessions.services.encrypted_session.some_func")`, not where defined

#### Parametrization
- **`@pytest.mark.parametrize`** with `ids=` for readable test output
- **Tuple format** — `("input, expected", [(val1, val2)], ids=["case_name"])`

### Code Quality & Style Rules

#### Formatting (ruff-enforced)
- **Line length** — 88 chars (ruff default); max 100 for pycodestyle
- **Quote style** — double quotes everywhere
- **Indentation** — 4 spaces, no tabs
- **Import sorting** — ruff isort with `known-first-party = ["adk_secure_sessions"]`
- **Docstring code formatting** — `docstring-code-format = true` in ruff
- **`assert` is test-only** — ruff `S101` is ignored in `tests/*.py` but flags production code. Use explicit `if/raise` in production, never bare `assert`.

#### Docstring Requirements (Google-style)
- **One-line summary** — max 80 chars, ends with period
- **Section order** — summary → description → Args → Returns → Raises → Yields → Examples → See Also
- **Args format** — `name: Description.` (no type in docstring, type hints handle that)
- **Module docstrings** — three-part structure: overview paragraph, `Typical usage::` block (uses `::` directive), `See Also:` section with cross-reference links
- **Function/class docstrings** — `Examples:` section uses fenced triple-backtick code blocks (NOT `::` directive). Do NOT mix conventions between module and function/class docstrings.
- **Examples must be runnable code** — griffe validates them; no pseudocode
- **Cross-references** — markdown links: `` [`module`][full.path] ``
- **`@property` docstrings** — "The X" not "Returns the X"
- **95% coverage** — enforced by interrogate; `__init__` and magic methods excluded

#### File & Module Structure
- **`src/` layout** — all source code lives under `src/adk_secure_sessions/`. Never add source code outside `src/`.
- **Module docstring** — every `.py` file starts with a module-level docstring (overview, typical usage, See Also)
- **snake_case** for all file names, function names, variable names
- **PascalCase** for class names only
- **`__init__.py`** — serves as public API surface with `__all__`; re-exports all public symbols. Subpackage `__init__.py` files must have docstrings (not empty files).
- **Single responsibility** — one module = one concept (protocols, exceptions, serialization, etc.)

#### Quality Pipeline
- **Full pipeline:** `pre-commit run --all-files` — runs 7 hooks: yamllint, actionlint, ruff-check, ruff-format, ty check (src/ only), pytest, docvet
- **Pre-commit hooks run automatically on each commit** — no manual step needed before pushing

### Development Workflow Rules

#### Git & Branching
- **Base branch** — `main`; all PRs target `main`
- **Branch naming** — `type/description` format matching conventional commit types (e.g., `feat/add-key-rotation`, `fix/connection-leak`)
- **Conventional commits** — `type(scope): description`
  - Types: `feat | fix | docs | refactor | test | chore | perf`
  - Scope: a codebase noun (e.g., `serialization`, `ci`), NOT issue/story numbers
  - Breaking changes: add `!` after scope (e.g., `feat(session)!: change API`)
  - Commits drive **release-please** changelog generation — malformed commits break the release pipeline
- **No `Co-Authored-By`** — never add co-author trailers to commits or PRs
- **BMAD story IDs** — go in branch names only; never use `#N` syntax in commits (GitHub auto-links `#N` to issues)
- **`Closes #N`** — must reference real GitHub issues only; never fabricate issue numbers

#### Pull Requests
- **Always draft** — use `gh pr create --draft`; ready PRs trigger automated review
- **Follow PR template** — read `.github/PULL_REQUEST_TEMPLATE.md`; remove HTML comments, keep visible content
- **Diff before PR** — always run `git diff main..HEAD` and `git log --oneline main..HEAD` to understand full scope
- **Push before PR** — `git push -u origin <branch>` before `gh pr create`
- **Squash and merge** — `--subject` = PR title, `--body` = only content above the `---` separator (Why paragraph + What changed bullets). Never include the PR Review section (checklist, review focus, related) in the commit body.

#### GitHub Issues
- **Use issue templates** — bug report, feature request, tech debt, story, retro action (`.github/ISSUE_TEMPLATE/`). Never create blank issues.

#### CI Pipeline
- Triggered on push to `main` and all PRs to `main`
- Must pass: lint → format check → type check (`src/` only) → tests (90% coverage)
- `ty check` runs on `src/` only — type errors in tests won't fail CI (intentional)
- google-adk version matrix ensures backward compatibility
- **Pre-commit runs on every commit** — hooks enforce lint, format, types, tests, and docvet before code reaches the remote

### Critical Don't-Miss Rules

#### Anti-Patterns to Avoid
- **Never use SQLAlchemy ORM** — despite being in deps, all DB access is raw parametrized SQL via aiosqlite
- **Never use `unittest.mock`** — always `pytest-mock` (`mocker` fixture); this includes `Mock()`, `MagicMock()`, `patch()`
- **Never use `ABC`/`abstractmethod`** — use PEP 544 `Protocol` with `@runtime_checkable`
- **Never use relative imports** — always absolute: `from adk_secure_sessions.x import Y`
- **Never call `cryptography` functions directly** in async code — wrap in `asyncio.to_thread()`
- **Never access `self._connection` directly** — always `await self._get_connection()`

#### Security Rules
- **Error messages must never contain sensitive data** — no keys, passphrases, plaintext, or ciphertext in exception messages. Tests verify this.
- **Every database path must encrypt/decrypt** — an unencrypted data path is a security defect
- **Parametrized SQL only** — never interpolate values into SQL strings
- **Envelope header is mandatory** — never strip version byte or backend ID from serialized data

#### Edge Cases Agents Must Handle
- **Empty bytes round-trip** — `encrypt(b"")` followed by `decrypt()` must return `b""`
- **Empty dict state** — `encrypt_session({})` must produce valid envelope
- **Wrong key decryption** — must raise `DecryptionError`, not a generic exception
- **Connection lifecycle** — `close()` on an already-closed or never-opened service must not raise
- **Concurrent access** — SQLite connections are single-writer; don't assume concurrent writes work

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-28
