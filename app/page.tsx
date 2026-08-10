"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels"
import { SidebarClose, SidebarOpen, X } from "lucide-react"
import { ImagePreview } from "@/components/image-preview"
import { MetadataPanel } from "@/components/metadata-panel"
import { DropZone } from "@/components/drop-zone"
import { UploadZone } from "@/components/upload-zone"
import { FsItem } from "@/types/fs"
import type { ImageMetadata } from "@/types/metadata"
import { useSettings } from "@/hooks/use-settings"

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia(query)
    setMatches(mq.matches)
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [query])

  return matches
}

export default function Home() {
  const { settings } = useSettings()
  const isDesktop = useMediaQuery("(min-width: 768px)")
  const [selectedFile, setSelectedFile] = useState<FsItem | null>(null)
  const [imageSrc, setImageSrc] = useState<string>("")
  const [metadata, setMetadata] = useState<{ data: ImageMetadata | null; loading: boolean; error?: string }>({ data: null, loading: false })
  const [showMetadata, setShowMetadata] = useState(true)
  const metadataRef = useRef<ImageMetadata | null>(null)
  const fileRef = useRef<File | null>(null)

  const handleFileDrop = useCallback((file: File) => {
    fileRef.current = file

    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      setImageSrc(dataUrl)
      setSelectedFile({
        name: file.name,
        path: dataUrl,
        isDirectory: false,
      })
    }
    reader.readAsDataURL(file)

    setMetadata({ data: null, loading: true })
    const formData = new FormData()
    formData.append("file", file)
    console.log("[demo] uploading file:", file.name, file.type, file.size)
    fetch("/api/metadata-from-file", { method: "POST", body: formData })
      .then(async (res) => {
        console.log("[demo] metadata response status:", res.status)
        if (res.ok) {
          const data = await res.json()
          console.log("[demo] metadata parsed, keys:", Object.keys(data))
          metadataRef.current = data
          setMetadata({ data, loading: false })
        } else {
          const text = await res.text()
          console.error("[demo] metadata error response:", res.status, text)
          setMetadata({ data: null, loading: false, error: `Server error: ${res.status}` })
        }
      })
      .catch((err) => {
        console.error("[demo] metadata fetch failed:", err)
        setMetadata({ data: null, loading: false, error: String(err) })
      })
  }, [])

  const handleClear = useCallback(() => {
    setSelectedFile(null)
    setImageSrc("")
    setMetadata({ data: null, loading: false })
    metadataRef.current = null
    fileRef.current = null
  }, [])

  const handleRefresh = useCallback(() => {
    if (!metadataRef.current || !selectedFile) return
    setMetadata({ data: metadataRef.current, loading: false })
  }, [selectedFile])

  return (
    <>
      <DropZone onFileDrop={handleFileDrop} />
      <div className="flex flex-col h-full">
        <div className="h-10 border-b border-border bg-muted/20 flex items-center justify-between px-4">
          <div />
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="p-1.5 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded-lg transition-colors md:hidden"
            aria-label={showMetadata ? "Hide metadata" : "Show metadata"}
          >
            {showMetadata ? <SidebarClose className="w-3.5 h-3.5" /> : <SidebarOpen className="w-3.5 h-3.5" />}
          </button>
        </div>

        {!selectedFile ? (
          <UploadZone onFileDrop={handleFileDrop} />
        ) : isDesktop ? (
          <PanelGroup id="demo-layout" direction="horizontal" className="flex-1">
            <Panel id="image-preview" defaultSize={showMetadata ? 60 : 100} minSize={30}>
              <div className="h-full flex flex-col">
                <div className="h-8 border-b border-border bg-muted/20 flex items-center justify-between px-3">
                  <span className="text-xs text-muted-foreground truncate max-w-[80%]">{selectedFile.name}</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setShowMetadata(!showMetadata)}
                      className="p-1 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded-lg transition-colors hidden md:block"
                      aria-label={showMetadata ? "Hide metadata" : "Show metadata"}
                    >
                      {showMetadata ? <SidebarClose className="w-3.5 h-3.5" /> : <SidebarOpen className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={handleClear}
                      className="p-1 hover:bg-accent rounded transition-colors"
                      aria-label="Remove image"
                    >
                      <X className="w-3.5 h-3.5 text-muted-foreground" />
                    </button>
                  </div>
                </div>
                {metadata.error && (
                  <div className="px-3 py-1.5 bg-destructive/10 border-b border-destructive/20 text-xs text-destructive">
                    Metadata failed: {metadata.error}
                  </div>
                )}
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
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="h-8 border-b border-border bg-muted/20 flex items-center justify-between px-3 shrink-0">
              <span className="text-xs text-muted-foreground truncate max-w-[60%]">{selectedFile.name}</span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setShowMetadata(!showMetadata)}
                  className="p-1 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded-lg transition-colors"
                  aria-label={showMetadata ? "Hide metadata" : "Show metadata"}
                >
                  {showMetadata ? <SidebarClose className="w-3.5 h-3.5" /> : <SidebarOpen className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={handleClear}
                  className="p-1 hover:bg-accent rounded transition-colors"
                  aria-label="Remove image"
                >
                  <X className="w-3.5 h-3.5 text-muted-foreground" />
                </button>
              </div>
            </div>
            {metadata.error && (
              <div className="px-3 py-1.5 bg-destructive/10 border-b border-destructive/20 text-xs text-destructive">
                Metadata failed: {metadata.error}
              </div>
            )}
            <div className="flex-1 min-h-0">
              <ImagePreview
                src={imageSrc}
                fileName={selectedFile.name}
                onRefresh={handleRefresh}
              />
            </div>
            {showMetadata && (
              <div className="border-t border-border max-h-[50vh] overflow-y-auto shrink-0">
                <MetadataPanel
                  metadata={metadata.data}
                  isLoading={metadata.loading}
                  filePath={selectedFile.path}
                  baseFolder={settings.currentFolder}
                  onRefresh={handleRefresh}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}
