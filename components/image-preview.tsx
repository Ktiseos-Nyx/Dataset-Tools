"use client"

import { ZoomIn, ZoomOut, Maximize2, RefreshCw, Minimize2, RotateCw } from "lucide-react"
import { useState } from "react"

interface ImagePreviewProps {
  src: string
  fileName: string
  /** Reload the file list (e.g. after editing creates a new _edited.png). */
  onRefresh?: () => void
}

export function ImagePreview({ src, fileName, onRefresh }: ImagePreviewProps) {
  const [zoom, setZoom] = useState(0) // 0 = fit-to-container
  const [rotation, setRotation] = useState(0) // degrees: 0, 90, 180, 270

  const isFit = zoom === 0

  const rotate = () => setRotation((r) => (r + 90) % 360)

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
            onClick={rotate}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Rotate 90° clockwise"
            title={`Rotated ${rotation}°`}
          >
            <RotateCw className="w-4 h-4" />
          </button>
          {onRefresh && (
            <>
              <div className="w-px h-4 bg-border mx-1" />
              <button
                onClick={onRefresh}
                className="p-2 hover:bg-accent rounded-md transition-colors"
                aria-label="Refresh file list"
                title="Refresh file list (pick up newly edited files)"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Image Display */}
      <div className="flex-1 overflow-auto bg-muted/30 flex items-center justify-center p-4">
        {isFit ? (
          rotation === 0 ? (
            <img
              src={src || "/placeholder.svg"}
              alt={fileName}
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl border border-border"
            />
          ) : (
            <div
              className="max-w-full max-h-full transition-transform duration-200 flex items-center justify-center"
              style={{ transform: `rotate(${rotation}deg)` }}
            >
              <img
                src={src || "/placeholder.svg"}
                alt={fileName}
                className="max-w-full max-h-full object-contain rounded-lg shadow-2xl border border-border"
              />
            </div>
          )
        ) : (
          <div
            className="transition-transform duration-200"
            style={{ transform: `scale(${zoom / 100}) rotate(${rotation}deg)` }}
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
