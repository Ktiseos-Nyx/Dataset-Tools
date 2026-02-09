"use client"

import { ZoomIn, ZoomOut, Maximize2, RotateCw, Minimize2 } from "lucide-react"
import { useState } from "react"

interface ImagePreviewProps {
  src: string
  fileName: string
}

export function ImagePreview({ src, fileName }: ImagePreviewProps) {
  const [zoom, setZoom] = useState(0) // 0 = fit-to-container
  const [rotation, setRotation] = useState(0)

  const isFit = zoom === 0

  return (
    <div className="h-full flex flex-col">
      {/* Preview Header */}
      <div className="h-12 flex items-center justify-between px-4 border-b border-border bg-muted/20">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{fileName}</p>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom(isFit ? 100 : Math.max(25, zoom - 25))}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Zoom out"
            disabled={!isFit && zoom <= 25}
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-sm font-mono text-muted-foreground min-w-[4ch] text-center px-2">
            {isFit ? "Fit" : `${zoom}%`}
          </span>
          <button
            onClick={() => setZoom(isFit ? 150 : Math.min(400, zoom + 25))}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Zoom in"
            disabled={!isFit && zoom >= 400}
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(isFit ? 100 : 0)}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label={isFit ? "Actual size" : "Fit to view"}
          >
            {isFit ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
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
        {isFit ? (
          <img
            src={src || "/placeholder.svg"}
            alt={fileName}
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl border border-border transition-transform duration-200"
            style={{ transform: rotation ? `rotate(${rotation}deg)` : undefined }}
          />
        ) : (
          <div
            className="transition-transform duration-200"
            style={{
              transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
            }}
          >
            <img
              src={src || "/placeholder.svg"}
              alt={fileName}
              className="max-w-none rounded-lg shadow-2xl border border-border"
            />
          </div>
        )}
      </div>
    </div>
  )
}
