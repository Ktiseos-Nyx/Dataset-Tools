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

export interface FileItem {
  id: string
  name: string
  size: number
  type: string
  lastModified: string
  url: string
  thumbnail: string
}

export type ViewMode = "thumbnail" | "list"
