import { contextBridge, ipcRenderer } from 'electron';

// The surface exposed to the renderer as `window.electronAPI`.
// Keep this minimal and typed to match lib/electron-bridge.ts.
const api = {
  pickFolder: (): Promise<string | null> => ipcRenderer.invoke('dialog:pickFolder'),
};

contextBridge.exposeInMainWorld('electronAPI', api);
