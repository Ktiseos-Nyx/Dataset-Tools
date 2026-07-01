export interface ImageMetadata {
  fileName: string
  fileSize: number
  fileType: string
  lastModified: string
  /** Hex SHA-256 of the raw file bytes (Civitai-style content hash). */
  sha256?: string
  width?: number
  height?: number
  exif: Record<string, unknown>
  iptc: Record<string, unknown>
  xmp: Record<string, unknown>
  ai: Record<string, unknown>
}

export type ViewMode = "thumbnail" | "list"
