# Story 1.10: Trunk-Based Migration to Main

Status: in-progress
Branch: chore/ci-1-10-trunk-migration
GitHub Issue: https://github.com/Alberto-Codes/adk-secure-sessions/issues/67

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **library maintainer**,
I want **the repository migrated from develop-based branching to main as the default branch**,
so that **the publish pipeline can trigger on release tags from main, following standard open-source conventions**.

## Acceptance Criteria

1. **Given** the repository uses `develop` as the primary branch
   **When** I migrate to trunk-based development with `main` as default
   **Then** `main` exists and contains the current `develop` content
   **And** CI workflows (`ci.yml`, `docs.yml`, `release-please.yml`) are updated to reference `main` instead of `develop`
   **And** branch protection rules are applied to `main`
   **And** the publish pipeline can be configured to trigger on release tags (enables Story 1.11)

## Tasks / Subtasks

- [x] Task 1: Update CI workflow triggers and config to reference `main` (AC: #1)
  - [x] 1.1 Update `.github/workflows/ci.yml` — change `branches: [main, develop]` to `branches: [main]` for both `pull_request` and `push` triggers
  - [x] 1.2 Update `.github/workflows/release-please.yml` — change `push.branches` from `[develop]` to `[main]` and `target-branch` from `develop` to `main`
  - [x] 1.3 Verify `.github/workflows/docs.yml` needs no branch changes (only triggers on PRs, no branch filter)
  - [x] 1.4 Update `.github/dependabot.yml` — change both `target-branch: "develop"` to `target-branch: "main"` (lines 9, 23) [added by code review]

- [x] Task 2: Update README.md branch references (AC: #1)
  - [x] 2.1 Update CI badge URL: `?branch=develop` to `?branch=main` (line 2)
  - [x] 2.2 Update docs link: `/tree/develop/docs` to `/tree/main/docs` (lines 42 and 56)

- [x] Task 3: Update CONTRIBUTING.md branch references (AC: #1)
  - [x] 3.1 Replace `git checkout develop` with `git checkout main` in Development Setup section (line 35)
  - [x] 3.2 Replace all `develop` branch references in Making Changes section (lines 111-115): `git checkout develop`, `git pull origin develop`, and "targeting `develop`" (line 132)

- [x] Task 4: Update docs/development-guide.md branch references (AC: #1)
  - [x] 4.1 Replace `git checkout develop` with `git checkout main` in Setup section (line 21)
  - [x] 4.2 Update "Base branch" entry from `develop (not main)` to `main` (line 95)
  - [x] 4.3 Update "PRs: target `develop`" to "PRs: target `main`" (line 98)
  - [x] 4.4 Update CI/CD section: Release Please trigger description from "`develop`" to "`main`" (line 80)
  - [x] 4.5 Update Tests Workflow trigger description from "`main`/`develop`" to "`main`" (line 69)

- [x] Task 5: Update `.claude/rules/` and CLAUDE.md agent instructions (AC: #1)
  - [x] 5.1 Update `.claude/rules/pull-requests.md` — change "PRs target `develop`" to "PRs target `main`" and all `develop` diff/log references
  - [x] 5.2 Update `.claude/rules/sonarqube.md` — change "After merging to develop" to "After merging to main" and "on develop branch" to "on main branch"
  - [x] 5.3 Update `CLAUDE.md` — no `develop` references found; CLAUDE.md is auto-generated and currently has no branch references. No changes needed.

- [ ] Task 6: Post-merge migration steps — create `main` branch and configure GitHub (AC: #1)
  **Note:** Phase 2 requires GitHub repo admin access. The dev agent may not have `gh repo edit` or branch protection API permissions. These steps may require manual user intervention.
  - [ ] 6.1 Create `main` branch from `develop`: `git checkout -b main develop && git push -u origin main`
  - [ ] 6.2 Set default branch to `main`: `gh repo edit --default-branch main`
  - [ ] 6.3a Run CI on `main` (push triggers it), then verify exact status check context names: `gh api repos/Alberto-Codes/adk-secure-sessions/commits/HEAD/check-runs --jq '.check_runs[].name'`
  - [ ] 6.3b Apply branch protection to `main` using verified check names from 6.3a — require status checks, require up-to-date branches, enforce for admins
  - [ ] 6.4 Update `remotes/origin/HEAD` to point to `main`
  - [ ] 6.5 Verify release-please still has valid state by checking `.release-please-manifest.json` (version: 0.1.1) — no changes needed, manifest is branch-agnostic
  - [ ] 6.6 Regenerate `_bmad-output/project-context.md` to reflect `main` as base branch [added by code review]

- [ ] Task 7 (optional): Clean up stale local branches — not in AC, good hygiene
  - [ ] 7.1 Delete stale local branches that are already merged: `002-encryption-backend-protocol`, `003-fernet-backend`, `004-exception-hierarchy`, `006-encrypted-session-service`, `chore/bmad-github-tracking`, `chore/pr-review-comments-rule`, `feat/session-1-2-schema-version-reservation`, `feat/session-1-3-configurationerror-startup-validation`
  - [ ] 7.2 Verify `develop` branch can be archived or kept as historical (do NOT delete — may have open references)

- [x] Task 8: Run quality gates (AC: all)
  - [x] 8.1 `pre-commit run --all-files` — all 7 hooks pass (actionlint validated workflow YAML)
  - [x] 8.2 `uv run pytest` — all 167 tests pass, 99.68% coverage (>= 90% threshold)
  - [x] 8.3 Verify no broken links — repo-wide grep confirmed zero remaining `develop` branch references in `.github/`, `docs/`, `.claude/`, `CONTRIBUTING.md`, `README.md`, `CLAUDE.md` [scope corrected by code review — original grep only checked changed files]

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done -->

| AC # | Test(s) | Status |
|------|---------|--------|
| 1 (main exists) | Phase 2: `git branch -a` shows `main` with same HEAD as `develop` | pending (Phase 2) |
| 1 (CI workflows) | `ci.yml` references `main` only; `release-please.yml` targets `main`; actionlint passes (pre-commit) | pass |
| 1 (branch protection) | Phase 2: `gh api repos/.../branches/main/protection` returns protection rules | pending (Phase 2) |
| 1 (publish pipeline) | `release-please.yml` triggers on `main` push; `target-branch: main` confirmed in file | pass |

## Dev Notes

### What This Story Does

This story migrates the repository from `develop`-based branching to trunk-based development with `main` as the default branch. This is a prerequisite for Story 1.11 (CI/CD Publish Pipeline), which needs release-please to create releases from `main` so that release tags trigger the publish workflow.

This is primarily a **configuration and documentation story** — no Python source code changes, no test changes. The changes are:
1. GitHub Actions workflow YAML files (CI triggers and release-please target)
2. Documentation files (README, CONTRIBUTING, development guide)
3. AI agent instruction files (CLAUDE.md, `.claude/rules/`)
4. GitHub repository settings (default branch, branch protection)

### Execution Order Is Critical

This story has a **chicken-and-egg problem**: the config changes reference `main`, but the PR workflow still targets `develop`. The correct execution order is:

**Phase 1 — Code Changes (on feature branch, PR to `develop`):**
- Tasks 1-5: Update all file references from `develop` to `main`
- Task 8: Quality gates
- Merge PR to `develop`

**Phase 2 — Repository Migration (post-merge, manual/scripted):**
- Task 6: Create `main` from `develop`, set default branch, apply protection
- Task 7: Clean up stale branches

**Important:** The PR for Phase 1 MUST target `develop` (it's still the default branch at PR time). After merging, Phase 2 creates `main` from the updated `develop`, making `main` the source of truth with all the correct references.

### Files That Reference `develop` (Full Blast Radius)

**CI workflows and GitHub config (must change):**
| File | Line(s) | Current | Target |
|------|---------|---------|--------|
| `.github/workflows/ci.yml` | 5, 7 | `branches: [main, develop]` | `branches: [main]` |
| `.github/workflows/release-please.yml` | 6 | `branches: [develop]` | `branches: [main]` |
| `.github/workflows/release-please.yml` | 29 | `target-branch: develop` | `target-branch: main` |
| `.github/dependabot.yml` | 9, 23 | `target-branch: "develop"` | `target-branch: "main"` [found by code review] |

**Documentation (must change):**
| File | Line(s) | Reference |
|------|---------|-----------|
| `README.md` | 2 | `?branch=develop` in CI badge URL |
| `README.md` | 42, 56 | `/tree/develop/docs` links |
| `CONTRIBUTING.md` | 35 | `git checkout develop` |
| `CONTRIBUTING.md` | 111-115 | `git checkout develop`, `git pull origin develop` |
| `CONTRIBUTING.md` | 132 | "targeting `develop`" |
| `docs/development-guide.md` | 19-21 | `git checkout develop` |
| `docs/development-guide.md` | 69 | "Push to `main`/`develop`" |
| `docs/development-guide.md` | 80 | "Push to `develop`" |
| `docs/development-guide.md` | 95 | "Base branch: `develop`" |
| `docs/development-guide.md` | 98 | "target `develop`" |

**AI agent instructions (must change):**
| File | Reference |
|------|-----------|
| `CLAUDE.md` | "Base branch: `develop`", `git diff develop..HEAD` |
| `.claude/rules/pull-requests.md` | "PRs target `develop`", `git diff develop..HEAD` |
| `.claude/rules/sonarqube.md` | "After merging to develop", "on develop branch" |

**Files that do NOT need changing:**
| File | Reason |
|------|--------|
| `.github/workflows/docs.yml` | No branch filter — triggers on any PR with matching paths |
| `release-please-config.json` | No branch reference — branch is set in the workflow YAML |
| `.release-please-manifest.json` | Branch-agnostic version tracker |
| `sonar-project.properties` | No branch reference (Community Edition has no branch analysis) |
| `SECURITY.md` | "pre-release" mention is about versioning, not branching |
| `CHANGELOG.md` | Historical commit links are permanent — do not rewrite history |
| `_bmad-output/project-context.md` | Will be regenerated — do not manually update BMAD output |
| `_bmad-output/implementation-artifacts/*.md` | Historical story files — do not retroactively modify |

### CI Badge Strategy

The CI badge URL currently uses `?branch=develop`. After migration:
- Change to `?branch=main`
- Badge will show "failing" briefly during the transition window (after `develop` references are removed but before `main` exists and CI runs)
- This is acceptable for a pre-release library with zero PyPI users — the badge self-heals once `main` receives its first push and CI runs
- **Do not panic** if the badge shows an error state between Phase 1 merge and Phase 2 completion

### release-please Transition

release-please tracks state via:
1. **`.release-please-manifest.json`** — version only (`"0.1.1"`), no branch reference
2. **`release-please-config.json`** — package config only, no branch reference
3. **Workflow YAML** — `target-branch` parameter tells release-please which branch to create release PRs against

The transition is clean: change `target-branch` from `develop` to `main`, and release-please will create release PRs targeting `main` on the next qualifying push. No manifest reset needed.

### Branch Protection Rules for `main`

**Step 1 (Task 6.3a):** After creating `main` and pushing (which triggers CI), verify the exact status check context names:

```bash
gh api repos/Alberto-Codes/adk-secure-sessions/commits/HEAD/check-runs --jq '.check_runs[].name'
```

**Step 2 (Task 6.3b):** Configure protection using the verified check names. Reference template (context names are examples — use verified names from step 1):

```bash
gh api repos/Alberto-Codes/adk-secure-sessions/branches/main/protection \
  -X PUT \
  -f required_status_checks='{"strict":true,"contexts":["lint","type-check","test (3.12, 1.22.0)","test (3.12, latest)","test (3.13, 1.22.0)","test (3.13, latest)","interrogate","docvet"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":0}' \
  -f restrictions=null
```

**Risk:** GitHub silently ignores unknown context names in branch protection. If check names are wrong, PRs could merge without required checks. For a security library, this is unacceptable — always verify first.

### What About the `develop` Branch?

**Do NOT delete `develop`.** Reasons:
- Existing PRs may reference it
- Historical story files reference it in branch fields
- GitHub issue/PR links reference commits on `develop`
- CHANGELOG.md has permanent commit links

`develop` becomes a historical branch. It will naturally diverge (no new pushes) and can be archived later if desired. The critical action is setting `main` as default so new clones, forks, and PRs target it.

### Documentation Impact

| Page | Nature of Update |
|------|-----------------|
| `.github/workflows/ci.yml` | UPDATE — branch triggers from `[main, develop]` to `[main]` |
| `.github/workflows/release-please.yml` | UPDATE — trigger branch and target-branch from `develop` to `main` |
| `README.md` | UPDATE — CI badge branch, docs link branch references |
| `CONTRIBUTING.md` | UPDATE — all `develop` branch references to `main` |
| `docs/development-guide.md` | UPDATE — all `develop` branch references to `main` |
| `CLAUDE.md` | UPDATE — base branch and diff references |
| `.claude/rules/pull-requests.md` | UPDATE — PR target branch and diff references |
| `.claude/rules/sonarqube.md` | UPDATE — merge target branch references |

### Project Structure Notes

- No changes to `src/` directory
- No changes to `tests/` directory
- No changes to `pyproject.toml`
- All changes are to workflow YAML, markdown documentation, and AI agent instructions
- Aligns with standard open-source convention (main as trunk)
- Enables Story 1.11 (publish pipeline triggers on release tags from main)

### Previous Story Intelligence (1.9)

**Patterns established:**
- Documentation-only story — no Python code changes, no test changes
- 167 tests passing at 99.68% coverage (all quality gates green)
- `pre-commit run --all-files` runs 7 hooks: yamllint, actionlint, ruff-check, ruff-format, ty check, pytest, docvet
- actionlint hook validates GitHub Actions workflow YAML — will catch syntax errors in ci.yml and release-please.yml changes
- License confirmed as Apache-2.0
- pyproject.toml version is `0.1.1`

**Review learnings to carry forward:**
- Verify task completion claims with actual file inspection (Story 1.9 had a sqlalchemy dep issue caught in review)
- Be precise about technical claims — verify file contents, don't assume
- Always run the full quality pipeline, not just individual checks
- Keep changes focused — don't scope-creep into "improvements" beyond the AC

### Git Context

Recent commits on develop:
- `b2b6713` docs(readme): rewrite with compliance gateway positioning
- `e7ab509` docs(security): add SECURITY.md and Apache-2.0 LICENSE
- `8553c4b` chore(deps-dev): bump griffe from 1.15.0 to 2.0.0
- `da9e10d` chore(deps-dev): update uv-build requirement from <0.10.0 to <0.11.0
- `f1e1103` chore(deps): bump the minor-and-patch group with 10 updates

Stale local branches to clean up (Task 7):
- `002-encryption-backend-protocol`
- `003-fernet-backend`
- `004-exception-hierarchy`
- `006-encrypted-session-service`
- `chore/bmad-github-tracking`
- `chore/pr-review-comments-rule`
- `feat/session-1-2-schema-version-reservation`
- `feat/session-1-3-configurationerror-startup-validation`

Conventional commit format for this story: `chore(ci): migrate to trunk-based development on main`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.10 — Trunk-Based Migration to Main]
- [Source: _bmad-output/planning-artifacts/architecture.md#CI/CD Pipeline Configuration — release-please and publish pipeline decisions]
- [Source: _bmad-output/project-context.md#Development Workflow Rules — branching, conventional commits, PR rules]
- [Source: _bmad-output/implementation-artifacts/1-9-readme-rewrite.md#Dev Notes — previous story patterns and learnings]
- [Source: .github/workflows/ci.yml — current CI trigger configuration]
- [Source: .github/workflows/release-please.yml — current release-please configuration]
- [Source: .github/workflows/docs.yml — current docs workflow (no branch changes needed)]
- [Source: release-please-config.json — release-please package configuration]
- [Source: .release-please-manifest.json — version manifest (branch-agnostic)]
- [Source: README.md — current badge and link references]
- [Source: CONTRIBUTING.md — current branch workflow instructions]
- [Source: docs/development-guide.md — current dev workflow documentation]

## Quality Gates

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors (src/ only)
- [x] `uv run pytest --cov=adk_secure_sessions --cov-fail-under=90` -- 167 passed, 99.68% coverage
- [x] `pre-commit run --all-files` -- all 7 hooks pass (actionlint validated workflow YAML)

## Code Review

- **Reviewer:** Code Review workflow (adversarial) + Party Mode consensus (Winston, Amelia, Bob, Murat)
- **Outcome:** Changes Requested → Fixed

### Findings Summary

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | HIGH | `.github/dependabot.yml` lines 9, 23 still targeted `develop` — missed in blast radius analysis | Fixed: both `target-branch` values changed to `"main"` |
| 2 | MEDIUM | No commits on branch — all changes unstaged | Acknowledged: commit after review (by design) |
| 3 | MEDIUM | Task 8.3 grep verification only checked changed files, not all candidate files (root cause of #1) | Fixed: Task 8.3 wording updated; repo-wide grep re-verified clean |
| 5 | LOW | `_bmad-output/project-context.md` still references `develop` | Fixed: Phase 2 subtask 6.6 added to regenerate |

### Verification

- [x] All HIGH findings resolved
- [x] All MEDIUM findings resolved or accepted
- [ ] Tests pass after review fixes
- [ ] Quality gates re-verified

## Change Log

| Date | Description |
|------|-------------|
| 2026-03-01 | Story created by create-story workflow |
| 2026-03-01 | Party mode review (Winston, Amelia, Bob, Murat): 5 consensus items applied. (1) Task 6 annotated with repo admin access requirement — may need manual user intervention. (2) Task 7 marked optional — branch cleanup not in AC. (3) Task 6.3 split into 6.3a (verify check names from CI run) and 6.3b (apply protection with verified names) — prevents silent misconfiguration. (4) Task 5.3 CLAUDE.md edit strategy documented — edit now, accept regeneration drift. (5) CI badge transition window explicitly documented as acceptable for pre-release library. |
| 2026-03-01 | Phase 1 implementation complete: Tasks 1-5 (config/doc changes) and Task 8 (quality gates) done. All 7 pre-commit hooks pass. 167 tests pass at 99.68% coverage. Tasks 6-7 (Phase 2: GitHub admin ops) remain for post-merge execution. |
| 2026-03-01 | Code review (adversarial + party mode consensus): 1 HIGH finding — `.github/dependabot.yml` missed in blast radius, both `target-branch` still `"develop"`. Fixed. Task 8.3 verification scope corrected to repo-wide grep. Phase 2 subtask 6.6 added (regenerate project-context.md). |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Phase 1 (Tasks 1-5, 8) complete — all file references migrated from `develop` to `main`
- Task 1: CI workflows updated — `ci.yml` triggers on `main` only, `release-please.yml` targets `main`
- Task 2: README.md badge and docs links updated to `main`
- Task 3: CONTRIBUTING.md branch instructions updated to `main`
- Task 4: docs/development-guide.md all branch references updated to `main`
- Task 5: `.claude/rules/pull-requests.md` and `.claude/rules/sonarqube.md` updated; CLAUDE.md had no `develop` references
- Task 8: All quality gates pass — 7/7 pre-commit hooks, 167 tests at 99.68% coverage
- Tasks 6-7 (Phase 2) deferred to post-merge — require GitHub admin access (create `main`, set default, apply protection)

### File List

**Modified:**
- `.github/workflows/ci.yml` — branch triggers from `[main, develop]` to `[main]`
- `.github/workflows/release-please.yml` — trigger and target-branch from `develop` to `main`
- `.github/dependabot.yml` — both `target-branch` values from `"develop"` to `"main"` [added by code review]
- `README.md` — CI badge `?branch=main`, docs links `/tree/main/docs`
- `CONTRIBUTING.md` — all `develop` branch references to `main`
- `docs/development-guide.md` — all `develop` branch references to `main`
- `.claude/rules/pull-requests.md` — PR target and diff references to `main`
- `.claude/rules/sonarqube.md` — merge target references to `main`

**Not modified (verified no changes needed):**
- `.github/workflows/docs.yml` — no branch filter
- `CLAUDE.md` — no `develop` references found
- `release-please-config.json` — no branch reference
- `.release-please-manifest.json` — branch-agnostic
