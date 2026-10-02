import { contextBridge, ipcRenderer } from 'electron';

// The surface exposed to the renderer as `window.electronAPI`.
// Keep this minimal and typed to match lib/electron-bridge.ts.
const api = {
  pickFolder: (): Promise<string | null> => ipcRenderer.invoke('dialog:pickFolder'),
  setTheme: (theme: 'dark' | 'light') => ipcRenderer.send('theme:set', theme),
  watchFolder: (dir: string): Promise<void> => ipcRenderer.invoke('fs:watch', dir),
  onFsChange: (callback: () => void): (() => void) => {
    const listener = () => callback();
    ipcRenderer.on('fs:change', listener);
    return () => {
      ipcRenderer.removeListener('fs:change', listener);
    };
  },
};

contextBridge.exposeInMainWorld('electronAPI', api);
