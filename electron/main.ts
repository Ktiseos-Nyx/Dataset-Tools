import { app, BrowserWindow, dialog, ipcMain, nativeTheme, shell, type OpenDialogOptions } from 'electron';
import { spawn, type ChildProcess } from 'child_process';
import * as path from 'path';
import * as http from 'http';
import * as net from 'net';
import * as fs from 'fs';

const DEV_URL = 'http://localhost:3000';

// Native window background must be a hex value (not an OKLCH CSS function).
// These match the app theme in globals.css: oklch(0.145 0 0) / oklch(1 0 0).
const DARK_BG = '#0a0a0a';
const LIGHT_BG = '#ffffff';

let nextProcess: ChildProcess | null = null;
let mainWindow: BrowserWindow | null = null;
let fsWatcher: fs.FSWatcher | null = null;
let serverPort: number | null = null;

function debounce<T extends (...args: unknown[]) => void>(fn: T, ms: number): (...args: Parameters<T>) => void {
  let timer: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

function getFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once('error', reject);
    srv.listen(0, () => {
      const address = srv.address();
      srv.close(() => {
        if (address && typeof address === 'object') resolve(address.port);
        else reject(new Error('Could not allocate a free port'));
      });
    });
  });
}

function waitForServer(url: string, timeout = 30_000): Promise<void> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      const req = http.get(url, (res) => {
        if (res.statusCode !== undefined && res.statusCode < 500) {
          resolve();
        } else {
          retry();
        }
      });
      req.on('error', retry);
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

// `electron . --self-serve` runs the built app (`next start`) without a dev
// server — no Turbopack watcher, near-zero steady-state disk I/O. Use it after
// a one-time `npm run build` to test the shell without `next dev` churn.
const SELF_SERVE = process.argv.includes('--self-serve');

/**
 * In a packaged app, spawn the production Next.js server on a free port and
 * hand it the per-user data dir so secrets/cache land outside the read-only
 * install dir. In dev, the server is already running under `next dev`.
 */
async function startNextServer(port: number): Promise<void> {
  // The self-contained server lives in `.next/standalone` in dev, and is copied
  // to `resources/standalone` (electron-builder extraResources) when packaged.
  const standaloneDir = app.isPackaged
    ? path.join(process.resourcesPath, 'standalone')
    : path.join(__dirname, '..', '.next', 'standalone');

  // Run the standalone build's self-contained server through Electron's own
  // Node runtime (ELECTRON_RUN_AS_NODE) so the packaged app doesn't depend on
  // a system Node/npx installation. The standalone server reads PORT + HOSTNAME
  // from the environment (defaults to 0.0.0.0, so HOSTNAME is pinned explicitly
  // to keep the server off the network).
  nextProcess = spawn(
    process.execPath,
    [path.join(standaloneDir, 'server.js')],
    {
      cwd: standaloneDir,
      env: {
        ...process.env,
        ELECTRON_RUN_AS_NODE: '1',
        NODE_ENV: 'production',
        PORT: String(port),
        HOSTNAME: '127.0.0.1',
        ELECTRON_USER_DATA: app.getPath('userData'),
      },
      stdio: 'inherit',
    }
  );

  nextProcess.on('error', (err) => {
    console.error('[electron] Failed to start Next.js server:', err);
  });

  await waitForServer(`http://127.0.0.1:${port}`);
}

async function createWindow(): Promise<void> {
  let url = DEV_URL;

  if (app.isPackaged || SELF_SERVE) {
    if (serverPort === null) {
      serverPort = await getFreePort();
      await startNextServer(serverPort);
    }
    url = `http://127.0.0.1:${serverPort}`;
  }

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'Dataset Tools',
    autoHideMenuBar: true,
    backgroundColor: nativeTheme.shouldUseDarkColors ? DARK_BG : LIGHT_BG,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(url);

  mainWindow.webContents.setWindowOpenHandler(({ url: target }) => {
    try {
      const parsed = new URL(target);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        shell.openExternal(target);
      }
    } catch {
      // ignore malformed or disallowed URLs — only http/https are opened
    }
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  ipcMain.handle('dialog:pickFolder', async () => {
    const options: OpenDialogOptions = { properties: ['openDirectory'] };
    const result = mainWindow
      ? await dialog.showOpenDialog(mainWindow, options)
      : await dialog.showOpenDialog(options);
    if (result.canceled || result.filePaths.length === 0) return null;
    return result.filePaths[0];
  });

  // Keep the native window background in sync with the OS theme. The renderer
  // also reports its resolved theme via `theme:set` (handles in-app toggles
  // that differ from the OS setting).
  nativeTheme.on('updated', () => {
    mainWindow?.setBackgroundColor(nativeTheme.shouldUseDarkColors ? DARK_BG : LIGHT_BG);
  });

  ipcMain.on('theme:set', (_event, theme: 'dark' | 'light') => {
    mainWindow?.setBackgroundColor(theme === 'light' ? LIGHT_BG : DARK_BG);
  });

  // Watch a folder for changes and notify the renderer so the file tree can
  // auto-refresh (B5). Uses Node's built-in fs.watch — zero dependencies, and
  // recursive watching works on Windows under Electron's Node 22.
  ipcMain.handle('fs:watch', async (_event, dir: unknown) => {
    if (fsWatcher) {
      fsWatcher.close();
      fsWatcher = null;
    }
    if (typeof dir !== 'string' || dir.length === 0) return;
    try {
      const notify = debounce(() => {
        mainWindow?.webContents.send('fs:change');
      }, 300);
      fsWatcher = fs.watch(dir, { recursive: true }, notify);
      fsWatcher.on('error', () => {
        fsWatcher?.close();
        fsWatcher = null;
      });
    } catch (err) {
      console.error('[electron] fs.watch failed:', err);
    }
  });

  try {
    await createWindow();
  } catch (err) {
    console.error('[electron] Failed to create window:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    nextProcess?.kill();
    app.quit();
  }
  // On macOS the app stays in the dock — keep the Next server running so
  // re-activating reuses it (createWindow reuses serverPort) instead of
  // spawning a fresh server per activation.
});

app.on('activate', () => {
  if (mainWindow === null) void createWindow();
});

app.on('before-quit', () => {
  fsWatcher?.close();
  fsWatcher = null;
  nextProcess?.kill();
});
