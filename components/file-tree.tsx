"use client"

import { ChevronRight, ChevronDown, Folder, FolderOpen, FileImage, Loader2, FolderSearch, Copy } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import type { FsItem } from "@/types/fs"
import type { ViewMode } from "@/types/metadata"
import { useSettings } from "@/hooks/use-settings"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription } from "@/components/ui/empty"
import {
  ContextMenu, ContextMenuTrigger, ContextMenuContent, ContextMenuItem, ContextMenuSeparator,
} from "@/components/ui/context-menu"

interface FileTreeProps {
  onFileSelect: (file: FsItem) => void;
  onDirExpand?: (dirPath: string) => void;
  selectedFile?: FsItem;
  viewMode?: ViewMode;
}

function Directory({
  item,
  onFileSelect,
  onDirExpand,
  selectedFile,
  level = 0,
  showHidden,
  viewMode,
  showFileExtensions,
  thumbnailSize,
}: {
  item: FsItem;
  onFileSelect: (file: FsItem) => void;
  onDirExpand?: (dirPath: string) => void;
  selectedFile?: FsItem;
  level?: number;
  showHidden: boolean;
  viewMode: ViewMode;
  showFileExtensions: boolean;
  thumbnailSize: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [children, setChildren] = useState<FsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchChildren = async () => {
    if (!isExpanded) {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/fs?path=${encodeURIComponent(item.path)}&showHidden=${showHidden}`);
        if (!response.ok) {
          throw new Error('Failed to fetch directory contents');
        }
        const data = await response.json();
        setChildren(data.map((child: { name: string; isDirectory: boolean }) => ({
          ...child,
          path: `${item.path}/${child.name}`,
        })));
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
      onDirExpand?.(item.path);
    }
    setIsExpanded(!isExpanded);
  };

  return (
    <div>
      <button
        onClick={fetchChildren}
        className="w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-accent rounded text-sm group"
        style={{ paddingLeft: `${level * 1.5 + 0.5}rem` }}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />
        ) : isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
        )}
        {isExpanded ? (
          <FolderOpen className="w-4 h-4 text-primary" />
        ) : (
          <Folder className="w-4 h-4 text-muted-foreground" />
        )}
        <span className="font-medium">{item.name}</span>
      </button>

      {isExpanded && !isLoading && (
        <>
          {/* Thumbnail grid for image files in this directory */}
          {viewMode === "thumbnail" && children.some(c => !c.isDirectory) && (
            <ThumbnailGrid
              items={children.filter(c => !c.isDirectory)}
              onFileSelect={onFileSelect}
              selectedFile={selectedFile}
              level={level + 1}
              showFileExtensions={showFileExtensions}
              thumbnailSize={thumbnailSize}
            />
          )}
          <div className="space-y-0.5">
            {children.map((child) =>
              child.isDirectory ? (
                <Directory
                  key={child.path}
                  item={child}
                  onFileSelect={onFileSelect}
                  onDirExpand={onDirExpand}
                  selectedFile={selectedFile}
                  level={level + 1}
                  showHidden={showHidden}
                  viewMode={viewMode}
                  showFileExtensions={showFileExtensions}
                  thumbnailSize={thumbnailSize}
                />
              ) : viewMode === "list" ? (
                <ContextMenu key={child.path}>
                  <ContextMenuTrigger asChild>
                    <button
                      onClick={() => onFileSelect(child)}
                      className={`w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-accent rounded text-sm group ${
                        selectedFile?.path === child.path ? "bg-accent" : ""
                      }`}
                      style={{ paddingLeft: `${(level + 1) * 1.5 + 0.5}rem` }}
                    >
                      <FileImage className="w-4 h-4 text-muted-foreground" />
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="truncate text-left flex-1">
                            {showFileExtensions ? child.name : stripExtension(child.name)}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent side="right">{child.name}</TooltipContent>
                      </Tooltip>
                    </button>
                  </ContextMenuTrigger>
                  <ContextMenuContent>
                    <ContextMenuItem onClick={() => navigator.clipboard.writeText(child.name)}>
                      <Copy className="w-4 h-4" />
                      Copy Filename
                    </ContextMenuItem>
                    <ContextMenuItem onClick={() => navigator.clipboard.writeText(child.path)}>
                      <Copy className="w-4 h-4" />
                      Copy Path
                    </ContextMenuItem>
                  </ContextMenuContent>
                </ContextMenu>
              ) : null /* thumbnail files rendered in grid above */
            )}
          </div>
        </>
      )}
    </div>
  );
}


function stripExtension(name: string): string {
  const lastDot = name.lastIndexOf('.')
  return lastDot > 0 ? name.slice(0, lastDot) : name
}

const THUMB_SIZES: Record<string, number> = { sm: 80, md: 120, lg: 160 }

function ThumbnailGrid({
  items,
  onFileSelect,
  selectedFile,
  level,
  showFileExtensions,
  thumbnailSize,
}: {
  items: FsItem[];
  onFileSelect: (file: FsItem) => void;
  selectedFile?: FsItem;
  level: number;
  showFileExtensions: boolean;
  thumbnailSize: string;
}) {
  const size = THUMB_SIZES[thumbnailSize] || 120

  return (
    <div
      className="flex flex-wrap gap-2 p-2"
      style={{ paddingLeft: `${level * 1.5 + 0.5}rem` }}
    >
      {items.map((item) => (
        <button
          key={item.path}
          onClick={() => onFileSelect(item)}
          className={`flex flex-col items-center gap-1 p-1.5 rounded-lg hover:bg-accent transition-colors ${
            selectedFile?.path === item.path ? "bg-accent ring-1 ring-primary" : ""
          }`}
          style={{ width: size + 16 }}
        >
          <LazyThumbnail path={item.path} size={size} />
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="text-xs truncate w-full text-center">
                {showFileExtensions ? item.name : stripExtension(item.name)}
              </span>
            </TooltipTrigger>
            <TooltipContent>{item.name}</TooltipContent>
          </Tooltip>
        </button>
      ))}
    </div>
  )
}

function LazyThumbnail({ path: filePath, size }: { path: string; size: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin: '100px' }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className="rounded bg-muted/50 flex items-center justify-center overflow-hidden"
      style={{ width: size, height: size }}
    >
      {isVisible ? (
        <img
          src={`/api/thumbnail?path=${encodeURIComponent(filePath)}&size=${size * 2}`}
          alt=""
          className={`object-cover w-full h-full transition-opacity duration-200 ${loaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setLoaded(true)}
          loading="lazy"
        />
      ) : (
        <FileImage className="w-6 h-6 text-muted-foreground/30" />
      )}
      {isVisible && !loaded && (
        <Loader2 className="w-4 h-4 text-muted-foreground animate-spin absolute" />
      )}
    </div>
  )
}

export function FileTree({ onFileSelect, onDirExpand, selectedFile, viewMode = "list" }: FileTreeProps) {
  const [rootItems, setRootItems] = useState<FsItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { settings } = useSettings();

  useEffect(() => {
    const fetchRoot = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/fs?showHidden=${settings.showHiddenFiles}`);
        if (!response.ok) {
            throw new Error('Failed to fetch root directory');
        }
        const data = await response.json();
        setRootItems(data.map((item: { name: string; isDirectory: boolean }) => ({
            ...item,
            path: item.name,
        })));
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchRoot();
  }, [settings.showHiddenFiles]);

  return (
    <aside className="h-full bg-muted/20 flex flex-col">
      <div className="h-10 border-b border-border px-3 flex items-center">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">File Browser</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="w-6 h-6 text-muted-foreground animate-spin" />
          </div>
        ) : rootItems.length === 0 ? (
          <Empty className="border-0 py-8">
            <EmptyHeader>
              <EmptyMedia variant="icon"><FolderSearch /></EmptyMedia>
              <EmptyTitle>No images found</EmptyTitle>
              <EmptyDescription>This directory has no image files</EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <>
            {/* Root-level thumbnail grid */}
            {viewMode === "thumbnail" && rootItems.some(i => !i.isDirectory) && (
              <ThumbnailGrid
                items={rootItems.filter(i => !i.isDirectory)}
                onFileSelect={onFileSelect}
                selectedFile={selectedFile}
                level={0}
                showFileExtensions={settings.showFileExtensions}
                thumbnailSize={settings.thumbnailSize}
              />
            )}
            <div className="space-y-0.5">
              {rootItems.map((item) => (
                item.isDirectory ? (
                  <Directory
                    key={item.path}
                    item={item}
                    onFileSelect={onFileSelect}
                    onDirExpand={onDirExpand}
                    selectedFile={selectedFile}
                    showHidden={settings.showHiddenFiles}
                    viewMode={viewMode}
                    showFileExtensions={settings.showFileExtensions}
                    thumbnailSize={settings.thumbnailSize}
                  />
                ) : viewMode === "list" ? (
                  <ContextMenu key={item.path}>
                    <ContextMenuTrigger asChild>
                      <button
                        onClick={() => onFileSelect(item)}
                        className={`w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-accent rounded text-sm group ${
                            selectedFile?.path === item.path ? "bg-accent" : ""
                        }`}
                      >
                        <FileImage className="w-4 h-4 text-muted-foreground" />
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="truncate text-left flex-1">
                              {settings.showFileExtensions ? item.name : stripExtension(item.name)}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent side="right">{item.name}</TooltipContent>
                        </Tooltip>
                      </button>
                    </ContextMenuTrigger>
                    <ContextMenuContent>
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
                ) : null
              ))}
            </div>
          </>
        )}
      </div>
    </aside>
  )
}
