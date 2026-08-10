"use client"

import { useState, useRef } from "react"
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels"
import { SidebarClose, SidebarOpen, X } from "lucide-react"
import { ImagePreview } from "@/components/image-preview"
import { MetadataPanel } from "@/components/metadata-panel"
import { DropZone } from "@/components/drop-zone"
import { UploadZone } from "@/components/upload-zone"
import { FsItem } from "@/types/fs"
import type { ImageMetadata } from "@/types/metadata"
import { useSettings } from "@/hooks/use-settings"

export default function Home() {
  const { settings } = useSettings()
  const [selectedFile, setSelectedFile] = useState<FsItem | null>(null)
  const [imageSrc, setImageSrc] = useState<string>("")
  const [metadata, setMetadata] = useState<{ data: ImageMetadata | null; loading: boolean }>({ data: null, loading: false })
  const [showMetadata, setShowMetadata] = useState(true)
  const metadataRef = useRef<ImageMetadata | null>(null)

  const handleFileDrop = (file: File) => {
    const objectUrl = URL.createObjectURL(file)
    setImageSrc(objectUrl)
    setSelectedFile({
      name: file.name,
      path: objectUrl,
      isDirectory: false,
    })

    setMetadata({ data: null, loading: true })
    const formData = new FormData()
    formData.append("file", file)
    fetch("/api/metadata-from-file", { method: "POST", body: formData })
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json()
          metadataRef.current = data
          setMetadata({ data, loading: false })
        } else {
          setMetadata({ data: null, loading: false })
        }
      })
      .catch(() => setMetadata({ data: null, loading: false }))
  }

  const handleClear = () => {
    setSelectedFile(null)
    setImageSrc("")
    setMetadata({ data: null, loading: false })
    metadataRef.current = null
  }

  const handleRefresh = () => {
    if (!metadataRef.current || !selectedFile) return
    setMetadata({ data: metadataRef.current, loading: false })
  }

  return (
    <>
      <DropZone onFileDrop={(file) => handleFileDrop(file)} />
      <div className="flex flex-col h-full">
        <div className="h-10 border-b border-border bg-muted/20 flex items-center justify-between px-4">
          <div />
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="p-1.5 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded-lg transition-colors"
            aria-label={showMetadata ? "Hide metadata" : "Show metadata"}
          >
            {showMetadata ? <SidebarClose className="w-3.5 h-3.5" /> : <SidebarOpen className="w-3.5 h-3.5" />}
          </button>
        </div>

        {!selectedFile ? (
          <UploadZone onFileDrop={handleFileDrop} />
        ) : (
          <PanelGroup id="demo-layout" direction="horizontal" className="flex-1">
            <Panel id="image-preview" defaultSize={showMetadata ? 60 : 100} minSize={30}>
              <div className="h-full flex flex-col">
                <div className="h-8 border-b border-border bg-muted/20 flex items-center justify-between px-3">
                  <span className="text-xs text-muted-foreground truncate max-w-[80%]">{selectedFile.name}</span>
                  <button
                    onClick={handleClear}
                    className="p-1 hover:bg-accent rounded transition-colors"
                    aria-label="Remove image"
                  >
                    <X className="w-3.5 h-3.5 text-muted-foreground" />
                  </button>
                </div>
                <ImagePreview
                  src={imageSrc}
                  fileName={selectedFile.name}
                  onRefresh={handleRefresh}
                />
              </div>
            </Panel>

            {showMetadata && (
              <>
                <PanelResizeHandle className="w-1 bg-border hover:bg-primary/50 transition-colors cursor-col-resize" />
                <Panel id="metadata" defaultSize={40} minSize={20} maxSize={55}>
                  <MetadataPanel
                    metadata={metadata.data}
                    isLoading={metadata.loading}
                    filePath={selectedFile.path}
                    baseFolder={settings.currentFolder}
                    onRefresh={handleRefresh}
                  />
                </Panel>
              </>
            )}
          </PanelGroup>
        )}
      </div>
    </>
  )
}
