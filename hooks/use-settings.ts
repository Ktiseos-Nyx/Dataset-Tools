import { useState, useEffect, useCallback } from 'react'
import { type AppSettings, DEFAULT_SETTINGS } from '@/types/settings'
import { getSettings, saveSettings } from '@/lib/settings'

const STORAGE_KEY = 'app-settings'

// In-tab broadcast: notify all useSettings() hooks when settings change
let listeners: Array<() => void> = []

function notifyAll() {
  for (const fn of listeners) fn()
}

export function useSettings() {
  const [settings, setSettingsState] = useState<AppSettings>(DEFAULT_SETTINGS)

  // Load initial + subscribe to same-tab and cross-tab changes
  useEffect(() => {
    // Load from localStorage on mount
    setSettingsState(getSettings())

    // Same-tab listener
    const refresh = () => setSettingsState(getSettings())
    listeners.push(refresh)

    // Cross-tab listener
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) refresh()
    }
    window.addEventListener('storage', onStorage)

    return () => {
      listeners = listeners.filter(l => l !== refresh)
      window.removeEventListener('storage', onStorage)
    }
  }, [])

  const updateSettings = useCallback((updates: Partial<AppSettings>) => {
    const current = getSettings()
    const next = { ...current, ...updates }
    saveSettings(next)
    // Notify ALL hooks in this tab (including this one)
    notifyAll()
  }, [])

  return { settings, updateSettings }
}
