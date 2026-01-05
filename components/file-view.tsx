"use client"

import type React from "react"

import { FileImage, Upload } from "lucide-react"
import type { FileItem, ViewMode } from "@/types/metadata"
import { useCallback } from "react"

interface FileViewProps {
  files: FileItem[]
  viewMode: ViewMode
  onFileSelect: (file: FileItem) => void
  onFilesAdded: (files: File[]) => void
}

export function FileView({ files, viewMode, onFileSelect, onFilesAdded }: FileViewProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      const droppedFiles = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith("image/"))
      if (droppedFiles.length > 0) {
        onFilesAdded(droppedFiles)
      }
    },
    [onFilesAdded],
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }, [])

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
    return (bytes / (1024 * 1024)).toFixed(1) + " MB"
  }

  if (files.length === 0) {
    return (
      <div onDrop={handleDrop} onDragOver={handleDragOver} className="h-full flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
            <Upload className="w-8 h-8 text-primary" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No Files Loaded</h3>
          <p className="text-muted-foreground mb-4">
            Drop your images here or use the "Add Files" button to get started
          </p>
          <p className="text-sm text-muted-foreground">Supported formats: JPEG, PNG, WebP, TIFF, and more</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-10 border-b border-border px-4 flex items-center justify-between bg-muted/20">
        <h2 className="text-sm font-medium">
          {files.length} {files.length === 1 ? "file" : "files"}
        </h2>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {viewMode === "thumbnail" ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {files.map((file) => (
              <button
                key={file.id}
                onClick={() => onFileSelect(file)}
                className="group relative aspect-square rounded-lg overflow-hidden border border-border hover:border-primary transition-colors bg-muted"
              >
                <img
                  src={file.thumbnail || "/placeholder.svg"}
                  alt={file.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="absolute bottom-0 left-0 right-0 p-2">
                    <p className="text-xs text-white font-medium truncate">{file.name}</p>
                    <p className="text-xs text-white/70">{formatFileSize(file.size)}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            {files.map((file) => (
              <button
                key={file.id}
                onClick={() => onFileSelect(file)}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors group text-left"
              >
                <div className="w-10 h-10 rounded overflow-hidden border border-border flex-shrink-0 bg-muted">
                  <img
                    src={file.thumbnail || "/placeholder.svg"}
                    alt={file.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(file.size)} • {new Date(file.lastModified).toLocaleDateString()}
                  </p>
                </div>
                <FileImage className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
