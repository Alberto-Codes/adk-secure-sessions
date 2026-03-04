---
title: 'Docs Site Branding and Polish'
slug: 'docs-branding-polish'
created: '2026-03-04'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: [mkdocs-material, css-custom-properties, svg]
files_to_modify: [mkdocs.yml, docs/index.md, docs/stylesheets/theme.css, docs/assets/logo.svg, docs/assets/favicon.svg]
code_patterns: [docvet-branding-pattern, material-css-custom-properties, material-palette-toggle]
test_patterns: [mkdocs-build-strict]
---

# Tech-Spec: Docs Site Branding and Polish

**Created:** 2026-03-04

## Overview

### Problem Statement

The docs site uses stock mkdocs-material defaults — no custom palette, no logo/favicon, broken edit pencil links, no badges, no social links, and a stale hardcoded version. For a security/encryption library targeting regulated industries, visual polish signals trustworthiness. Sister project docvet has full custom branding; we should match that level of quality.

### Solution

Add custom branding (deep navy + teal/cyan palette, geometric lock icon SVG, dark mode as default), fix the broken edit_uri, add landing page badges, add social footer links, and remove the stale extra.version config.

### Scope

**In Scope:**
- #103 — Fix `edit_uri` missing `docs/` prefix (broken edit pencil icons)
- #104 — Custom branding: palette (navy + teal), logo SVG, favicon SVG, dark mode default
- #105 — Add badges to docs landing page (PyPI, CI, coverage, Python, license, Ruff, docvet)
- #111 — Social footer links (GitHub, PyPI)
- #110 — Remove stale `extra.version: "0.1.0"` from mkdocs.yml

**Out of Scope:**
- Glossary page (#106)
- Backend comparison guide (#107)
- Content changes to any existing doc pages beyond index.md badges
- New documentation pages
- Any Python code or test changes

## Context for Development

### Codebase Patterns

- mkdocs-material theme with extensive plugin configuration (mkdocstrings, gen-files, literate-nav, macros, glightbox, minify, git-revision-date-localized)
- docvet sister project is the reference pattern: custom `theme.css` with CSS custom properties for both dark/light schemes, SVG logo/favicon, slate-first palette, social links, font declarations
- No existing `docs/assets/` or `docs/stylesheets/` directories — both must be created
- `mkdocs build --strict` is the quality gate (enforced in CI via docs.yml)
- `docs/index.md` landing page uses Material grid cards (`<div class="grid cards" markdown>`) — badges go above this, after H1

### Files to Modify/Create

| File | Action | Purpose |
| ---- | ------ | ------- |
| `mkdocs.yml` | Modify | Palette (slate first), edit_uri fix, logo/favicon paths, extra_css, social links, font, new features, remove extra.version |
| `docs/index.md` | Modify | Add 7 badge images after H1, before tagline |
| `docs/stylesheets/theme.css` | Create | CSS custom properties for dark + light palettes, admonitions, code highlights |
| `docs/assets/logo.svg` | Create | Geometric lock icon, teal stroke on transparent |
| `docs/assets/favicon.svg` | Create | Same lock icon, teal stroke on navy rounded-rect background |

### Technical Decisions

- **Accent color (dark):** `#00bcd4` (Material Cyan 500)
- **Accent color (light):** `#00838f` (Cyan 800)
- **Header/tabs:** `#16213e` / `#1a2744` — shared with docvet for project family cohesion
- **Dark background:** `#141b2d`
- **Light background:** `#fafaf8`
- **Code background (dark):** `#0f1520`
- **Code background (light):** `#f0f4f5`
- **Dark headings:** `#e0f7fa` (Cyan 50)
- **Dark mode default:** Slate scheme listed first in palette array
- **Palette entries:** Remove `primary` and `accent` keys — CSS custom properties handle all colors
- **Fonts:** Roboto / Roboto Mono (match docvet)
- **Lock icon:** Geometric padlock — body rectangle + shackle arc + keyhole dot. viewBox 0 0 32 32

### SVG Asset Specifications

**Logo (`docs/assets/logo.svg`) — teal on transparent:**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <path d="M11 14V10a5 5 0 0 1 10 0v4" fill="none"
        stroke="#00bcd4" stroke-width="2" stroke-linecap="round"/>
  <rect x="9" y="14" width="14" height="12" rx="2" fill="none"
        stroke="#00bcd4" stroke-width="2"/>
  <circle cx="16" cy="20" r="1.5" fill="#00bcd4"/>
</svg>
```

**Favicon (`docs/assets/favicon.svg`) — teal lock on navy background:**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#16213e"/>
  <path d="M11 14V10a5 5 0 0 1 10 0v4" fill="none"
        stroke="#00bcd4" stroke-width="2" stroke-linecap="round"/>
  <rect x="9" y="14" width="14" height="12" rx="2" fill="none"
        stroke="#00bcd4" stroke-width="2"/>
  <circle cx="16" cy="20" r="1.5" fill="#00bcd4"/>
</svg>
```

### Admonition Color Specifications

| Admonition | Dark border | Dark bg | Light border | Light bg |
|---|---|---|---|---|
| tip | `#00bcd4` | `rgba(0, 188, 212, 0.1)` | `#00838f` | `rgba(0, 131, 143, 0.08)` |
| warning | `#ffab40` | `rgba(255, 171, 64, 0.1)` | `#e65100` | `rgba(230, 81, 0, 0.08)` |
| info | `#7b8cde` | `rgba(123, 140, 222, 0.1)` | `#4a5a9e` | `rgba(74, 90, 158, 0.08)` |

## Implementation Plan

### Tasks

- [x] Task 1: Create SVG assets
  - Prerequisite: Create `docs/assets/` directory (`mkdir -p docs/assets`)
  - File: `docs/assets/logo.svg` (create)
  - Action: Write the logo SVG from the specification above — teal lock on transparent
  - File: `docs/assets/favicon.svg` (create)
  - Action: Write the favicon SVG from the specification above — teal lock on navy rounded-rect

- [x] Task 2: Create custom theme CSS
  - Prerequisite: Create `docs/stylesheets/` directory (`mkdir -p docs/stylesheets`)
  - File: `docs/stylesheets/theme.css` (create)
  - Action: Create CSS file following docvet's pattern with these scoped sections:
    - `[data-md-color-scheme="slate"]` — dark mode: bg `#141b2d`, header `#16213e`, tabs `#1a2744`, accent `#00bcd4`, link color `#00bcd4`, code bg `#0f1520`, code highlight `rgba(0, 188, 212, 0.15)`, headings `#e0f7fa`, search input bg `#252547`, header topic `font-weight: 700`, footer `#0f1520` / `#0a0f1a`
    - `[data-md-color-scheme="default"]` — light mode: bg `#fafaf8`, lighter variants, header `#16213e`, tabs `#1a2744`, accent `#00838f`, link color `#00838f`, code bg `#f0f4f5`, code highlight `rgba(0, 131, 143, 0.15)`, search input bg `#e8eef0`, footer `#0f1520` / `#0a0f1a` (same as dark — navy footer in both modes), header topic `font-weight: 700`
    - Dark + light admonitions: tip, warning, info (use colors from Admonition Color Specifications table). Only these three types are custom-styled; all other admonition types (note, danger, example, etc.) keep Material defaults.
    - Dark mode card hover: `border-color: rgba(0, 188, 212, 0.4)`
    - Dark + light code line highlights (`.highlight .hll`)

- [x] Task 3: Update mkdocs.yml
  - File: `mkdocs.yml` (modify)
  - Action — edit_uri (line 6): Change `edit/HEAD/` to `edit/HEAD/docs/`
  - Action — theme section: Add `logo: assets/logo.svg`, `favicon: assets/favicon.svg`, `font:` block (Roboto / Roboto Mono)
  - Action — features: Add `navigation.instant`, `navigation.footer`, `content.code.annotate` to existing features list
    - **Risk note:** `navigation.instant` can conflict with `macros` or `glightbox` plugins in some mkdocs-material versions. If `mkdocs build --strict` fails after adding it, remove `navigation.instant` first as the likely culprit.
  - Action — palette: Reorder so `slate` scheme is first (dark default). Remove `primary` and `accent` keys from both entries. Complete palette YAML:
    ```yaml
    palette:
      - scheme: slate
        toggle:
          icon: material/brightness-4
          name: Switch to light mode
      - scheme: default
        toggle:
          icon: material/brightness-7
          name: Switch to dark mode
    ```
  - Action — extra_css: Add `extra_css: [stylesheets/theme.css]` as a new top-level key immediately after the closing of the `theme:` block and before `plugins:`
  - Action — extra section: Remove `version: "0.1.0"`, preserve `project_name: adk-secure-sessions`, add `social:` block:
    ```yaml
    extra:
      project_name: adk-secure-sessions
      social:
        - icon: fontawesome/brands/github
          link: https://github.com/Alberto-Codes/adk-secure-sessions
        - icon: fontawesome/brands/python
          link: https://pypi.org/project/adk-secure-sessions/
    ```
  - Notes: Preserve all existing features, plugins, markdown_extensions, nav, copyright, not_in_nav

- [x] Task 4: Add badges to docs landing page
  - File: `docs/index.md` (modify)
  - Action: Insert 7 badge lines between the `# adk-secure-sessions` H1 heading and the `**Encrypted session storage for Google ADK**` tagline. Same badges as README.md (copy the 7 `[![...](...)` lines), same order:
    1. CI status
    2. Coverage (Codecov)
    3. PyPI version
    4. Python versions
    5. License
    6. Ruff
    7. docs vetted (docvet)
  - Notes: Add a blank line after H1, then the 7 badge lines (no blank lines between them), then a blank line before the tagline

- [x] Task 5: Verify build
  - Action: Run `uv run mkdocs build --strict` — must pass with zero errors
  - Action: Run `pre-commit run --all-files` — must pass

### Acceptance Criteria

- [ ] AC 1: Given the docs site is built, when a user clicks the edit pencil icon on any page, then the link resolves to the correct file path on GitHub (e.g., `edit/HEAD/docs/getting-started.md`). **Verify:** inspect generated HTML for correct `edit_uri` paths.
- [ ] AC 2: Given the docs site loads in a browser, when dark mode is the default, then the page renders with deep navy background (`#141b2d`), teal accent links, and navy header. **Verify:** visual post-deploy.
- [ ] AC 3: Given the docs site loads, when the user toggles to light mode, then the page renders with warm white background (`#fafaf8`), darker teal accent, and navy header. **Verify:** visual post-deploy.
- [ ] AC 4: Given the docs site loads, when the user views the browser tab, then a teal lock favicon on navy background is visible. **Verify:** visual post-deploy.
- [ ] AC 5: Given the docs site loads, when the user views the nav header, then a teal lock logo is visible next to the site name. **Verify:** visual post-deploy.
- [ ] AC 6: Given the docs landing page loads, when the user views the page, then 7 badge images are visible between the title and tagline (CI, Coverage, PyPI, Python, License, Ruff, docs vetted). **Verify:** `mkdocs build --strict` (catches broken image refs) + visual post-deploy.
- [ ] AC 7: Given the docs site loads, when the user scrolls to the footer, then GitHub and PyPI social icons with links are visible. **Verify:** visual post-deploy.
- [ ] AC 8: Given the docs site is built, when `mkdocs build --strict` runs, then it completes with zero errors and zero warnings. **Verify:** CI gate.
- [ ] AC 9: Given the mkdocs.yml extra section, when inspected, then no `version` key exists (stale `"0.1.0"` removed). **Verify:** grep `mkdocs.yml` for `version`.
- [ ] AC 10: Given the docs site loads in dark mode, when an admonition (tip, warning, or info) is rendered, then it uses the custom teal/amber/blue-gray colors instead of Material defaults. **Verify:** visual post-deploy.

## Additional Context

### Dependencies

- mkdocs-material (already installed, includes Roboto fonts and FontAwesome icons)
- No new pip dependencies required

### Testing Strategy

- `uv run mkdocs build --strict` — catches broken refs, missing assets, YAML errors
- `pre-commit run --all-files` — lint/format checks on all files
- Visual verification after deploy via `workflow_dispatch` — check dark/light toggle, favicon, logo, badges, social links, edit pencil links, admonition colors
- No Python tests needed — zero code changes

### Notes

- Branch already created: `feat/docs-branding-and-polish`
- Closes: #103, #104, #105, #110, #111
- Deploy via `workflow_dispatch` after merge to verify live
- CSS follows docvet pattern: scope all custom properties under `[data-md-color-scheme="slate"]` and `[data-md-color-scheme="default"]` selectors
- Task order is dependency-driven: SVGs first (referenced by mkdocs.yml), CSS second (referenced by mkdocs.yml), mkdocs.yml third (wires everything together), badges fourth (independent), verify last

## Review Notes

- Adversarial review completed
- Findings: 3 total, 2 fixed, 1 accepted risk
- Resolution approach: party-mode consensus
- F1 (Medium, Real): Light-mode accent darkened `#00838f` → `#007c85` for WCAG AA (4.76:1)
- F2 (Low, Real): Dead `.tabbed-labels` selectors removed (pymdownx.tabbed not enabled)
- F3 (Low, Accepted): `navigation.instant` + `glightbox` runtime risk — no current `<img>` elements trigger it
