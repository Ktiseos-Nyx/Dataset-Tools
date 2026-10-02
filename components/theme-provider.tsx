'use client'

import * as React from 'react'
import {
  ThemeProvider as NextThemesProvider,
  useTheme,
  type ThemeProviderProps,
} from 'next-themes'
import { syncElectronTheme } from '@/lib/electron-bridge'

function ElectronThemeSync() {
  const { resolvedTheme } = useTheme()

  React.useEffect(() => {
    if (resolvedTheme === 'dark' || resolvedTheme === 'light') {
      syncElectronTheme(resolvedTheme)
    }
  }, [resolvedTheme])

  return null
}

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider {...props}>
      <ElectronThemeSync />
      {children}
    </NextThemesProvider>
  )
}
