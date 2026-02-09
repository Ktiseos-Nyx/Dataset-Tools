"use client"

import { useState } from "react"
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels"
import { Grid3x3, List, SidebarClose, SidebarOpen, ImageIcon } from "lucide-react"
import { FileTree } from "@/components/file-tree"
import { ImagePreview } from "@/components/image-preview"
import { MetadataPanel } from "@/components/metadata-panel"
import { ThumbnailViewport } from "@/components/thumbnail-viewport"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription } from "@/components/ui/empty"
import { FsItem } from "@/types/fs"
import type { ImageMetadata, ViewMode } from "@/types/metadata"

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<FsItem | null>(null)
  const [currentDir, setCurrentDir] = useState<string | null>(".")
  const [metadata, setMetadata] = useState<{ data: ImageMetadata | null; loading: boolean }>({ data: null, loading: false })
  const [viewMode, setViewMode] = useState<ViewMode>("list")
  const [showMetadata, setShowMetadata] = useState(true)

  const fetchMetadata = async (file: FsItem) => {
    setMetadata({ data: null, loading: true });
    try {
      const response = await fetch(`/api/metadata?path=${encodeURIComponent(file.path)}`);
      if (!response.ok) {
        throw new Error('Failed to fetch metadata');
      }
      const data = await response.json();
      setMetadata({ data, loading: false });
    } catch (error) {
      console.error(error);
      setMetadata({ data: null, loading: false });
    }
  };

  const handleFileSelect = (file: FsItem) => {
    if (file.isDirectory) {
      setSelectedFile(null)
      setMetadata({ data: null, loading: false })
      return
    }

    // Track which directory this file is in
    const dirPath = file.path.includes('/') ? file.path.slice(0, file.path.lastIndexOf('/')) : '.'
    setCurrentDir(dirPath)

    setSelectedFile(file)
    fetchMetadata(file);
  }

  const handleDirExpand = (dirPath: string) => {
    setCurrentDir(dirPath)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Page-specific toolbar */}
      <div className="h-10 border-b border-border bg-muted/20 flex items-center justify-between px-4">
        <div className="flex items-center gap-2 bg-muted rounded-lg p-0.5">
          <button
            onClick={() => setViewMode("list")}
            className={`p-1.5 rounded transition-colors ${
              viewMode === "list" ? "bg-background shadow-sm" : "hover:bg-background/50"
            }`}
            aria-label="List view"
          >
            <List className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setViewMode("thumbnail")}
            className={`p-1.5 rounded transition-colors ${
              viewMode === "thumbnail" ? "bg-background shadow-sm" : "hover:bg-background/50"
            }`}
            aria-label="Thumbnail view"
          >
            <Grid3x3 className="w-3.5 h-3.5" />
          </button>
        </div>

        <button
          onClick={() => setShowMetadata(!showMetadata)}
          className="p-1.5 hover:bg-accent rounded-lg transition-colors"
          aria-label={showMetadata ? "Hide metadata" : "Show metadata"}
        >
          {showMetadata ? <SidebarClose className="w-3.5 h-3.5" /> : <SidebarOpen className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Resizable panel layout */}
      <PanelGroup id="main-layout" direction="horizontal" className="flex-1">
        {/* File Tree */}
        <Panel id="file-tree" defaultSize={15} minSize={10} maxSize={30}>
          <FileTree
            onFileSelect={handleFileSelect}
            onDirExpand={handleDirExpand}
            selectedFile={selectedFile ?? undefined}
            viewMode={viewMode}
          />
        </Panel>

        <PanelResizeHandle className="w-1 bg-border hover:bg-primary/50 transition-colors cursor-col-resize" />

        {/* Center: Image Preview + Thumbnail Strip */}
        <Panel id="center" defaultSize={showMetadata ? 60 : 85} minSize={30}>
          <PanelGroup id="center-vertical" direction="vertical">
            {/* Image Preview */}
            <Panel id="image-preview" defaultSize={70} minSize={30}>
              <div className="h-full flex flex-col">
                {!selectedFile ? (
                  <Empty className="flex-1 border-0">
                    <EmptyHeader>
                      <EmptyMedia variant="icon"><ImageIcon /></EmptyMedia>
                      <EmptyTitle>No image selected</EmptyTitle>
                      <EmptyDescription>Browse the file tree and select an image to preview</EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                ) : (
                  <ImagePreview
                    src={`/api/image?path=${encodeURIComponent(selectedFile.path)}`}
                    fileName={selectedFile.name}
                  />
                )}
              </div>
            </Panel>

            <PanelResizeHandle className="h-1 bg-border hover:bg-primary/50 transition-colors cursor-row-resize" />

            {/* Thumbnail Viewport */}
            <Panel id="thumbnails" defaultSize={30} minSize={10} maxSize={60}>
              <ThumbnailViewport
                currentDir={currentDir}
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile ?? undefined}
              />
            </Panel>
          </PanelGroup>
        </Panel>

        {/* Metadata Panel */}
        {showMetadata && (
          <>
            <PanelResizeHandle className="w-1 bg-border hover:bg-primary/50 transition-colors cursor-col-resize" />
            <Panel id="metadata" defaultSize={25} minSize={15} maxSize={50}>
              <MetadataPanel metadata={metadata.data} isLoading={metadata.loading} />
            </Panel>
          </>
        )}
      </PanelGroup>
    </div>
  )
}
