import { useState, useEffect, useCallback } from 'react'
import { type AppSettings, DEFAULT_SETTINGS } from '@/types/settings'
import { getSettings, saveSettings } from '@/lib/settings'

const STORAGE_KEY = 'app-settings'

export function useSettings() {
  const [settings, setSettingsState] = useState<AppSettings>(DEFAULT_SETTINGS)

  useEffect(() => {
    setSettingsState(getSettings())

    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setSettingsState(getSettings())
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const updateSettings = useCallback((updates: Partial<AppSettings>) => {
    setSettingsState(prev => {
      const next = { ...prev, ...updates }
      saveSettings(next)
      return next
    })
  }, [])

  return { settings, updateSettings }
}
