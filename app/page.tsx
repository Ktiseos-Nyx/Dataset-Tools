"use client"

import { useState } from "react"
import { Navbar } from "@/components/navbar"
import { FileTree } from "@/components/file-tree"
import { FileView } from "@/components/file-view"
import { ImagePreview } from "@/components/image-preview"
import { MetadataPanel } from "@/components/metadata-panel"
import type { ImageMetadata, FileItem, ViewMode } from "@/types/metadata"

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [metadata, setMetadata] = useState<ImageMetadata | null>(null)
  const [fileName, setFileName] = useState<string>("")
  const [viewMode, setViewMode] = useState<ViewMode>("thumbnail")
  const [showMetadata, setShowMetadata] = useState(true)
  const [files, setFiles] = useState<FileItem[]>([])

  const handleFileSelect = (file: FileItem) => {
    setSelectedImage(file.url)
    setFileName(file.name)
    setMetadata({
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      lastModified: file.lastModified,
      exif: {},
      iptc: {},
      xmp: {},
      ai: {},
    })
  }

  const handleFilesAdded = (newFiles: File[]) => {
    const fileItems: FileItem[] = newFiles.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: new Date(file.lastModified).toISOString(),
      url: URL.createObjectURL(file),
      thumbnail: URL.createObjectURL(file),
    }))

    setFiles((prev) => [...prev, ...fileItems])

    // Auto-select first file if none selected
    if (!selectedImage && fileItems.length > 0) {
      handleFileSelect(fileItems[0])
    }
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      <Navbar
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showMetadata={showMetadata}
        onToggleMetadata={() => setShowMetadata(!showMetadata)}
        onFilesAdded={handleFilesAdded}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* File Tree Sidebar */}
        <FileTree
          files={files}
          onFileSelect={handleFileSelect}
          selectedFileId={files.find((f) => f.url === selectedImage)?.id}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* File View / Image Preview */}
          <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
            {!selectedImage ? (
              <FileView
                files={files}
                viewMode={viewMode}
                onFileSelect={handleFileSelect}
                onFilesAdded={handleFilesAdded}
              />
            ) : (
              <ImagePreview src={selectedImage || "/placeholder.svg"} fileName={fileName} />
            )}
          </div>

          {/* Metadata Panel */}
          {showMetadata && (
            <div className="w-96 border-l border-border overflow-hidden">
              <MetadataPanel metadata={metadata} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
