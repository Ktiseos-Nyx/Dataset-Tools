# npm Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish Dataset Tools to npm so users can run it locally via `npx @ktiseos-nyx/dataset-tools` or `npm install -g @ktiseos-nyx/dataset-tools` — no Electron, no signing, no friction.

**Architecture:** A small CLI entry script checks for a production build, builds if missing, starts `next start` on a configurable port, and opens the browser automatically. The package publishes source (not the built `.next` dir — too large) and builds on first run via `postinstall`. Subsequent runs just start the already-built server.

**Tech Stack:** npm, Next.js CLI (`next build` / `next start`), `open` (auto-open browser), scoped npm package `@ktiseos-nyx/dataset-tools`.

---

## How it works for the user

```bash
# Try it without installing anything
npx @ktiseos-nyx/dataset-tools

# Or install globally for regular use (builds once, starts fast every time)
npm install -g @ktiseos-nyx/dataset-tools
dataset-tools
```

First run: downloads package, runs `next build` (~1-2 minutes), opens browser.
Every run after: starts in a few seconds.

---

## File Structure

```
bin/
  dataset-tools.js    — CLI entry point: checks build, starts server, opens browser
package.json          — modified: name, bin, files, engines, dependencies
.npmignore            — exclude dev-only files from the published package
```

---

### Task 1: Check the npm package name

- [ ] **Step 1: Check if the name is available**

```bash
npm view @ktiseos-nyx/dataset-tools 2>&1
```

Expected if available: `npm error 404 Not Found - GET https://registry.npmjs.org/@ktiseos-nyx%2fdataset-tools`

Expected if taken: shows package info. If taken, try `@ktiseos-nyx/dataset-tools` or `@ktiseos-nyx/comfyui-metadata-viewer`.

- [ ] **Step 2: Create an npm account if needed**

Go to https://www.npmjs.com/signup. Use the `ktiseos-nyx` org or personal account — scoped packages (`@ktiseos-nyx/`) require the org to exist on npm.

```bash
npm login
# follow prompts
npm whoami
# should print your username
```

- [ ] **Step 3: Create the npm org (if using scoped package)**

Go to https://www.npmjs.com/org/create and create `ktiseos-nyx` org. Free for public packages.

---

### Task 2: Create the CLI entry script

**Files:**
- Create: `bin/dataset-tools.js`

- [ ] **Step 1: Install the `open` package**

```bash
npm install open
```

`open` launches the default browser cross-platform (Windows, Mac, Linux).

- [ ] **Step 2: Create `bin/dataset-tools.js`**

```js
#!/usr/bin/env node

import { execSync, spawn } from 'child_process';
import { existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');
const port = process.env.PORT || 3737;
const url = `http://localhost:${port}`;

// Build if no production build exists yet
if (!existsSync(join(projectRoot, '.next', 'BUILD_ID'))) {
  console.log('Building Dataset Tools for first run (this takes a minute)...');
  try {
    execSync('npx next build', { cwd: projectRoot, stdio: 'inherit' });
  } catch {
    console.error('Build failed. Check the output above.');
    process.exit(1);
  }
}

console.log(`Starting Dataset Tools at ${url}`);

const server = spawn(
  process.platform === 'win32' ? 'npx.cmd' : 'npx',
  ['next', 'start', '--port', String(port)],
  { cwd: projectRoot, stdio: 'inherit' }
);

server.on('error', err => {
  console.error('Failed to start server:', err.message);
  process.exit(1);
});

// Wait a moment for the server to be ready then open the browser
setTimeout(async () => {
  const { default: open } = await import('open');
  open(url);
}, 2500);

// Clean shutdown
process.on('SIGINT', () => {
  server.kill();
  process.exit(0);
});
process.on('SIGTERM', () => {
  server.kill();
  process.exit(0);
});
```

- [ ] **Step 3: Make it executable**

```bash
chmod +x bin/dataset-tools.js
```

On Windows this does nothing, but it's needed for Mac/Linux.

- [ ] **Step 4: Commit**

```bash
git add bin/dataset-tools.js
git commit -m "feat: add CLI entry script for npm distribution"
```

---

### Task 3: Update package.json

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Check current package.json name and version**

```bash
cat package.json | grep -E '"name"|"version"|"private"'
```

- [ ] **Step 2: Update the relevant fields**

Add/update these fields in `package.json`:

```json
{
  "name": "@ktiseos-nyx/dataset-tools",
  "version": "0.1.0",
  "description": "Image metadata viewer and analyzer for AI-generated images. Supports A1111, ComfyUI, NovelAI, and more.",
  "private": false,
  "type": "module",
  "bin": {
    "dataset-tools": "./bin/dataset-tools.js"
  },
  "files": [
    "app",
    "components",
    "lib",
    "hooks",
    "types",
    "public",
    "bin",
    "next.config.mjs",
    "tailwind.config.ts",
    "postcss.config.mjs",
    "tsconfig.json",
    "components.json"
  ],
  "engines": {
    "node": ">=18.0.0"
  },
  "keywords": [
    "comfyui",
    "stable-diffusion",
    "a1111",
    "novelai",
    "metadata",
    "exif",
    "ai-image",
    "image-viewer"
  ],
  "homepage": "https://github.com/Ktiseos-Nyx/Dataset-Tools",
  "repository": {
    "type": "git",
    "url": "https://github.com/Ktiseos-Nyx/Dataset-Tools.git"
  },
  "license": "MIT"
}
```

> **Note:** Keep all existing `dependencies` and `devDependencies` as-is. Only add/change the fields listed above. `next`, `react`, and all runtime deps must stay in `dependencies` (not `devDependencies`) since they're needed when the user installs the package.

- [ ] **Step 3: Verify next is in dependencies not devDependencies**

```bash
cat package.json | grep -A3 '"dependencies"' | grep '"next"'
```

If `next` is missing from `dependencies`, move it:
```bash
npm install next
```

- [ ] **Step 4: Commit**

```bash
git add package.json
git commit -m "chore: configure package.json for npm publishing"
```

---

### Task 4: Create .npmignore

**Files:**
- Create: `.npmignore`

This keeps the published package lean — no test files, no CI config, no local cache.

- [ ] **Step 1: Create `.npmignore`**

```
# Dev / local only
.env.local
.env*.local
.cache/
.next/
node_modules/

# Docs and planning
docs/
*.md
!README.md

# CI / tooling
.github/
.vscode/
.claude/
*.log

# Python leftovers
__pycache__/
*.py
*.pyc
venv/
requirements*.txt

# Misc
dist/
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Verify what would be published**

```bash
npm pack --dry-run 2>&1 | head -60
```

Check the output — you should see `app/`, `components/`, `lib/`, `bin/`, `public/`, config files. You should NOT see `node_modules/`, `.next/`, `.env.local`, `.cache/`.

- [ ] **Step 3: Commit**

```bash
git add .npmignore
git commit -m "chore: add .npmignore for clean npm package"
```

---

### Task 5: Test locally before publishing

- [ ] **Step 1: Pack the package locally**

```bash
npm pack
```

This creates a `.tgz` file (e.g. `ktiseos-nyx-dataset-tools-0.1.0.tgz`) without publishing.

- [ ] **Step 2: Install it locally to test**

```bash
npm install -g ./ktiseos-nyx-dataset-tools-0.1.0.tgz
dataset-tools
```

Expected: build runs (first time), browser opens to `http://localhost:3737`, app loads.

- [ ] **Step 3: Test the file browser**

Open a folder using the inline path input. Confirm images load and metadata appears. This confirms the API routes work in production mode (`next start`).

- [ ] **Step 4: Test clean shutdown**

Press `Ctrl+C` in the terminal. Confirm the server stops and the terminal returns to prompt. No orphan Node processes.

- [ ] **Step 5: Clean up the test install**

```bash
npm uninstall -g @ktiseos-nyx/dataset-tools
rm ktiseos-nyx-dataset-tools-0.1.0.tgz
```

- [ ] **Step 6: Commit any fixes found during testing**

```bash
git add -A
git commit -m "fix: resolve issues found during local npm pack test"
```

---

### Task 6: Publish to npm

- [ ] **Step 1: Make sure you're logged in**

```bash
npm whoami
```

Should print your npm username. If not: `npm login`

- [ ] **Step 2: Publish (public scoped package)**

```bash
npm publish --access public
```

Scoped packages (`@org/name`) default to private — `--access public` makes it free and public.

- [ ] **Step 3: Verify it's live**

```bash
npm view @ktiseos-nyx/dataset-tools
```

Expected: shows package info with version, description, keywords.

- [ ] **Step 4: Test the published package**

```bash
npx @ktiseos-nyx/dataset-tools
```

Expected: builds and opens browser. If this works, shipping.

- [ ] **Step 5: Commit and tag the release**

```bash
git add package.json
git commit -m "chore: publish v0.1.0 to npm"
git tag v0.1.0
git push origin nextjs-rewrite --tags
```

---

### Task 7: Add install instructions to README

- [ ] **Step 1: Add to README.md**

Add a Usage / Installation section:

```markdown
## Installation

**Quick start (no install):**
```bash
npx @ktiseos-nyx/dataset-tools
```

**Install globally for regular use:**
```bash
npm install -g @ktiseos-nyx/dataset-tools
dataset-tools
```

First run builds the app (~1-2 min). Every run after starts in seconds.
Runs at `http://localhost:3737` — opens in your browser automatically.

**Default port:** 3737. Override with `PORT=8080 dataset-tools`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add npm installation instructions"
git push origin nextjs-rewrite
```

---

## Publishing updates later

When you make changes and want to push a new version:

```bash
npm version patch   # 0.1.0 → 0.1.1 (bug fix)
npm version minor   # 0.1.0 → 0.2.0 (new feature)
npm publish --access public
git push origin nextjs-rewrite --tags
```

---

## Notes

- **Port 3737** was chosen deliberately — unlikely to conflict with other common dev servers (3000, 4000, 8080, 8000, 5173)
- **`extension-node-map.json`** (ComfyUI node registry) — check its size with `ls -lh lib/extension-node-map.json`. If it's over 5MB consider fetching it at runtime instead of bundling it, as npm packages over ~20MB get slow to install
- **Homebrew custom tap** — once you hit 100 stars, point a Homebrew formula at the GitHub releases tarball. The formula is about 20 lines and lives in its own repo (`homebrew-dataset-tools`). No threshold needed for a custom tap.
