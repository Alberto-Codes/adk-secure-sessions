---
paths:
  - "tests/**/*.py"
  - "**/test_*.py"
  - "**/conftest.py"
---

# Pytest Best Practices

## Test File and Function Naming

### File Naming
- MUST use `test_*.py` pattern for pytest discovery
- Place test files in `tests/` directory at project root
- Mirror application structure: `src/adk_secure_sessions/protocols.py` → `tests/unit/test_protocols.py`

### Test Function Naming
- MUST prefix with `test_`
- Use pattern: `test_<what>_<condition>_<expected_result>`
- Examples:
  - `test_encrypt_with_valid_key_returns_ciphertext()`
  - `test_decrypt_with_wrong_key_raises_decryption_error()`
  - `test_isinstance_check_with_missing_method_returns_false()`

### Test Class Naming
- MUST prefix with `Test` (capital T)
- No `__init__` method in test classes
- Use classes to group related tests for a specific component

```python
class TestEncryptionBackendProtocol:
    def test_conforming_class_passes_isinstance(self):
        pass

    def test_missing_method_fails_isinstance(self):
        pass
```

## Test Organization

### Project Structure
```
tests/
├── unit/
│   ├── test_protocols.py
│   ├── test_backends.py
│   └── test_serialization.py
├── integration/
│   └── test_session_roundtrip.py
├── conftest.py
└── pytest.ini
```

### Testing Pyramid
- **MOST tests**: Unit tests (fast, isolated)
- **FEWER tests**: Integration tests (component interactions)
- **LEAST tests**: End-to-end tests (full workflows)

### Principles
- Each test verifies ONE specific aspect
- Tests MUST be independent — no execution order dependencies
- Tests MUST be fast, deterministic, and readable

## Fixtures

### Definition
```python
import pytest

@pytest.fixture
def fernet_backend():
    return FernetBackend(key=Fernet.generate_key())

@pytest.fixture
def database_session():
    conn = create_connection()
    yield conn
    conn.close()
```

### Scopes
- **function** (default): Fresh for each test — maximum isolation
- **class**: Shared across test class methods
- **module**: Shared across test file — for expensive setup
- **session**: Shared across all tests — for very expensive operations

### conftest.py
- Place shared fixtures in `conftest.py` for automatic discovery
- Root `tests/conftest.py` for global fixtures
- Directory-specific `conftest.py` for localized fixtures

### Factory Fixtures
```python
@pytest.fixture
def make_backend():
    def _make_backend(key=None):
        if key is None:
            key = Fernet.generate_key()
        return FernetBackend(key=key)
    return _make_backend
```

### Anti-Patterns to Avoid
- Overloaded fixtures with too many responsibilities
- Hardcoded values (use factory pattern)
- Global state leakage without cleanup
- Deep fixture dependency chains

## Parametrization

```python
@pytest.mark.parametrize("input_data, expected", [
    (b"hello", b"hello"),
    (b"", b""),
    (b"\x00\xff", b"\x00\xff"),
], ids=["ascii", "empty", "binary"])
async def test_encrypt_decrypt_roundtrip(backend, input_data, expected):
    encrypted = await backend.encrypt(input_data)
    decrypted = await backend.decrypt(encrypted)
    assert decrypted == expected
```

## Assertions

### Principles
- One assertion concept per test
- Use plain `assert` — pytest provides detailed introspection
- Test public interfaces, not private methods

### Exception Testing
```python
def test_decrypt_with_wrong_key():
    with pytest.raises(DecryptionError) as excinfo:
        await backend.decrypt(ciphertext)
    assert "decryption failed" in str(excinfo.value).lower()
```

### Anti-Patterns
- Testing private methods (test public interface)
- Non-deterministic assertions (mock time, random)
- Multiple unrelated assertions in single test
- Not validating exception messages

## Async Testing

Use `pytest-asyncio` for async test functions:

```python
import pytest

@pytest.mark.asyncio
async def test_encrypt_returns_bytes(backend):
    result = await backend.encrypt(b"plaintext")
    assert isinstance(result, bytes)
```

For fixtures that need async setup/teardown:
```python
@pytest.fixture
async def session_service():
    service = EncryptedSessionService(db_url="sqlite+aiosqlite:///:memory:")
    yield service
    await service.close()
```

## Mocking

MUST use `pytest-mock` (the `mocker` fixture) for all mocking. Do NOT use `unittest.mock` directly (`from unittest.mock import Mock, patch`). The `mocker` fixture provides automatic cleanup and better pytest integration.

### When to Mock
- External API calls (KMS, Vault)
- Database connections (when unit testing)
- Expensive operations
- Non-deterministic code (time, random)

### pytest-mock Usage
```python
def test_api_call(mocker):
    mock_encrypt = mocker.patch(
        "adk_secure_sessions.services.encrypted_session.backend.encrypt"
    )
    mock_encrypt.return_value = b"ciphertext"

    result = await service.create_session(...)
    mock_encrypt.assert_called_once()
```

Use `mocker.AsyncMock()` for async methods:
```python
def test_async_backend(mocker):
    backend = mocker.AsyncMock()
    backend.encrypt.return_value = b"encrypted"
    backend.decrypt.return_value = b"decrypted"
```

### Patching Rule
Patch where the object is USED, not where it's DEFINED:
```python
# Correct — patch at the import site
mocker.patch("adk_secure_sessions.services.encrypted_session.backend.encrypt")

# Wrong — too broad
mocker.patch("adk_secure_sessions.backends.fernet.FernetBackend.encrypt")
```

### Prefer Fakes Over Mocks When Possible
For simple cases, a fake object is more readable than mock assertions:
```python
class FakeBackend:
    """In-memory backend for testing."""

    async def encrypt(self, plaintext: bytes) -> bytes:
        return b"encrypted:" + plaintext

    async def decrypt(self, ciphertext: bytes) -> bytes:
        return ciphertext.removeprefix(b"encrypted:")
```

## Quick Reference

```bash
uv run pytest                       # Run all tests
uv run pytest tests/unit/           # Run unit tests
uv run pytest -k "protocol"         # Match keyword
uv run pytest -m "not slow"         # Exclude slow
uv run pytest -v                    # Verbose
uv run pytest --lf                  # Last failed
uv run pytest -x                    # Stop on first failure
```
