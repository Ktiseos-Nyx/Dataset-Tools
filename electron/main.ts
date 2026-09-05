import { app, BrowserWindow, dialog, ipcMain, nativeTheme, shell, type OpenDialogOptions } from 'electron';
import { spawn, type ChildProcess } from 'child_process';
import * as path from 'path';
import * as http from 'http';
import * as net from 'net';

const DEV_URL = 'http://localhost:3000';

// Native window background must be a hex value (not an OKLCH CSS function).
// These match the app theme in globals.css: oklch(0.145 0 0) / oklch(1 0 0).
const DARK_BG = '#0a0a0a';
const LIGHT_BG = '#ffffff';

let nextProcess: ChildProcess | null = null;
let mainWindow: BrowserWindow | null = null;

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
  const projectRoot = app.isPackaged
    ? path.join(process.resourcesPath, 'app')
    : path.join(__dirname, '..');

  // Run the bundled `next` CLI through Electron's own Node runtime
  // (ELECTRON_RUN_AS_NODE) so the packaged app doesn't depend on a system
  // Node/npx installation.
  nextProcess = spawn(
    process.execPath,
    ['node_modules/next/dist/bin/next', 'start', '--port', String(port), '--hostname', '127.0.0.1'],
    {
      cwd: projectRoot,
      env: {
        ...process.env,
        ELECTRON_RUN_AS_NODE: '1',
        NODE_ENV: 'production',
        PORT: String(port),
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
    const port = await getFreePort();
    await startNextServer(port);
    url = `http://127.0.0.1:${port}`;
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
    shell.openExternal(target);
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

  try {
    await createWindow();
  } catch (err) {
    console.error('[electron] Failed to create window:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  nextProcess?.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) void createWindow();
});

app.on('before-quit', () => {
  nextProcess?.kill();
});
