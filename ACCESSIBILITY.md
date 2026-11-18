# Accessibility Statement

Dataset Tools is a local-first desktop/web application for viewing and editing image metadata (AI generation parameters and camera EXIF). This statement describes what we currently do for accessibility, what we haven't tested, and how to report a barrier. **It is documentation, not a conformance claim** — we name our gaps rather than overstate our support.

## Priorities and goals

* [ ] **Maintainer to fill in — UX priorities.** Current draft: the app's core audience interacts with dense visual metadata panels, so our near-term goals are (1) keyboard operability for the main browse → view → edit flow, (2) visible focus states on all interactive controls, and (3) readable contrast across all 7 accent themes and dark mode. Specific targets still being decided.

## What we already have

* **User-adjustable font size** and **thumbnail size** in the settings panel.
* **7 accent color themes** (zinc, red, orange, green, blue, violet, pink) plus dark mode — users can pick what reads best for them. Themes use the OKLch color space for perceptually consistent contrast.
* Text-based metadata output: every panel presents prompts, parameters, and tags as selectable text, not just images.

## Supported environments

| Environment | Status |
| :--- | :--- |
| Windows desktop build (installer / portable) | Supported, primary test target |
| Linux AppImage | Supported (Nov 2026); desktop-integration details under test |
| macOS | No Electron build planned; CLI/web install works in a browser |
| Browsers | Chrome/Edge recommended (File System Access API powers local folder browsing); other browsers fall back to drag-and-drop |
| Screen readers | **Not tested — no claims made** |
| Keyboard-only operation | **Not systematically tested** |

## Known limitations

* The interface is heavily pointer-driven (file tree, drag-and-drop, click-to-inspect). Keyboard use works through the basics — every file row and thumbnail tile is a real focusable button, and menus/dialogs use Radix primitives with built-in arrow-key and Escape support — but there is no arrow-key navigation *within* the file grid: keyboard users tab through files one button at a time.
* File selection is conveyed visually only (a background-color change) — screen readers are not currently told which file is selected (`aria-selected`/`aria-pressed` not set on file items).
* The metadata panels are dense, visually-layered tables — we have not yet verified how screen readers announce them.
* Some icon-only toolbar buttons rely on `title` attributes rather than `aria-label`.
* Drag-and-drop is the primary import gesture in some flows; equivalents exist (folder picker, file picker) but aren't documented as accessibility alternatives yet.
* No formal WCAG audit has been performed. We name WCAG as a direction, not a claim.

## Reporting a barrier

Open a [GitHub issue](https://github.com/Ktiseos-Nyx/Dataset-Tools/issues/new) with the **`accessibility`** label (or just describe the problem — we'll label it). To help us reproduce, it's useful if you can share the affected screen/flow, your browser or build version, and your OS — but **you never need to disclose a disability, and screenshots or recordings are always optional.** Plain descriptions are enough.

## How reports are handled

1. Acknowledged in the issue thread by a maintainer.
2. Trialed/triaged against the known limitations above and tracked openly in the issue.
3. Fixes or workarounds land as normal PRs; we update this statement when a limitation is resolved or a new one is found.

## Contributor expectations

For changes that touch UI flows, we ask that contributors (human or coding agent) check at minimum:

* Keyboard reachability of any new interactive element (tab order, focus visibility)
* Contrast of new colors against both light and dark themes
* Text alternatives for anything conveyed by icon alone

Agents working in this repo should follow the conventions in `AGENTS.md`; UI-affecting changes go through PR review (including the third-party review pass).

## Ownership and maintenance

Maintained by the Duskfall Portal Crew ([@duskfallcrew](https://github.com/duskfallcrew)). This statement is reviewed whenever a supported environment changes, a known limitation is fixed, or a user report contradicts something written here.

*Last updated: November 2026.*
