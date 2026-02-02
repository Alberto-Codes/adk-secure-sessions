# Contributing to adk-secure-sessions

Thank you for your interest in contributing to adk-secure-sessions! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)
- [Release Process](#release-process)

## Code of Conduct

This project follows standard open-source community guidelines. Be respectful, constructive, and collaborative in all interactions.

## Getting Started

### Prerequisites

- **Python 3.12** (strictly required)
- **uv** package manager (recommended)
- **Git** for version control

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Alberto-Codes/adk-secure-sessions.git
   cd adk-secure-sessions
   git checkout develop
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync --dev
   ```

3. **Verify the setup**:
   ```bash
   uv run pytest           # Run tests
   uv run ruff check .     # Check code style
   ```

### Project Structure

```
adk-secure-sessions/
├── src/adk_secure_sessions/   # Source code
│   ├── backends/              # Encryption backends (Fernet, SQLCipher, KMS)
│   ├── services/              # Session service implementations
│   └── migrations/            # Schema migration utilities
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests (fast, isolated)
│   └── integration/           # Integration tests (real databases)
├── docs/                      # Documentation source
│   └── contributing/          # Contributing guides and templates
└── .github/                   # GitHub templates and CI
```

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feat/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### Making Changes

1. Create a new branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feat/your-feature-name
   ```

2. Make your changes, following the code style guidelines below.

3. Run quality checks before committing:
   ```bash
   uv run ruff check .
   uv run ruff format .
   uv run pytest
   ```

4. Commit with conventional commit messages (see [Commit Messages](#commit-messages)).

5. Push and create a pull request targeting `develop`.

## Code Style

### Python Guidelines

- **Python 3.12** features are encouraged
- **Line length**: 88 characters (formatter), 100 (linter threshold)
- **Quotes**: Double quotes for strings
- **Imports**: Sorted automatically via ruff/isort

### Linting and Formatting

We use **ruff** for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

### Type Hints

All public functions and methods must have type annotations:

```python
async def create_session(
    self,
    app_name: str,
    user_id: str,
    *,
    state: dict[str, Any] | None = None,
) -> Session:
    """Create a new encrypted session."""
    ...
```

### Docstrings

We follow **Google-style docstrings** with strict quality standards enforced by `interrogate` (95% threshold).

See [docs/contributing/docstring-templates.md](docs/contributing/docstring-templates.md) for comprehensive templates.

Quick example:

```python
async def encrypt_state(
    self,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Encrypt all values in a session state dictionary.

    Args:
        state: Plaintext session state key-value pairs.

    Returns:
        Dictionary with encrypted values (keys remain plaintext).

    Raises:
        EncryptionError: If encryption fails for any value.

    Examples:
        ```python
        backend = FernetBackend(key="your-key")
        encrypted = await backend.encrypt_state({"ssn": "123-45-6789"})
        ```
    """
```

## Testing

### Test Structure

| Layer | Location | Purpose | Speed |
|-------|----------|---------|-------|
| Unit | `tests/unit/` | Isolated logic with mocks | Fast |
| Integration | `tests/integration/` | Real database encryption | Slow |

### Running Tests

```bash
# Default: unit tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=term-missing

# Specific markers
uv run pytest -m unit
uv run pytest -m integration
```

### Test Markers

Use appropriate markers for your tests:

```python
import pytest

@pytest.mark.unit
async def test_fernet_encrypt_decrypt():
    """Unit test for Fernet round-trip encryption."""
    ...

@pytest.mark.integration
async def test_encrypted_session_persistence():
    """Integration test with real SQLite database."""
    ...
```

### Writing Tests

- Use `pytest-asyncio` for async tests (auto mode enabled)
- Use `pytest-mock` for mocking (inject `mocker` fixture)
- Never commit real encryption keys or sensitive data in tests
- Use fixture-generated temporary databases for integration tests

### Deprecation Warning Handling

We treat all warnings as errors. When CI fails due to a third-party warning:

1. **Your code?** Fix it immediately.
2. **Third-party dependency?** Add an ignore in `pyproject.toml` with a tracking issue:
   ```toml
   # Description - Issue #NNN
   "ignore:warning message pattern:WarningType",
   ```
3. **Create a tracking issue** using the Tech Debt template.

## Documentation

### Documentation Standards

- All public APIs must have docstrings
- Include code examples in docstrings
- Update relevant docs when changing behavior
- Security-sensitive documentation should include threat model context

## Submitting Changes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Scopes**: `encryption`, `session`, `backend`, `migration`, `fernet`, `sqlcipher`, `kms`

**Examples**:
```
feat(backend): add AWS KMS encryption backend
fix(session): handle empty state encryption gracefully
docs(readme): update installation instructions
refactor(encryption): simplify key rotation logic
test(fernet): add round-trip encryption tests
```

**Breaking changes**: Add `!` after type and include `BREAKING CHANGE:` in footer:
```
feat(session)!: change encryption key parameter format

BREAKING CHANGE: encryption_key now accepts bytes instead of str.
Use key.encode() to migrate existing string keys.
```

### Pull Request Process

1. **Ensure all checks pass**:
   ```bash
   uv run ruff check .
   uv run pytest
   ```

2. **Fill out the PR template** with:
   - Clear description of changes
   - Link to related issues
   - Test coverage information
   - Breaking change notes (if applicable)

3. **PR Checklist**:
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated for changes
   - [ ] Documentation updated
   - [ ] Commit messages follow conventions
   - [ ] No secrets or keys committed

4. **Review process**:
   - PRs require review before merging
   - Address review feedback promptly
   - Keep PRs focused and reasonably sized

## Issue Reporting

### Choosing the Right Template

| Template | Use When |
|----------|----------|
| Bug Report | Something isn't working as expected |
| Feature Request | New encryption backend, feature, or improvement |
| Tech Debt | Code quality, schema migration needs, refactoring |

### Security Issues

**Do not open public issues for security vulnerabilities.** Instead, email alberto.codes.dev@gmail.com with details. See [SECURITY.md](SECURITY.md) for the full policy.

## Release Process

Releases follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking API changes
- **MINOR** (0.2.0): New features, backwards-compatible
- **PATCH** (0.1.1): Bug fixes, backwards-compatible

## Getting Help

- **Issues**: https://github.com/Alberto-Codes/adk-secure-sessions/issues
- **Discussions**: Use GitHub Issues for questions

Thank you for contributing to adk-secure-sessions!
