export type AccentColor = 'zinc' | 'red' | 'orange' | 'green' | 'blue' | 'violet' | 'pink'

export interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  accentColor: AccentColor
  fontSize: 'sm' | 'md' | 'lg'
  showHiddenFiles: boolean
  showFileExtensions: boolean
  thumbnailSize: 'sm' | 'md' | 'lg'
  metadataPanelWidth: number
  sortBy: 'name' | 'date' | 'size'
  currentFolder: string  // Folder to browse (defaults to project root)
}

// Keys stored server-side in .env.local, not in JSON config
export interface ServerSecrets {
  civitaiApiKey?: string
  githubToken?: string
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'system',
  accentColor: 'zinc',
  fontSize: 'md',
  showHiddenFiles: false,
  showFileExtensions: true,
  thumbnailSize: 'md',
  metadataPanelWidth: 384,
  sortBy: 'name',
  currentFolder: '.',  // Project root by default
}
