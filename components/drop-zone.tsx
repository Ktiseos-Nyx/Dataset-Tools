"use client"

import { useState, useEffect } from "react"
import { Upload } from "lucide-react"

interface DropZoneProps {
  onFileDrop: (file: File, folderPath?: string) => void
}

export function DropZone({ onFileDrop }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  // Listen for drag events on the window - doesn't block clicks
  useEffect(() => {
    let dragCount = 0

    const onDragEnter = (e: DragEvent) => {
      e.preventDefault()
      dragCount++
      if (dragCount === 1) setIsDragging(true)
    }

    const onDragLeave = (e: DragEvent) => {
      e.preventDefault()
      dragCount--
      if (dragCount === 0) setIsDragging(false)
    }

    const onDragOver = (e: DragEvent) => {
      e.preventDefault() // Required to allow drop
    }

    const onDrop = (e: DragEvent) => {
      e.preventDefault()
      dragCount = 0
      setIsDragging(false)
    }

    window.addEventListener('dragenter', onDragEnter)
    window.addEventListener('dragleave', onDragLeave)
    window.addEventListener('dragover', onDragOver)
    window.addEventListener('drop', onDrop)

    return () => {
      window.removeEventListener('dragenter', onDragEnter)
      window.removeEventListener('dragleave', onDragLeave)
      window.removeEventListener('dragover', onDragOver)
      window.removeEventListener('drop', onDrop)
    }
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return

    const file = files[0]

    // Check if it's an image
    if (!file.type.startsWith('image/')) {
      console.warn('Not an image file:', file.type)
      return
    }

    // Try to get the folder path directly from the file
    // Works in Electron and some environments
    const filePath = (file as any).path as string | undefined
    let folderPath: string | undefined

    if (filePath && (filePath.includes('\\') || filePath.includes('/'))) {
      const sep = filePath.includes('\\') ? '\\' : '/'
      folderPath = filePath.substring(0, filePath.lastIndexOf(sep))
    }

    onFileDrop(file, folderPath)
  }

  return (
    <>
      {/* Drop overlay - shows when dragging, handles all events */}
      {isDragging && (
        <div
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center gap-4 text-muted-foreground pointer-events-none">
            <Upload className="w-16 h-16" />
            <div className="text-xl font-semibold">Drop an image to browse its folder</div>
            <div className="text-sm">The app will load all images from the same directory</div>
          </div>
        </div>
      )}

      {/* Global drag detection via window events */}
    </>
  )
}
