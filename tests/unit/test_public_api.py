"""Public API surface guardrail tests.

Verifies that the package's public contract (``__all__``) stays consistent
with the actual module namespace and that package metadata resolves correctly.
A failure here means a refactoring silently broke every downstream import.
"""

from __future__ import annotations

import importlib.metadata
import re
import types

import pytest

import adk_secure_sessions

pytestmark = pytest.mark.unit


class TestAllExportsImportable:
    """Every symbol declared in ``__all__`` must be importable and non-None."""

    def test_all_is_defined(self) -> None:
        """Package exposes a non-empty __all__ list."""
        assert hasattr(adk_secure_sessions, "__all__")
        assert len(adk_secure_sessions.__all__) > 0

    def test_each_symbol_is_accessible(self) -> None:
        """Every __all__ symbol resolves to a non-None attribute."""
        for name in adk_secure_sessions.__all__:
            attr = getattr(adk_secure_sessions, name, None)
            assert attr is not None, (
                f"{name!r} is declared in __all__ but resolves to None"
            )


class TestAllConsistency:
    """``__all__`` and the module namespace must stay in sync."""

    def test_no_public_name_missing_from_all(self) -> None:
        """No public name in the module namespace is missing from __all__."""
        module_public = {
            name
            for name in dir(adk_secure_sessions)
            if not name.startswith("_")
            and not isinstance(getattr(adk_secure_sessions, name), types.ModuleType)
        }
        declared = set(adk_secure_sessions.__all__)
        missing = module_public - declared
        assert missing == set(), f"Public names not in __all__: {sorted(missing)}"

    def test_no_all_entry_missing_from_module(self) -> None:
        """No __all__ entry is absent from the module namespace."""
        declared = set(adk_secure_sessions.__all__)
        module_names = set(dir(adk_secure_sessions))
        extra = declared - module_names
        assert extra == set(), (
            f"__all__ entries not in module namespace: {sorted(extra)}"
        )


class TestPackageMetadata:
    """Package metadata must resolve for install-time validation."""

    def test_version_is_valid_semver(self) -> None:
        """Installed version string matches semver pattern."""
        version = importlib.metadata.version("adk-secure-sessions")
        assert re.match(r"^\d+\.\d+\.\d+", version), (
            f"Version {version!r} does not match semver pattern"
        )

    def test_package_name_resolves(self) -> None:
        """Package name in metadata matches distribution name."""
        meta = importlib.metadata.metadata("adk-secure-sessions")
        assert meta["Name"] == "adk-secure-sessions"
