"use client"

import { useState, useEffect } from "react"
import { Navbar } from "@/components/navbar"
import { FileTree } from "@/components/file-tree"
import { ImagePreview } from "@/components/image-preview"
import { MetadataPanel } from "@/components/metadata-panel"
import { FsItem } from "@/types/fs"
import type { ImageMetadata, ViewMode } from "@/types/metadata"
import { Loader2 } from "lucide-react"

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<FsItem | null>(null)
  const [metadata, setMetadata] = useState<{ data: ImageMetadata | null; loading: boolean }>({ data: null, loading: false })
  const [viewMode, setViewMode] = useState<ViewMode>("thumbnail")
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
      // Handle error display
    }
  };

  const handleFileSelect = (file: FsItem) => {
    if (file.isDirectory) {
      setSelectedFile(null)
      setMetadata({ data: null, loading: false })
      return
    }
    
    setSelectedFile(file)
    fetchMetadata(file);
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      <Navbar
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showMetadata={showMetadata}
        onToggleMetadata={() => setShowMetadata(!showMetadata)}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* File Tree Sidebar */}
        <FileTree
          onFileSelect={handleFileSelect}
          selectedFile={selectedFile ?? undefined}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* File View / Image Preview */}
          <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
            {!selectedFile ? (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <p>Select an image to view its metadata</p>
              </div>
            ) : (
              <ImagePreview 
                src={`/api/image?path=${encodeURIComponent(selectedFile.path)}`} 
                fileName={selectedFile.name} 
              />
            )}
          </div>

          {/* Metadata Panel */}
          {showMetadata && (
            <div className="w-96 border-l border-border overflow-hidden">
              <MetadataPanel metadata={metadata.data} isLoading={metadata.loading} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

