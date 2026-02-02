<!--
PR Title → squash commit subject (50 chars, imperative)
Format: type(scope): description
Types: feat | fix | docs | refactor | test | chore | perf

Scope: A noun describing a section of the codebase (per conventionalcommits.org).
  ✓ feat(encryption): add Fernet field-level encryption
  ✓ feat(session): support SQLCipher backend
  ✗ feat(001-feature): ...  ← NOT spec/issue numbers

Breaking: add ! after scope → feat(session)!: remove deprecated method
-->
<!--
Why this change? Problem solved? Contrast with previous behavior.
-->

<!--
What changed? 2-4 bullets, imperative mood.
-->
-

<!-- How to verify: command, manual steps, or "CI only" -->
Test: `uv run pytest -v`

<!--
Git trailers (one per line):
  Closes #123
  BREAKING CHANGE: remove deprecated foo() method
  Co-authored-by: Name <email>
-->
Closes #

---

## PR Review

### Checklist
- [ ] Self-reviewed my code
- [ ] Tests pass (`uv run pytest`)
- [ ] Lint passes (`uv run ruff check .`)
- [ ] Breaking changes use `!` in title and `BREAKING CHANGE:` in body

### Review Focus
<!-- Where should reviewers concentrate? Known limitations? -->

### Related
<!-- Other PRs, issues for context -->
