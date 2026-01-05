"use client"

import type React from "react"

import { useCallback } from "react"
import { Upload, ImageIcon } from "lucide-react"

interface ImageUploadProps {
  onImageSelect: (file: File) => void
}

export function ImageUpload({ onImageSelect }: ImageUploadProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      const file = e.dataTransfer.files[0]
      if (file && file.type.startsWith("image/")) {
        onImageSelect(file)
      }
    },
    [onImageSelect],
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }, [])

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        onImageSelect(file)
      }
    },
    [onImageSelect],
  )

  return (
    <div onDrop={handleDrop} onDragOver={handleDragOver} className="relative w-full max-w-2xl">
      <input
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        id="file-upload"
      />

      <div className="border-2 border-dashed border-border hover:border-primary/50 rounded-xl p-12 text-center bg-card transition-colors">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/10 blur-xl rounded-full" />
            <div className="relative bg-primary/5 p-6 rounded-2xl">
              <Upload className="w-12 h-12 text-primary" />
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-semibold text-foreground">Drop your image here</h3>
            <p className="text-sm text-muted-foreground">or click to browse your files</p>
          </div>

          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-2">
            <div className="flex items-center gap-1.5">
              <ImageIcon className="w-4 h-4" />
              <span>JPEG, PNG, WebP, TIFF</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
