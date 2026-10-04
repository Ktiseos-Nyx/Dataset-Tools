import { contextBridge, ipcRenderer, webUtils } from 'electron';

// The surface exposed to the renderer as `window.electronAPI`.
// Keep this minimal and typed to match lib/electron-bridge.ts.
const api = {
  pickFolder: (): Promise<string | null> => ipcRenderer.invoke('dialog:pickFolder'),
  setTheme: (theme: 'dark' | 'light') => ipcRenderer.send('theme:set', theme),
  // `File.path` was removed from Electron 32+; `webUtils.getPathForFile` is the
  // replacement. Exposed here so the renderer can recover a dropped file's
  // absolute path without nodeIntegration.
  getPathForFile: (file: File): string => webUtils.getPathForFile(file),
};

contextBridge.exposeInMainWorld('electronAPI', api);
