# Security Policy for Dataset-Tools

Hello! We're Ktiseos Nyx, and we take the security of Dataset-Tools seriously. As an open-source project, we believe in transparency and welcome the community's help in keeping our software safe. If you think you've found a security vulnerability, please let us know!

## Our Commitment

* We aim to address security vulnerabilities in a timely manner, prioritizing them based on their potential impact.
* We will be transparent about vulnerabilities and our efforts to fix them, following responsible disclosure practices.
* We strive to use secure coding practices and keep our dependencies up-to-date.

## Supported Versions & Development Status

Dataset-Tools is under active development.

* **Currently Supported Version:** The `main` branch always represents the latest development version and is the primary focus for new features, bug fixes, and security updates. We encourage all users to use the latest state of the `main` branch.
* **Release Tags (Future):** As we begin to make formal releases (e.g., v0.6.0, v1.0.0), we will clearly define which tagged releases are actively supported with security patches. For now, `main` is key.
* **Older Development States/Branches:** Branches or tags representing development states significantly older than the current `main` (e.g., pre-v0.58 series or unmaintained feature branches) are considered unsupported and may not receive security updates.

We are committed to providing security support for the current development version (`main` branch) and will define support for tagged releases as they are made.

## Reporting a Vulnerability

Found a security issue? Thank you for helping us! Please report it to us **privately** so we can address it before it becomes public knowledge.

**🔒 Preferred Method: GitHub Security Advisories**
This is the best and most secure way:

1. Go to the "Security" tab of the [Dataset-Tools GitHub repository](https://github.com/Ktiseos-Nyx/Dataset-Tools).
2. Click on "Advisories."
3. Click "New draft security advisory."
This creates a private space for us to discuss and fix the issue.

**⚠️ Please DO NOT open a regular public GitHub issue for security vulnerabilities.**

**Alternative Reporting Methods (if GitHub Advisories aren't possible):**

* Open a [GitHub Discussion](https://github.com/Ktiseos-Nyx/Dataset-Tools/discussions) to reach a maintainer for guidance on private disclosure.

**What to Include in Your Report:**
To help us understand and fix the issue quickly, please include:

* A clear description of the vulnerability.
* Steps to reproduce it (be as detailed as possible).
* Which version/branch of Dataset-Tools is affected.
* The potential impact if the vulnerability is exploited.
* Any proof-of-of-concept code (if you have it and it's safe to share).
* Your environment details (OS, Node.js/Electron version, app version) if relevant.

We'll do our best to acknowledge your report within 48-72 hours. As an independent project, timelines for fixes will vary based on complexity and severity, but we are committed to addressing confirmed vulnerabilities.

## How the Local App Is Hardened

Dataset-Tools is a **local-first** application: the server binds to loopback
(127.0.0.1) and the filesystem routes are designed for a single user on their
own machine. The relevant layers:

* **Loopback binding, enforced in every launch path.** `next dev` runs with
  `-H 127.0.0.1` (dev + Electron dev), the packaged Electron app spawns its
  server with `HOSTNAME: '127.0.0.1'`, and the standalone build is pinned to
  loopback by a postbuild rewrite plus a start wrapper that neutralizes ambient
  `HOSTNAME` inheritance. Deliberate non-loopback deployments require an
  explicitly-named override (`DT_HOSTNAME`).
* **Filesystem routes are desktop-only.** `/api/fs`, `/api/image`, `/api/metadata`,
  `/api/thumbnail`, `/api/metadata-write` and `/api/safetensors` all validate a
  loopback-only Host/Origin (defense-in-depth — a Host header is
  client-controlled) and confine paths with `path.relative` containment
  (shared helper: `lib/fs-guard.ts`). On any public web deployment these routes
  refuse every request with 403 by design; the Vercel demo parses in-browser.
* **Outbound HTTP is allowlisted.** All server-side requests funnel through
  `lib/safe-fetch.ts` (civitai.com, api.github.com, raw.githubusercontent.com
  only), with a matching renderer CSP in `next.config.mjs` — a hostile image's
  embedded metadata can't steer the app to arbitrary domains.
* **The write surface is tiny.** The only write route is `/api/metadata-write`:
  PNG-only, must target an existing file, containment + symlink re-checks, and
  its CSRF gate requires an exact loopback Origin match.
* **Packaging integrity.** The Electron app ships as a fused ASAR with
  embedded ASAR integrity validation; only the app bundle is tamper-checked,
  and native dependencies ship outside it via `extraResources`.

Residual risks we accept and track are listed in
[SECURITY_TODO.md](SECURITY_TODO.md) — notably that another local process
under the same user account can reach the loopback endpoints, same as it could
reach any local app.

### About browser extensions

A browser extension with content-script permissions can inject into any page
the user opens — including a page served from localhost. No web application
can prevent that; it is inherent to how extension permissions work, and it is
true of every local web app (dev servers, routers, etc.), not just this one.
The practical exposure is limited to what the page itself shows, and the app
never serves secrets on those pages.

### About code signing

The Windows EXE is currently **unsigned**. Code signing attests to who built
a binary — it does not make the code more secure — and signing services gate on
download-reputation, which a young open-source project hasn't accumulated yet.
The README documents what the SmartScreen warning means and how to verify a
release (VirusTotal link, open-source build). Signing is a 1.0 milestone
decision, not a magic security fix.

## Our Security Practices

* **Code Review:** Every change lands via pull request and is reviewed — including by AI reviewers (CodeRabbit, DeepScan, SafeDep dependency scanning, Aikido SAST on dedicated branches) as well as humans.
* **Dependency Management:** We keep third-party libraries up to date using:
  * **`npm audit`** for the Node.js/Next.js + Electron toolchain. Transitive dependencies are pinned via `overrides` in `package.json`, and production dependencies (`npm audit --omit=dev`) are kept at **0 known vulnerabilities**.
  * **GitHub's Dependabot alerts** to notify us of vulnerable dependencies.
* **Static Analysis:** **TypeScript** (`tsc --noEmit`) type-checks the codebase, and ESLint enforces code quality across the Next.js/Electron source.
* **Dev-chain advisories.** Findings that exist only in build/lint tooling (never in the shipped app bundle) are assessed as audit noise, accepted, and monitored until upstream ships an in-range fix.

> **Known accepted advisory:** `braces` (CVE-2026-93687) currently flags as high severity through the dev-only ESLint toolchain (`eslint-config-next` → `fast-glob` → `micromatch` → `braces`). There is no patched release yet (affects all versions up to and including 3.0.3), and it never ships in the installer — it's a build-time linter dependency only. We'll drop the pin/override once upstream publishes a fix.

* **Vendored Code:** Code vendored from other projects (like components from `sd-prompt-reader`) is included with clear attribution and its original license. We take on the responsibility of maintaining or updating these components as needed within our project. See our `NOTICE.md` file for details.

We are always looking to improve our security posture and appreciate community feedback on our practices.

## Licensing

Dataset-Tools is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**. The full text of this license can be found in the [LICENSE](LICENSE) file in the root of this repository.

Our use of any third-party libraries or vendored code is done in compliance with their respective licenses (details in `NOTICE.md`).

---
