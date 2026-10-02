import { useSyncExternalStore } from 'react'

function subscribe(onStoreChange: () => void) {
  window.addEventListener('online', onStoreChange)
  window.addEventListener('offline', onStoreChange)

  return () => {
    window.removeEventListener('online', onStoreChange)
    window.removeEventListener('offline', onStoreChange)
  }
}

function getSnapshot() {
  return window.navigator.onLine
}

function getServerSnapshot() {
  return true
}

export function useIsOnline() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
