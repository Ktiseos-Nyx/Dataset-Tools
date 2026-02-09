export interface ImageMetadata {
  fileName: string
  fileSize: number
  fileType: string
  lastModified: string
  exif: Record<string, unknown>
  iptc: Record<string, unknown>
  xmp: Record<string, unknown>
  ai: Record<string, unknown>
}

export type ViewMode = "thumbnail" | "list"
