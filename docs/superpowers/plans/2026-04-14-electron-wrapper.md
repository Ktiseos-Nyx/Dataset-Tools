# Electron Wrapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap the existing Next.js app in Electron so it ships as a native desktop app (.exe / .dmg / .AppImage) without changing any existing app code.

**Architecture:** Electron's main process spawns the Next.js server as a child process, waits for it to be ready on localhost:3000, then opens a BrowserWindow pointing at it. The app code is completely unchanged — Electron is a thin shell. electron-builder packages everything into a self-contained installer.

**Tech Stack:** Electron 34+, electron-builder 25+, wait-on (dev dependency only for the dev workflow), TypeScript for the main process.

---

## The "Will Windows Call This a Virus?" section

Short answer: not if you handle it right. Here's what actually happens:

**Unsigned exe:** Windows SmartScreen shows "Windows protected your PC." Users can click *More info → Run anyway*. Fine for personal use or early testers who trust you.

**Self-signed cert:** Slightly better message, still a warning. Not worth the effort over just staying unsigned for now.

**EV (Extended Validation) code signing cert:** Warning goes away completely. Costs ~$300–500/year from DigiCert or Sectigo. Worth it before any public release.

**The plan below gets you a working exe first. Code signing is Task 8 — you can skip it until you're ready to share publicly.**

---

## File Structure

```
electron/
  main.ts          — Electron entry point: spawns Next.js, opens BrowserWindow
  preload.ts       — (empty for now, required by Electron security model)
electron-builder.yml  — Package config: icons, targets, what to bundle
package.json          — modified: new scripts, electron as devDep
```

No existing files are modified.

---

### Task 1: Install Electron dependencies

**Files:**
- Modify: `package.json` (devDependencies only)

- [ ] **Step 1: Install packages**

```bash
npm install --save-dev electron electron-builder
```

- [ ] **Step 2: Verify install**

```bash
npx electron --version
```

Expected output: `v34.x.x` (or whatever current is)

- [ ] **Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: add electron and electron-builder dev dependencies"
```

---

### Task 2: Create the Electron main process

**Files:**
- Create: `electron/main.ts`
- Create: `electron/preload.ts`

- [ ] **Step 1: Create the preload script (empty but required)**

Create `electron/preload.ts`:

```typescript
// Preload runs in a sandboxed context between main and renderer.
// Empty for now — add contextBridge calls here later if needed.
```

- [ ] **Step 2: Create the main process**

Create `electron/main.ts`:

```typescript
import { app, BrowserWindow, shell } from 'electron';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as http from 'http';

const PORT = 3000;
const DEV_URL = `http://localhost:${PORT}`;

let nextProcess: ChildProcess | null = null;
let mainWindow: BrowserWindow | null = null;

function waitForServer(url: string, timeout = 30000): Promise<void> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      http.get(url, res => {
        if (res.statusCode && res.statusCode < 500) {
          resolve();
        } else {
          retry();
        }
      }).on('error', retry);
    };
    const retry = () => {
      if (Date.now() - start > timeout) {
        reject(new Error(`Next.js server did not start within ${timeout}ms`));
        return;
      }
      setTimeout(check, 500);
    };
    check();
  });
}

function startNextServer(): Promise<void> {
  return new Promise((resolve, reject) => {
    // In production, next is bundled — run `next start` from the app resources dir
    const isProd = app.isPackaged;
    const projectRoot = isProd
      ? path.join(process.resourcesPath, 'app')
      : path.join(__dirname, '..');

    nextProcess = spawn(
      process.platform === 'win32' ? 'npx.cmd' : 'npx',
      ['next', 'start', '--port', String(PORT)],
      {
        cwd: projectRoot,
        env: { ...process.env, NODE_ENV: 'production' },
        stdio: 'inherit',
      }
    );

    nextProcess.on('error', reject);

    // Wait until the server is actually accepting connections
    waitForServer(DEV_URL).then(resolve).catch(reject);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'Dataset Tools',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(DEV_URL);

  // Open external links in the system browser, not inside the app
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

app.whenReady().then(async () => {
  try {
    await startNextServer();
    createWindow();
  } catch (err) {
    console.error('Failed to start Next.js server:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  nextProcess?.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) createWindow();
});

app.on('before-quit', () => {
  nextProcess?.kill();
});
```

- [ ] **Step 3: Commit**

```bash
git add electron/main.ts electron/preload.ts
git commit -m "feat(electron): add main process and preload script"
```

---

### Task 3: Add TypeScript config for the Electron folder

**Files:**
- Create: `electron/tsconfig.json`

The root `tsconfig.json` targets the browser/Next.js. Electron's main process is Node.js — it needs its own config.

- [ ] **Step 1: Create `electron/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "../.electron",
    "rootDir": ".",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": ["."]
}
```

- [ ] **Step 2: Install Electron types**

```bash
npm install --save-dev @types/electron
```

(If `@types/electron` doesn't resolve, Electron 34+ ships its own types — skip this step if `npx tsc --project electron/tsconfig.json` passes without it.)

- [ ] **Step 3: Test compile**

```bash
npx tsc --project electron/tsconfig.json --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add electron/tsconfig.json package.json package-lock.json
git commit -m "chore(electron): add tsconfig for main process"
```

---

### Task 4: Wire up npm scripts

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Add scripts to `package.json`**

Add these to the `"scripts"` block:

```json
"electron:compile": "tsc --project electron/tsconfig.json",
"electron:dev": "npm run build && npm run electron:compile && concurrently \"npm run dev\" \"wait-on http://localhost:3000 && electron .electron/main.js\"",
"electron:build": "npm run build && npm run electron:compile && electron-builder"
```

- [ ] **Step 2: Install concurrently and wait-on**

```bash
npm install --save-dev concurrently wait-on
```

- [ ] **Step 3: Verify scripts exist**

```bash
npm run --list 2>/dev/null | grep electron
```

Expected: shows `electron:compile`, `electron:dev`, `electron:build`

- [ ] **Step 4: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore(electron): add dev and build scripts"
```

---

### Task 5: Configure electron-builder

**Files:**
- Create: `electron-builder.yml`

- [ ] **Step 1: Create `electron-builder.yml`**

```yaml
appId: com.ktiseos-nyx.dataset-tools
productName: Dataset Tools
copyright: "Copyright © 2025 The Duskfall Portal Crew"

# What gets bundled into the app
files:
  - .next/**/*
  - public/**/*
  - electron/**/*
  - .electron/**/*
  - app/**/*
  - lib/**/*
  - types/**/*
  - hooks/**/*
  - components/**/*
  - node_modules/**/*
  - package.json
  - next.config.mjs

directories:
  output: dist
  buildResources: build

# Electron entry point (compiled from electron/main.ts)
main: .electron/main.js

win:
  target:
    - target: nsis
      arch: [x64]
  icon: build/icon.ico   # 256x256 .ico — create this before building

mac:
  target:
    - target: dmg
      arch: [x64, arm64]
  icon: build/icon.icns  # macOS icon — create this before building
  category: public.app-category.productivity

linux:
  target:
    - target: AppImage
      arch: [x64]
  icon: build/icon.png   # 512x512 .png

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
```

- [ ] **Step 2: Create placeholder icon directory**

```bash
mkdir -p build
```

You need real icons before Task 7. For now just make the directory. Icon requirements:
- `build/icon.ico` — Windows, 256×256 minimum
- `build/icon.icns` — macOS (can convert from png with `iconutil`)
- `build/icon.png` — Linux, 512×512

Free tool to generate all three from one source PNG: **https://www.icoconverter.com** and **Image2icon** (Mac).

- [ ] **Step 3: Commit**

```bash
git add electron-builder.yml build/.gitkeep
git commit -m "chore(electron): add electron-builder config"
```

---

### Task 6: Test the dev workflow

No build needed — this just verifies the Electron window opens and loads the app.

- [ ] **Step 1: Run the dev mode**

```bash
npm run electron:dev
```

Expected: Next.js dev server starts, then an Electron window opens and loads the app at localhost:3000.

- [ ] **Step 2: Verify the file browser works**

Open a folder using the inline path input added earlier. Confirm images load, metadata panel shows, workflow tab works.

- [ ] **Step 3: Verify external links open in browser**

Click any external link (e.g. a GitHub repo link in the ComfyUI nodes section). It should open in your system browser, not inside the Electron window.

- [ ] **Step 4: Close the window**

Confirm the Next.js process also exits (no orphan node processes in Task Manager / Activity Monitor).

---

### Task 7: Build a test executable

Do this after Task 6 is confirmed working and you have icons in `build/`.

- [ ] **Step 1: Run the build**

```bash
npm run electron:build
```

Expected: `dist/` directory is created containing:
- Windows: `dist/Dataset Tools Setup x.x.x.exe`
- Mac: `dist/Dataset Tools-x.x.x.dmg`
- Linux: `dist/Dataset-Tools-x.x.x.AppImage`

- [ ] **Step 2: Test the installer**

Run the generated `.exe` (Windows) or `.dmg` (Mac). Install it. Open it. Verify:
- App window opens
- File browser works
- No console errors (open DevTools with `Ctrl+Shift+I` / `Cmd+Option+I`)

- [ ] **Step 3: Check for orphan processes on close**

After closing the app, check Task Manager (Windows) or Activity Monitor (Mac) — no `node` or `next` processes should remain.

- [ ] **Step 4: Commit**

```bash
git add electron-builder.yml build/
git commit -m "chore(electron): verified build produces working installer"
```

---

### Task 8: Trust signals for public release (OSS-friendly approach)

**Skip this task until you're ready to share publicly.**

The honest picture on Windows SmartScreen:
- **Unsigned** = "Windows protected your PC" warning. Users click *More info → Run anyway*. Totally fine for OSS.
- **Standard OV cert** = still warns on first download. Microsoft changed rules in 2023. OV no longer suppresses SmartScreen.
- **EV cert** = suppresses SmartScreen immediately but costs $300–500/year. Not worth it for OSS.
- **Reputation** = SmartScreen backs off automatically as more people download your app over time, even unsigned.

**The practical OSS path:**

- [ ] **Add a VirusTotal scan to every GitHub Release**

After building, upload the `.exe` to https://www.virustotal.com and paste the results link in the release notes. This is the community trust standard — most OSS users check VT before running an unfamiliar exe.

```markdown
## Downloads
- [Dataset-Tools-Setup-1.0.0.exe](link)

**VirusTotal scan:** [0/72 — clean](virustotal-link)
```

- [ ] **Add SmartScreen instructions to the README**

```markdown
## Windows Installation Note
Windows may show a "Windows protected your PC" warning on first launch.
This happens because the app isn't commercially signed (common for OSS).

To install:
1. Click **More info**
2. Click **Run anyway**

You can verify the binary is safe: [VirusTotal scan results](link)
```

- [ ] **Optional free tier: SignPath.io**

SignPath offers free code signing for open source projects (https://signpath.io/). It's an OV cert (not EV) so SmartScreen still warns on first install, but it builds reputation faster than unsigned and integrates with GitHub Actions. Apply at their site with your repo link.

- [ ] **Mac: Apple Developer account ($99/year)**

Required for notarization — without it macOS Gatekeeper blocks the app entirely (stricter than Windows). If Mac support matters to you this one is unavoidable. electron-builder handles notarization via its `afterSign` hook once you have the account.

---

### Task 9: Settings and userData migration (skip until after Task 7 works)

Right now `.env.local` and `.cache/` live next to the project. That works in dev but breaks in a packaged app where the install directory is read-only.

- [ ] **Move settings storage to `app.getPath('userData')`**

In `electron/main.ts`, before spawning Next.js, set an env var:

```typescript
const userDataPath = app.getPath('userData');
process.env.ELECTRON_USER_DATA = userDataPath;
```

- [ ] **Update the settings API route** (`app/api/settings/route.ts`) to check for `process.env.ELECTRON_USER_DATA` and store settings there when running under Electron.

- [ ] **Update the GitHub search cache** (`lib/comfyui-github-search.ts`) similarly — write cache to `path.join(process.env.ELECTRON_USER_DATA, 'comfyui-github-search.json')` when the env var is set.

- [ ] **For `GITHUB_TOKEN`**: surface a Settings field in the UI (already exists) that writes to a `config.json` in userData instead of `.env.local`.

---

## Known Limitations (not blocking)

- **App bundle size will be large** (~300–500MB) because `node_modules` is bundled. This is normal for Electron apps. electron-builder's `asar` packaging compresses it somewhat.
- **Cold start is slow** (~5–10 seconds) because Next.js has to compile on first launch. A production build (`next build` before packaging) helps a lot — the `electron:build` script already does this.
- **Port 3000 conflicts**: if the user already has something on port 3000, the app won't open. Future improvement: pick a random available port.
