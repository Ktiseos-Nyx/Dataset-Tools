"use client"

import { ZoomIn, ZoomOut, Maximize2, RotateCw } from "lucide-react"
import { useState } from "react"

interface ImagePreviewProps {
  src: string
  fileName: string
}

export function ImagePreview({ src, fileName }: ImagePreviewProps) {
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)

  return (
    <div className="h-full flex flex-col">
      {/* Preview Header */}
      <div className="h-12 flex items-center justify-between px-4 border-b border-border bg-muted/20">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{fileName}</p>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom(Math.max(25, zoom - 25))}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Zoom out"
            disabled={zoom <= 25}
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-sm font-mono text-muted-foreground min-w-[4ch] text-center px-2">{zoom}%</span>
          <button
            onClick={() => setZoom(Math.min(400, zoom + 25))}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Zoom in"
            disabled={zoom >= 400}
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(100)}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Reset zoom"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <div className="w-px h-4 bg-border mx-1" />
          <button
            onClick={() => setRotation((rotation + 90) % 360)}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Rotate image"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Image Display */}
      <div className="flex-1 overflow-auto bg-muted/30 flex items-center justify-center p-4">
        <div
          className="transition-transform duration-200"
          style={{
            transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
          }}
        >
          <img
            src={src || "/placeholder.svg"}
            alt={fileName}
            className="max-w-full h-auto rounded-lg shadow-2xl border border-border"
          />
        </div>
      </div>
    </div>
  )
}
