# Story 1.12: v1.0.0 Release & Community Announcement

Status: done
Branch: chore/release-1-12-v1-publish
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/72

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer searching for ADK session encryption**,
I want **the library published on PyPI as v1.0.0 and announced in the community**,
so that **the first "how to encrypt ADK sessions" post defines SEO and I can find and install it**.

## Acceptance Criteria

1. **Given** all previous Epic 1 stories are complete (1-1 through 1-11 are done)
   **When** the v1.0.0 release tag is pushed
   **Then** the publish workflow triggers and publishes to TestPyPI then PyPI
   **And** `pip install adk-secure-sessions` succeeds from a clean virtual environment (FR27)

2. **Given** the package is published on PyPI
   **When** a developer installs it in a fresh project
   **Then** the installed package provides IDE autocomplete and type checking via `py.typed` marker (FR30)

3. **Given** the package is published on PyPI
   **When** the PyPI project page is viewed
   **Then** it displays correct metadata, classifiers (`Topic :: Security :: Cryptography`, `Intended Audience :: Developers`), keywords (`adk`, `encryption`, `encrypted sessions`, `google adk security`), and project description (FR33)

4. **Given** the PyPI release is successful
   **When** a GitHub Discussion post is created within 24 hours
   **Then** the Discussion post title uses a search-intent format (e.g., "How to Encrypt ADK Sessions at Rest")
   **And** the body includes install instructions, key features, and the keyword phrase "encrypt ADK sessions" for SEO positioning

5. **Given** the hand-curated CHANGELOG.md v1.0.0 entry
   **When** viewed on PyPI or GitHub
   **Then** it lists product capabilities (not raw commit log) and sets the precedent for all future release entries

6. **Given** the release-please configuration is updated with `bootstrap-sha`
   **When** release-please runs after the v1.0.0 release
   **Then** it only considers commits after the bootstrap SHA for future releases
   **And** the next auto-generated release PR contains no genesis commit noise

## Tasks / Subtasks

- [x] Task 1: Close stale release-please PR #69 (AC: #6)
  - [x] 1.1 Close PR #69: `gh pr close 69 --comment "Superseded — resetting to v1.0.0 with curated CHANGELOG and bootstrap-sha"`

- [x] Task 2: Version reset and release-please bootstrap (AC: #5, #6)
  - [x] 2.1 Update `pyproject.toml` version from `0.1.1` to `1.0.0`
  - [x] 2.2 Update `.release-please-manifest.json` from `{"." : "0.1.1"}` to `{"." : "1.0.0"}`
  - [x] 2.3 Add `"bootstrap-sha": "98c3d5bcb02ada0323c73e11aae3dcd4ffc3e283"` to top level of `release-please-config.json` (current HEAD of main — ensures release-please ignores all genesis commits)
  - [x] 2.4 Verify `release-please-config.json` is valid JSON after edit
  - [x] 2.5 Verify README renders for PyPI: `python -m readme_renderer README.md -o /tmp/readme.html` (install `readme-renderer[md]` if needed — PyPI uses a stricter markdown parser than GitHub)

- [x] Task 3: Hand-curate CHANGELOG.md v1.0.0 entry (AC: #5)
  - [x] 3.1 Replace the current auto-generated CHANGELOG.md with a curated v1.0.0 entry
  - [x] 3.2 Entry format — product capabilities, not commit log (see CHANGELOG Template in Dev Notes)
  - [x] 3.3 Use `releases/tag/v1.0.0` link format (not commit compare) for the version header
  - [x] 3.4 Verify the entry renders correctly in markdown preview

- [x] Task 4: Commit, push, and create manual GitHub Release (AC: #1)
  - [x] 4.1 Run `pre-commit run --all-files` — all hooks must pass before committing
  - [x] 4.2 Commit all changes: `chore(release): prepare v1.0.0 with curated CHANGELOG and bootstrap-sha`
  - [x] 4.3 Push to main
  - [x] 4.4 Create manual GitHub Release: `gh release create v1.0.0 --title "v1.0.0" --notes-file /tmp/release-notes.md`
  - [x] 4.5 Confirm `v1.0.0` tag is created and triggers `.github/workflows/publish.yml`

- [x] Task 5: Monitor publish pipeline (AC: #1)
  - [x] 5.1 Monitor workflow run: quality-gate -> build -> publish-testpypi -> smoke-test -> publish-pypi
  - [x] 5.2 If any job fails, diagnose using Troubleshooting section in Dev Notes
  - [x] 5.3 Confirm TestPyPI publish succeeds (check https://test.pypi.org/project/adk-secure-sessions/)
  - [x] 5.4 Confirm PyPI publish succeeds (check https://pypi.org/project/adk-secure-sessions/)

- [x] Task 6: Post-publish verification from real PyPI (AC: #1, #2, #3)
  - [x] 6.1 Create a temporary virtual environment: `python -m venv /tmp/test-install && source /tmp/test-install/bin/activate`
  - [x] 6.2 Install from PyPI: `pip install adk-secure-sessions==1.0.0`
  - [x] 6.3 Verify import: `python -c "from adk_secure_sessions import EncryptedSessionService, FernetBackend; print('v1.0.0 verified')"`
  - [x] 6.4 Verify `py.typed` marker: `python -c "import importlib.resources; print(importlib.resources.files('adk_secure_sessions') / 'py.typed')"`
  - [x] 6.5 Verify PyPI page metadata: classifiers, keywords, description, project URLs at https://pypi.org/project/adk-secure-sessions/
  - [x] 6.6 Clean up: `deactivate && rm -rf /tmp/test-install`

- [x] Task 7: Create GitHub Discussion announcement post (AC: #4)
  - [x] 7.1 Enable GitHub Discussions on the repo if not already enabled (Settings -> Features -> Discussions)
  - [x] 7.2 Create Discussion post in "Announcements" category (see Discussion Post Template in Dev Notes)
  - [x] 7.3 Pin the Discussion post (manual — pin API not available via GraphQL; user must pin from UI)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Verification Method | Type | Status |
|------|---------------------|------|--------|
| 1 (pip install works) | `pip install adk-secure-sessions==1.0.0` in fresh venv + import test | Manual | pass |
| 2 (IDE autocomplete) | Verify `py.typed` in installed package via `importlib.resources` | Manual | pass |
| 3 (PyPI metadata) | `pip show --verbose adk-secure-sessions` — classifiers, keywords, URLs verified | Manual | pass |
| 4 (Discussion post) | GitHub Discussion #74 created in Announcements — title uses search-intent, SEO phrase present | Manual | pass |
| 5 (CHANGELOG quality) | Review curated v1.0.0 entry — 7 capability bullets with scoped prefixes, no commit log noise | Manual | pass |
| 6 (bootstrap-sha) | Release-please PR #73 (v1.0.1) contains only post-bootstrap fix(ci) commit — no genesis noise | Post-release | pass |

## Dev Notes

### What This Story Does

This story performs a **version reset to v1.0.0** and executes the first PyPI publish. The library has never been released — no git tags, no GitHub Releases, no PyPI publishes exist. The existing release-please PR #69 (v0.1.2) carries noisy genesis commits and a pre-1.0 version number that misrepresents the library's maturity.

**The approach:**
1. **Reset to v1.0.0** — the library has 167 tests at 99.68% coverage, 5 ADRs, SECURITY.md, Apache-2.0 license, and a complete publish pipeline. This is a 1.0.
2. **Hand-curate the CHANGELOG** — the v1.0.0 entry is a product announcement, not a commit log. This sets precedent for the project.
3. **Add `bootstrap-sha`** — prevents release-please from re-ingesting genesis commits. Future releases auto-generate cleanly from this baseline.
4. **Manual GitHub Release** — `gh release create v1.0.0` creates the tag that triggers `publish.yml`. Release-please manages all subsequent releases automatically.

This story modifies **4 files** (pyproject.toml, manifest, config, CHANGELOG) and is otherwise operational (verify publish, verify install, write announcement).

### Why v1.0.0 and Not v0.1.2

| Signal | v0.1.2 | v1.0.0 |
|--------|--------|--------|
| Semver meaning | "Initial development, anything may change" | "Public API is defined and stable" |
| Trust signal | "Pre-release, maybe don't depend on it" | "Production-ready, safe to adopt" |
| Version history | Implies 2 prior releases that never happened | Clean first release |
| Semver behavior | `feat` → 0.2.0 (minor bump stays pre-1.0) | `feat` → 1.1.0 (proper semver) |

The `__init__.py` exports 13 stable public symbols. The API is defined. v1.0.0 is correct per semver.

### The Docvet Pattern (Proven)

This approach mirrors the docvet project's first release:
- docvet used `bootstrap-sha` pointing to the commit that added the release pipeline
- docvet's v1.0.0 CHANGELOG was hand-curated with product capabilities
- docvet's v1.0.0 link format: `releases/tag/v1.0.0` (not a commit compare)
- All subsequent releases (1.0.1, 1.0.2, ..., 1.6.2) were auto-generated cleanly by release-please

### Publish Pipeline Chain (Already Built — Story 1-11)

```
gh release create v1.0.0 (manual)
     |
  creates v1.0.0 tag
     |
  tag push triggers publish.yml
     |
quality-gate  (lint, format, type-check, test, interrogate, pip-audit)
     |
   build      (uv build -> upload dist/ artifact)
     |
publish-testpypi  (OIDC trusted publishing)
     |
smoke-test    (install from TestPyPI -> verify import)
     |
publish-pypi  (OIDC trusted publishing)
```

### CHANGELOG Template (v1.0.0)

```markdown
# Changelog

## [1.0.0](https://github.com/Alberto-Codes/adk-secure-sessions/releases/tag/v1.0.0) (2026-03-XX)

### Features

* **session:** EncryptedSessionService — drop-in replacement for ADK's BaseSessionService with field-level encryption at rest
* **encryption:** Fernet symmetric encryption backend (AES-128-CBC + HMAC-SHA256) with async-first design
* **serialization:** Self-describing binary envelope format with version and backend metadata for future key rotation
* **persistence:** Async SQLite persistence via aiosqlite with own schema, independent of ADK internals
* **validation:** ConfigurationError with startup-time passphrase and backend validation
* **security:** Coordinated disclosure policy (SECURITY.md), Apache-2.0 license, zero-CVE dependency audit
* **ci:** Automated PyPI releases via OIDC trusted publishing — no stored tokens, changelog generation via release-please
```

**Rules for this entry:**
- Each bullet describes a **capability**, not a code change
- Scopes match codebase nouns (session, encryption, serialization, persistence, validation, security, ci)
- No genesis noise (no "add .gitignore", "add pyproject.toml")
- Date filled in at release time

### Discussion Post Template

**Title:** How to Encrypt ADK Sessions at Rest with adk-secure-sessions

**Body structure:**
1. **Opening** (first 160 chars — Google snippet): "adk-secure-sessions is a drop-in encrypted session service for Google ADK. Encrypt ADK sessions at rest with one import swap."
2. **Install:** `pip install adk-secure-sessions`
3. **Quick-start code** (5 lines, same as README — swap BaseSessionService for EncryptedSessionService)
4. **Key features** (bullet list): field-level encryption, Fernet backend, async-first, envelope wire protocol, SQLite persistence, py.typed, 99%+ test coverage
5. **Links:** PyPI, GitHub, SECURITY.md, CONTRIBUTING.md
6. **SEO:** "encrypt ADK sessions" appears in title, opening paragraph, and at least once in the body

**Why search-intent title:** "How to Encrypt ADK Sessions at Rest" matches what a developer would Google. A version announcement title ("adk-secure-sessions v1.0.0") only matters to people who already know the library exists.

### release-please-config.json After Changes

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "bootstrap-sha": "98c3d5bcb02ada0323c73e11aae3dcd4ffc3e283",
  "release-type": "python",
  "include-component-in-tag": false,
  "changelog-sections": [
    { "type": "feat", "section": "Features" },
    { "type": "fix", "section": "Bug Fixes" },
    { "type": "perf", "section": "Performance Improvements" },
    { "type": "refactor", "section": "Code Refactoring", "hidden": true },
    { "type": "docs", "section": "Documentation" },
    { "type": "chore", "section": "Maintenance", "hidden": true },
    { "type": "test", "section": "Tests", "hidden": true },
    { "type": "ci", "section": "CI", "hidden": true }
  ],
  "packages": {
    ".": {
      "package-name": "adk-secure-sessions",
      "changelog-path": "CHANGELOG.md",
      "extra-files": [
        {
          "type": "toml",
          "path": "pyproject.toml",
          "jsonpath": "$.project.version"
        }
      ]
    }
  },
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true
}
```

**Note:** `bump-minor-pre-major` and `bump-patch-for-minor-pre-major` are harmless at v1.0.0+ (they only affect 0.x versioning). Leave them for now — they can be cleaned up in a future chore commit.

### Prerequisites Already Complete

| Prerequisite | Story | Status |
|-------------|-------|--------|
| Package metadata (classifiers, keywords, URLs) | 1-7 | done |
| `py.typed` marker | 1-7 | done |
| README with badges, quickstart, positioning | 1-9 | done |
| SECURITY.md + LICENSE | 1-8 | done |
| Trunk-based development on `main` | 1-10 | done |
| release-please config + workflow | 1-11 | done |
| `publish.yml` (5-job pipeline) | 1-11 | done |
| TestPyPI trusted publisher configured | 1-11 (Task 6) | done |
| PyPI trusted publisher configured | 1-11 (Task 6) | done |
| `RELEASE_PLEASE_TOKEN` PAT secret | 1-11 (Task 6) | done |
| GitHub environments (`testpypi`, `pypi`) | 1-11 (Task 6) | done |

### Troubleshooting: If Publish Fails

**quality-gate fails:**
- Something broke on `main` since the last CI run. Fix the issue, push to main, delete the `v1.0.0` tag and release, recreate after fix.

**publish-testpypi fails with 403:**
- Trusted publisher not configured on TestPyPI, or environment name mismatch. Verify at https://test.pypi.org/manage/project/adk-secure-sessions/settings/publishing/
- Check: Owner = `Alberto-Codes`, Repository = `adk-secure-sessions`, Workflow = `publish.yml`, Environment = `testpypi`

**publish-pypi fails with 403:**
- Same as above but for PyPI: https://pypi.org/manage/project/adk-secure-sessions/settings/publishing/
- Check: Owner = `Alberto-Codes`, Repository = `adk-secure-sessions`, Workflow = `publish.yml`, Environment = `pypi`

**smoke-test fails (package not found):**
- TestPyPI index propagation can take >30 seconds. The `sleep 30` in the smoke test may not be enough. Re-run the job — don't panic on first failure.

**smoke-test fails (import error):**
- The wheel is missing modules. Check `uv build` output and wheel contents. Likely a `pyproject.toml` include/exclude issue.

**Tag doesn't trigger publish.yml:**
- Manual `gh release create` tags are created by the authenticated user, not `GITHUB_TOKEN`, so this shouldn't be an issue. But verify the tag exists: `git ls-remote --tags origin v1.0.0`

**Published wrong version to PyPI:**
- PyPI is immutable — a published version cannot be overwritten or re-uploaded. If the wrong content was published, you must `yank` the version on PyPI and publish the next patch version (e.g., 1.0.1) with the correct content. Plan carefully before `gh release create`.

### What Changes in This Story

**Modified files:**
- `pyproject.toml` — version bump from `0.1.1` to `1.0.0`
- `.release-please-manifest.json` — version update to `1.0.0`
- `release-please-config.json` — add `bootstrap-sha`
- `CHANGELOG.md` — replace auto-generated content with curated v1.0.0 entry

**No changes to:**
- Python source code
- CI/CD workflows
- Any other configuration

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| CHANGELOG.md | Complete rewrite — curated v1.0.0 entry replacing auto-generated genesis noise |

### Project Structure Notes

- No new files created in the source tree
- 4 files modified (pyproject.toml, manifest, config, CHANGELOG)
- All modifications are release preparation — no functional changes

### Previous Story Intelligence (1-11)

**Patterns established:**
- Configuration-only story (no Python source changes) — same pattern here
- 167 tests passing at 99.68% coverage (all quality gates green)
- `pre-commit run --all-files` runs 7 hooks
- Trusted publishing (OIDC) configured for both TestPyPI and PyPI
- `RELEASE_PLEASE_TOKEN` PAT created with `repo` scope
- TestPyPI index configured in `pyproject.toml`
- Publish workflow validated by actionlint

**Key risk from 1-11 review:**
- **Silent failure**: If `RELEASE_PLEASE_TOKEN` expires or is revoked, release-please falls back to `GITHUB_TOKEN`, which creates releases/tags that **don't trigger** the publish workflow. Not applicable to v1.0.0 (manual release), but relevant for all subsequent releases.

### Git Context

Latest commits on main:
- `98c3d5b` feat(ci): add PyPI publish pipeline with trusted publishing
- `76027c4` chore(sprint): mark story 1.10 done
- `7884bef` docs(context): update project-context.md branch references to main
- `3b1864c` chore(ci): migrate to trunk-based development on main
- `b2b6713` docs(readme): rewrite with compliance gateway positioning

Full SHA for bootstrap-sha: `98c3d5bcb02ada0323c73e11aae3dcd4ffc3e283`

Open PR to close: #69 `chore(main): release 0.1.2`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.12 — v0.1.0 Release & Community Announcement]
- [Source: _bmad-output/planning-artifacts/epics.md#FR27 — pip install from PyPI]
- [Source: _bmad-output/planning-artifacts/epics.md#FR30 — py.typed + IDE autocomplete]
- [Source: _bmad-output/planning-artifacts/epics.md#FR33 — PyPI discoverability metadata]
- [Source: _bmad-output/implementation-artifacts/1-11-ci-cd-publish-pipeline.md — publish pipeline details]
- [Source: _bmad-output/implementation-artifacts/1-11-ci-cd-publish-pipeline.md#PyPI Trusted Publishing Setup]
- [Source: .github/workflows/publish.yml — publish pipeline (5 jobs)]
- [Source: .github/workflows/release-please.yml — release automation with PAT]
- [Source: release-please-config.json — release config (adding bootstrap-sha)]
- [Source: .release-please-manifest.json — current version 0.1.1, updating to 1.0.0]
- [Source: PR #69 — chore(main): release 0.1.2 (to be closed)]
- [Source: docvet release-please-config.json — bootstrap-sha pattern reference]
- [Source: docvet CHANGELOG.md — curated v1.0.0 entry pattern reference]
- [Source: https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md — bootstrap-sha docs]

## Quality Gates

- [x] `pre-commit run --all-files` — all 7 hooks pass after version bump
- [x] `pip install adk-secure-sessions==1.0.0` succeeds from fresh venv
- [x] `python -c "from adk_secure_sessions import EncryptedSessionService"` works
- [x] PyPI page shows correct metadata and version 1.0.0
- [x] CHANGELOG.md v1.0.0 entry is curated (capabilities, not commit log)
- [x] GitHub Discussion post published with SEO-optimized title and content
- [x] Release-please bootstrap-sha prevents genesis noise in future releases — verified via PR #73

## Code Review

- **Reviewer:** Code Review Workflow (Claude Opus 4.6) — 2026-03-01
- **Outcome:** Approved with fixes applied

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | HIGH | `Development Status :: 3 - Alpha` contradicts v1.0.0 positioning (pyproject.toml:34) | Fixed → `4 - Beta` (party mode consensus: Beta until real-world adoption) |
| 2 | MEDIUM | No `--check-url` on `publish-pypi` job — retry fragility (publish.yml:165) | Fixed → added `--check-url https://pypi.org/simple/` for idempotent retries |
| 3 | LOW | Stale local branch `chore/release-1-12-v1-publish` never used for PR | Fixed → branch deleted |
| 4 | LOW | Story filename uses `v010` (v0.1.0) vs v1.0.0 content | Rejected — filename is sprint tracking identifier, renaming breaks references |
| 5 | LOW | Dead `bump-minor-pre-major` config in release-please at v1.0.0+ | Informational — already documented in Dev Notes, cleanup when file next touched |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [x] Tests pass after review fixes
- [x] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-01 | Story created by create-story workflow. Initial version targeted v0.1.2 via release-please PR #69. |
| 2026-03-01 | Party mode review: Unanimous consensus to reset to v1.0.0. Rationale: (1) Library maturity warrants 1.0 — 167 tests, 99.68% coverage, stable API with 13 public symbols. (2) v0.1.2 implies 2 phantom prior releases. (3) Genesis CHANGELOG noise eliminated via bootstrap-sha. (4) Curated CHANGELOG sets professional precedent (docvet pattern). (5) SEO-optimized Discussion title uses search-intent format. Story fully rewritten with 7-task v1.0.0 approach. |
| 2026-03-01 | Party mode review (8-agent, 3-round): Applied 8 consensus items. HIGH: (1) Reordered Task 4 subtasks — pre-commit before commit. (2) Replaced phantom CHANGELOG_v1_excerpt with explicit sed extraction in gh release command. MEDIUM: (3) Added Task 2.5 — README render check via readme_renderer. LOW: (4) Branch name chore/ prefix. (5) PyPI immutability note in troubleshooting. (6) CHANGELOG ci bullet rewritten for both audiences. (7) AC6 type corrected to Post-release. (8) Task 1.1 explicit gh pr close command. |
| 2026-03-01 | Implementation complete. v1.0.0 published to PyPI. Smoke-test fix applied to publish.yml (missing uv venv). GitHub Discussion #74 created. All ACs verified except AC6 (post-release, requires subsequent commit). |
| 2026-03-01 | Code review (5-agent party mode, 1 round): 5 findings — 2 fixed (HIGH: Alpha→Beta classifier, MEDIUM: --check-url on publish-pypi), 1 cleanup (stale branch deleted), 1 rejected (filename rename breaks tracking), 1 informational (dead config keys). All HIGH/MEDIUM resolved. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Publish pipeline run 1 (22551287493): smoke-test failed — `uv pip install` requires a virtual environment. Fixed by adding `uv venv` step.
- Publish pipeline run 2 (22551365784): All 5 jobs passed. TestPyPI re-publish handled by `--check-url`.

### Completion Notes List

- Closed stale release-please PR #69 (v0.1.2)
- Version reset from 0.1.1 to 1.0.0 across pyproject.toml, manifest, and config
- Added bootstrap-sha to release-please-config.json (SHA: 98c3d5b)
- Hand-curated CHANGELOG.md with 7 product capability bullets
- Fixed publish.yml smoke-test (missing `uv venv`) and added `--check-url` for TestPyPI resilience
- v1.0.0 published to PyPI via OIDC trusted publishing (full pipeline: quality-gate -> build -> TestPyPI -> smoke-test -> PyPI)
- Post-publish verification: fresh venv install, import, py.typed marker, metadata all confirmed
- GitHub Discussion #74 created in Announcements category with SEO-optimized title
- AC6 (bootstrap-sha validation) is post-release — requires a subsequent commit to verify

### File List

- `pyproject.toml` — version bump 0.1.1 → 1.0.0
- `.release-please-manifest.json` — version update 0.1.1 → 1.0.0
- `release-please-config.json` — added bootstrap-sha
- `CHANGELOG.md` — replaced auto-generated genesis noise with curated v1.0.0 entry
- `.github/workflows/publish.yml` — fixed smoke-test (uv venv), added --check-url to TestPyPI
- `uv.lock` — lockfile sync with version bump
