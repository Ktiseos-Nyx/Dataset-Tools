"use client"

import { useRef, useState, useCallback } from "react"
import { Upload, ImageIcon } from "lucide-react"

interface UploadZoneProps {
  onFileDrop: (file: File) => void
}

export function UploadZone({ onFileDrop }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dragCount = useRef(0)

  const processFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return
    onFileDrop(file)
  }, [onFileDrop])

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCount.current++
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCount.current--
    if (dragCount.current <= 0) {
      dragCount.current = 0
      setIsDragging(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCount.current = 0
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) processFile(files[0])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      processFile(files[0])
      e.target.value = ""
    }
  }

  return (
    <>
      <div
        className={`flex-1 flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl m-4 transition-all cursor-pointer ${
          isDragging
            ? "border-primary bg-primary/5 scale-[1.02]"
            : "border-border hover:border-muted-foreground/50 hover:bg-muted/10"
        }`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <div className="flex flex-col items-center gap-4 text-center max-w-sm pointer-events-none">
          <div className={`p-4 rounded-full ${isDragging ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"} transition-colors`}>
            {isDragging ? <Upload className="w-10 h-10" /> : <ImageIcon className="w-10 h-10" />}
          </div>
          <div>
            <p className="text-lg font-semibold">
              {isDragging ? "Drop your image here" : "Drop an image or click to browse"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Supports PNG, JPEG, and WebP with AI generation metadata
            </p>
          </div>
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={handleFileSelect}
      />
    </>
  )
}
