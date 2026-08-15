import { useSyncExternalStore, useCallback } from 'react'
import { type AppSettings, DEFAULT_SETTINGS } from '@/types/settings'
import { getSettings, saveSettings } from '@/lib/settings'

const STORAGE_KEY = 'app-settings'

// In-tab broadcast: notify all useSettings() hooks when settings change
let listeners: Array<() => void> = []
let snapshot: AppSettings = getSettings()

function notifyAll() {
  snapshot = getSettings()
  for (const fn of listeners) fn()
}

function subscribe(onChange: () => void): () => void {
  listeners.push(onChange)
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) {
      snapshot = getSettings()
      onChange()
    }
  }
  window.addEventListener('storage', onStorage)
  return () => {
    listeners = listeners.filter(l => l !== onChange)
    window.removeEventListener('storage', onStorage)
  }
}

function getSnapshot(): AppSettings {
  return snapshot
}

function getServerSnapshot(): AppSettings {
  return DEFAULT_SETTINGS
}

export function useSettings() {
  const settings = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  const updateSettings = useCallback((updates: Partial<AppSettings>) => {
    const current = getSettings()
    const next = { ...current, ...updates }
    saveSettings(next)
    // Notify ALL hooks in this tab (including this one)
    notifyAll()
  }, [])

  return { settings, updateSettings }
}
