/**
 * Electron bridge — the single seam the renderer uses to reach native
 * capabilities when running under Electron.
 *
 * In a browser `window.electronAPI` is undefined and every helper here
 * degrades gracefully, so the app keeps working on the web/Vercel demo
 * (drag-and-drop per image) without any special-casing at call sites.
 */

export interface ElectronAPI {
  /** Opens a native directory picker and resolves the absolute path, or null if cancelled. */
  pickFolder: () => Promise<string | null>
  /** Reports the app's resolved theme so the native window background can match. */
  setTheme: (theme: 'dark' | 'light') => void
  /** Starts watching a folder for changes (native side handles debouncing). */
  watchFolder: (dir: string) => Promise<void>
  /** Subscribes to file-system change events. Returns an unsubscribe function. */
  onFsChange: (callback: () => void) => () => void
}

export function getElectronAPI(): ElectronAPI | undefined {
  if (typeof window === 'undefined') return undefined
  return (window as { electronAPI?: ElectronAPI }).electronAPI
}

export function isElectron(): boolean {
  return getElectronAPI() !== undefined
}

/**
 * Open a native folder picker. Returns the absolute path, or null when the
 * user cancels or when running outside Electron (no bridge available).
 */
export async function pickFolder(): Promise<string | null> {
  const api = getElectronAPI()
  if (!api?.pickFolder) return null
  try {
    return await api.pickFolder()
  } catch {
    return null
  }
}

/**
 * Sync the native window's background color with the app theme. No-ops in the
 * browser (no native window to update).
 */
export function syncElectronTheme(theme: 'dark' | 'light') {
  const api = getElectronAPI()
  try {
    api?.setTheme?.(theme)
  } catch {
    // ignore — web/Vercel has no native window to sync
  }
}

/**
 * Tell the native side to watch a folder for changes (no-op outside Electron).
 * Replaces any previous watcher so there's only ever one active watch.
 */
export function watchFolder(dir: string) {
  if (!dir) return
  const api = getElectronAPI()
  try {
    api?.watchFolder?.(dir)
  } catch {
    // ignore — browser has no filesystem watcher
  }
}

/**
 * Subscribe to file-system change events. Returns an unsubscribe function
 * (a no-op outside Electron). Callers should re-subscribe whenever the watched
 * folder changes.
 */
export function onFsChange(callback: () => void): () => void {
  const api = getElectronAPI()
  try {
    return api?.onFsChange?.(callback) ?? (() => {})
  } catch {
    return () => {}
  }
}
