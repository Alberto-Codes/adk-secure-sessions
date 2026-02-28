---
title: 'Clean up release-please configuration'
slug: 'release-please-cleanup'
created: '2026-02-28'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['release-please-action v4', 'GitHub Actions YAML', 'JSON config']
files_to_modify: ['.github/workflows/release-please.yml', 'release-please-config.json']
code_patterns: ['manifest-based release-please (config + manifest + workflow)', 'PAT token with GITHUB_TOKEN fallback', 'step id → job outputs pattern']
test_patterns: ['no automated tests — CI + manual verification']
---

# Tech-Spec: Clean up release-please configuration

**Created:** 2026-02-28

## Overview

### Problem Statement

The release-please configuration is implicit in places and missing outputs needed by the future publish pipeline (Issue #36). The workflow lacks an explicit `target-branch`, exposes no job outputs for downstream consumption, the refactoring changelog section is visible (cluttering user-facing changelogs), and the "Performance" section label is inconsistent with conventions.

### Solution

Make five surgical edits across two files to make the config explicit, forward-compatible with trunk migration (Issue #35), and wired for the publish pipeline (Issue #36).

### Scope

**In Scope:**

- Add `target-branch: develop` to the release-please workflow
- Add step `id: release` and expose job outputs (`release_created`, `tag_name`, `upload_url`)
- Hide refactoring section in changelog (`"hidden": true`)
- Rename "Performance" → "Performance Improvements" in changelog sections

**Out of Scope:**

- `.release-please-manifest.json` changes (version tracking — separate concern)
- `bump-minor-pre-major` / `bump-patch-for-minor-pre-major` settings (version policy — separate concern)
- Trunk-based migration (Issue #35)
- Publish pipeline wiring (Issue #36)

## Context for Development

### Codebase Patterns

- Release-please v4 action with manifest-based configuration
- Workflow triggers on push to `develop` branch
- Uses PAT token with GITHUB_TOKEN fallback for cross-workflow triggering
- Docvet project uses identical pattern — match its output format exactly
- Two-level output wiring: step outputs (`steps.release.outputs.*`) bubble up to job-level `outputs:` block

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `.github/workflows/release-please.yml` | Release-please workflow — add target-branch, step id, job outputs |
| `release-please-config.json` | Changelog sections config — hide refactoring, rename performance |
| `.release-please-manifest.json` | Version manifest — DO NOT MODIFY |

### Technical Decisions

- **Match docvet's output pattern exactly** — reduces cognitive overhead when comparing configs during trunk migration
- **Leave manifest and bump settings untouched** — out of scope, version-policy decisions
- **Step id must be `release`** — outputs reference `steps.release.outputs.*`
- **`outputs:` block before `steps:`** — GitHub Actions convention for YAML readability

## Implementation Plan

### Tasks

- [x] Task 1: Add step `id: release` to the release-please action step
  - File: `.github/workflows/release-please.yml`
  - Action: Add `id: release` to the `Run release-please` step (after `- name: Run release-please`)
  - Notes: Step-level anchor — must exist before job-level outputs can reference it. Bottom-up wiring order.

- [x] Task 2: Add job-level `outputs` block to release-please workflow
  - File: `.github/workflows/release-please.yml`
  - Action: Add `outputs:` block between `runs-on: ubuntu-latest` and `steps:`, mapping three outputs: `release_created`, `tag_name`, `upload_url` — each referencing `${{ steps.release.outputs.<name> }}`
  - Notes: Job-level consumer of Task 1's step outputs. Without the step `id`, these resolve to empty strings silently.

- [x] Task 3: Add `target-branch: develop` to the release-please action
  - File: `.github/workflows/release-please.yml`
  - Action: Add `target-branch: develop` inside the `with:` block, after `token:`
  - Notes: Makes the target branch explicit. Currently implicit from the `on.push.branches` trigger.

- [x] Task 4: Rename "Performance" to "Performance Improvements" in changelog sections
  - File: `release-please-config.json`
  - Action: Change `"section": "Performance"` to `"section": "Performance Improvements"` on the `perf` type entry
  - Notes: Aligns with docvet convention.

- [x] Task 5: Hide refactoring section from changelog
  - File: `release-please-config.json`
  - Action: Add `"hidden": true` to the `refactor` type entry: `{ "type": "refactor", "section": "Code Refactoring", "hidden": true }`
  - Notes: Refactoring is not user-facing; clutters changelog.

### Acceptance Criteria

- [x] AC 1: Given the release-please workflow, when inspecting the `with:` block, then `target-branch: develop` is present
- [x] AC 2: Given the release-please workflow, when inspecting the step, then `id: release` is present on the release-please action step
- [x] AC 3: Given the release-please workflow, when inspecting the job definition, then `outputs:` block exposes `release_created`, `tag_name`, and `upload_url` referencing `steps.release.outputs.*`
- [x] AC 4: Given `release-please-config.json`, when inspecting the `perf` changelog section, then the section name is `"Performance Improvements"`
- [x] AC 5: Given `release-please-config.json`, when inspecting the `refactor` changelog section, then `"hidden": true` is set
- [x] AC 6: Given a push to `develop`, when release-please runs, then it still creates release PRs correctly (no regression) — **verified post-merge, not in PR review**

## Additional Context

### Dependencies

- None — standalone config cleanup
- Downstream: Issue #36 (publish pipeline) will consume the exposed job outputs

### Testing Strategy

- No automated tests — these are CI config files
- CI regression: merge to develop and verify release-please action still runs and creates release PRs
- Manual verification: inspect the workflow YAML and JSON config to confirm all five edits are present and syntactically correct

### Notes

- Closes GitHub Issue #34
- Party Mode consensus: five edit points confirmed across two files, scope locked
- High-risk item: if step `id` is missing but job `outputs` are defined, downstream workflows get empty strings silently — Tasks 1 and 2 must both be implemented
- Future consideration: when trunk migration (Issue #35) happens, `target-branch` changes from `develop` to `main`

## Review Notes

- Adversarial review completed
- Findings: 11 total, 0 fixed, 11 skipped (noise/out-of-scope)
- Resolution approach: skip (Party Mode consensus — all findings were either reviewer lacking context or valid-but-out-of-scope improvements)
