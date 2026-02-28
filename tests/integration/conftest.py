"""Integration test fixtures for adk-secure-sessions.

Integration-specific fixtures go in this file. Shared fixtures available
from the root `tests/conftest.py` include `fernet_backend`,
`encryption_key`, `db_path`, and `encrypted_service`.

Future stories (1.6a, 1.6b) may add integration-specific fixtures here.

See Also:
    `tests/conftest.py` for shared fixtures.
"""

from __future__ import annotations
