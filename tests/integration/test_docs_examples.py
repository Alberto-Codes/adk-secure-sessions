"""Integration tests for documentation code examples.

Validates that code examples in documentation files execute successfully,
preventing documentation drift when the API changes. Each tested example
is marked with a sentinel HTML comment in the source markdown.

See Also:
    `docs/getting-started.md` for the Getting Started guide.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

# Path to docs directory relative to repo root
_DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"

# Pattern: sentinel comment followed by a fenced Python code block
_SENTINEL_PATTERN = re.compile(
    r"<!--\s*test:exec:(?P<name>[\w-]+)\s*-->\s*\n"
    r"```python\n(?P<code>.*?)```",
    re.DOTALL,
)


def _extract_example(doc_path: Path, sentinel_name: str) -> str:
    """Extract a Python code block marked by a sentinel comment.

    Args:
        doc_path: Path to the markdown file.
        sentinel_name: The sentinel identifier
            (e.g., ``getting-started-full-example``).

    Returns:
        The Python source code from the fenced block.

    Raises:
        ValueError: If the sentinel is not found in the file.
    """
    content = doc_path.read_text(encoding="utf-8")
    for match in _SENTINEL_PATTERN.finditer(content):
        if match.group("name") == sentinel_name:
            return match.group("code")
    msg = f"Sentinel 'test:exec:{sentinel_name}' not found in {doc_path}"
    raise ValueError(msg)


class TestGettingStartedExamples:
    """Validates that Getting Started guide examples run without error."""

    async def test_full_example_runs_successfully(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Full Working Example from Getting Started executes end-to-end.

        Extracts the code block marked with the
        ``test:exec:getting-started-full-example`` sentinel from
        ``docs/getting-started.md`` and executes it in an isolated
        temp directory. Verifies the example completes without raising.
        """
        doc_path = _DOCS_DIR / "getting-started.md"
        source = _extract_example(doc_path, "getting-started-full-example")

        # The example writes sessions.db to CWD — isolate in tmp_path
        monkeypatch.chdir(tmp_path)

        # Strip asyncio.run() — we're already in an async event loop.
        # exec() defines main(), then we await it directly.
        source = source.replace("asyncio.run(main())\n", "")

        namespace: dict[str, object] = {}
        exec(compile(source, f"{doc_path}:full-example", "exec"), namespace)  # noqa: S102
        await namespace["main"]()
