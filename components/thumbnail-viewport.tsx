"use client"

import { useState, useEffect, useRef } from "react"
import { FileImage, Loader2, FolderOpen, ImageIcon, Copy, FileText, Brain } from "lucide-react"
import type { FsItem } from "@/types/fs"
import { useSettings } from "@/hooks/use-settings"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription } from "@/components/ui/empty"
import {
  ContextMenu, ContextMenuTrigger, ContextMenuContent, ContextMenuItem, ContextMenuSeparator,
} from "@/components/ui/context-menu"

interface ThumbnailViewportProps {
  currentDir: string | null
  onFileSelect: (file: FsItem) => void
  selectedFile?: FsItem
}

export function ThumbnailViewport({ currentDir, onFileSelect, selectedFile }: ThumbnailViewportProps) {
  const [images, setImages] = useState<FsItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { settings } = useSettings()

  useEffect(() => {
    if (!currentDir) {
      setImages([])
      return
    }

    const fetchImages = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`/api/fs?path=${encodeURIComponent(currentDir)}&showHidden=${settings.showHiddenFiles}&baseFolder=${encodeURIComponent(settings.currentFolder)}`)
        if (!response.ok) throw new Error('Failed to fetch')
        const data = await response.json()
        const files: FsItem[] = data
          .filter((item: FsItem) => !item.isDirectory)
          .map((item: FsItem) => ({
            ...item,
            path: currentDir === '.' ? item.name : `${currentDir}/${item.name}`,
          }))
        const sortBy = settings.sortBy
        files.sort((a, b) => {
          switch (sortBy) {
            case 'date': return (b.mtime ?? 0) - (a.mtime ?? 0)
            case 'size': return (b.size ?? 0) - (a.size ?? 0)
            default: return a.name.localeCompare(b.name)
          }
        })
        setImages(files)
      } catch {
        setImages([])
      } finally {
        setIsLoading(false)
      }
    }
    fetchImages()
  }, [currentDir, settings.showHiddenFiles, settings.currentFolder, settings.sortBy])

  const selectedRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (selectedRef.current) {
      selectedRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }, [selectedFile?.path])

  return (
    <div className="h-full flex flex-col bg-muted/20">
      <div className="h-8 border-b border-border px-3 flex items-center shrink-0">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Thumbnails
          {currentDir && currentDir !== '.' && (
            <span className="ml-2 font-normal normal-case opacity-60">
              {currentDir.split('/').pop()}
            </span>
          )}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
          </div>
        ) : images.length === 0 ? (
          <Empty className="border-0 h-full">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                {currentDir ? <ImageIcon /> : <FolderOpen />}
              </EmptyMedia>
              <EmptyTitle className="text-sm">
                {currentDir ? 'No images' : 'No folder selected'}
              </EmptyTitle>
              <EmptyDescription className="text-xs">
                {currentDir ? 'This folder has no image files' : 'Browse a folder to see thumbnails'}
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <div className="flex flex-wrap gap-2 content-start">
            {images.map((item) => {
              const isSelected = selectedFile?.path === item.path
              return (
                <ContextMenu key={item.path}>
                  <ContextMenuTrigger asChild>
                    <button
                      ref={isSelected ? selectedRef : undefined}
                      onClick={() => onFileSelect(item)}
                      className={`flex flex-col items-center gap-1 p-1.5 rounded-lg hover:bg-accent transition-colors ${
                        isSelected ? "bg-accent ring-1 ring-primary" : ""
                      }`}
                      style={{ width: 96 }}
                    >
                      <Thumb path={item.path} baseFolder={settings.currentFolder} />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-[10px] truncate w-full text-center text-muted-foreground">
                            {item.name}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>{item.name}</TooltipContent>
                      </Tooltip>
                    </button>
                  </ContextMenuTrigger>
                  <ContextMenuContent>
                    <ContextMenuItem onClick={() => onFileSelect(item)}>
                      <FileText className="w-4 h-4" />
                      View Metadata
                    </ContextMenuItem>
                    <ContextMenuSeparator />
                    <ContextMenuItem onClick={() => navigator.clipboard.writeText(item.name)}>
                      <Copy className="w-4 h-4" />
                      Copy Filename
                    </ContextMenuItem>
                    <ContextMenuItem onClick={() => navigator.clipboard.writeText(item.path)}>
                      <Copy className="w-4 h-4" />
                      Copy Path
                    </ContextMenuItem>
                  </ContextMenuContent>
                </ContextMenu>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

const MODEL_EXTENSIONS = new Set(['.safetensors'])

function isModelFile(name: string): boolean {
  return MODEL_EXTENSIONS.has(name.slice(name.lastIndexOf('.')).toLowerCase())
}

function Thumb({ path: filePath, baseFolder }: { path: string; baseFolder: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)
  const [loaded, setLoaded] = useState(false)

  const fileName = filePath.split('/').pop() ?? filePath

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin: '50px' }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  if (isModelFile(fileName)) {
    return (
      <div className="w-[76px] h-[76px] rounded bg-primary/10 flex items-center justify-center">
        <Brain className="w-7 h-7 text-primary/60" />
      </div>
    )
  }

  return (
    <div
      ref={ref}
      className="w-[76px] h-[76px] rounded bg-muted/50 flex items-center justify-center overflow-hidden"
    >
      {visible ? (
        <img
          src={`/api/thumbnail?path=${encodeURIComponent(filePath)}&size=152&baseFolder=${encodeURIComponent(baseFolder)}`}
          alt=""
          className={`object-cover w-full h-full transition-opacity duration-200 ${loaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setLoaded(true)}
          loading="lazy"
        />
      ) : (
        <FileImage className="w-5 h-5 text-muted-foreground/20" />
      )}
    </div>
  )
}
