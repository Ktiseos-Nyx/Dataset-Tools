export interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  fontSize: 'sm' | 'md' | 'lg'
  showHiddenFiles: boolean
  showFileExtensions: boolean
  thumbnailSize: 'sm' | 'md' | 'lg'
  metadataPanelWidth: number
}

// Keys stored server-side in .env.local, not in JSON config
export interface ServerSecrets {
  civitaiApiKey?: string
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'system',
  fontSize: 'md',
  showHiddenFiles: false,
  showFileExtensions: true,
  thumbnailSize: 'md',
  metadataPanelWidth: 384,
}
