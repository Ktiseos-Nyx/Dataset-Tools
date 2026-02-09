"use client"

import type React from "react"
import { Grid3x3, List, SidebarClose, SidebarOpen, FolderOpen } from "lucide-react"
import type { ViewMode } from "@/types/metadata"

interface NavbarProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  showMetadata: boolean
  onToggleMetadata: () => void
}

export function Navbar({ viewMode, onViewModeChange, showMetadata, onToggleMetadata }: NavbarProps) {
  return (
    <nav className="h-14 border-b border-border bg-card flex items-center justify-between px-4 gap-4">
      {/* Left: App Title */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <FolderOpen className="w-4 h-4 text-primary" />
          </div>
          <h1 className="text-lg font-semibold">Image Metadata Viewer</h1>
        </div>
      </div>

      {/* Center: View Mode Controls */}
      <div className="flex items-center gap-2 bg-muted rounded-lg p-1">
        <button
          onClick={() => onViewModeChange("thumbnail")}
          className={`p-2 rounded transition-colors ${
            viewMode === "thumbnail" ? "bg-background shadow-sm" : "hover:bg-background/50"
          }`}
          aria-label="Thumbnail view"
        >
          <Grid3x3 className="w-4 h-4" />
        </button>
        <button
          onClick={() => onViewModeChange("list")}
          className={`p-2 rounded transition-colors ${
            viewMode === "list" ? "bg-background shadow-sm" : "hover:bg-background/50"
          }`}
          aria-label="List view"
        >
          <List className="w-4 h-4" />
        </button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <div className="w-px h-6 bg-border" />

        <button
          onClick={onToggleMetadata}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
          aria-label={showMetadata ? "Hide metadata" : "Show metadata"}
        >
          {showMetadata ? <SidebarClose className="w-4 h-4" /> : <SidebarOpen className="w-4 h-4" />}
        </button>
      </div>
    </nav>
  )
}
