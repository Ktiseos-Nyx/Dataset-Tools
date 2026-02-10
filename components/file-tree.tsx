"use client"

import { ChevronRight, ChevronDown, Folder, FolderOpen, FileImage, Loader2, FolderSearch, Copy, RefreshCw, ArrowUpDown, FolderInput } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import type { FsItem } from "@/types/fs"
import type { ViewMode } from "@/types/metadata"
import { useSettings } from "@/hooks/use-settings"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription } from "@/components/ui/empty"
import {
  ContextMenu, ContextMenuTrigger, ContextMenuContent, ContextMenuItem, ContextMenuSeparator,
} from "@/components/ui/context-menu"
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
} from "@/components/ui/dropdown-menu"

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
  sortBy,
  baseFolder,
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
  sortBy: 'name' | 'date' | 'size';
  baseFolder: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [children, setChildren] = useState<FsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchChildren = async () => {
    if (!isExpanded) {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/fs?path=${encodeURIComponent(item.path)}&showHidden=${showHidden}&baseFolder=${encodeURIComponent(baseFolder)}`);
        if (!response.ok) {
          throw new Error('Failed to fetch directory contents');
        }
        const data = await response.json();
        const items = data.map((child: FsItem) => ({
          ...child,
          path: `${item.path}/${child.name}`,
        }));
        setChildren(sortItems(items, sortBy));
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
          <Folder className="w-4 h-4 text-accent-foreground" />
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
              baseFolder={baseFolder}
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
                  sortBy={sortBy}
                  baseFolder={baseFolder}
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
                      <FileImage className="w-4 h-4 text-accent-foreground" />
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
  baseFolder,
}: {
  items: FsItem[];
  onFileSelect: (file: FsItem) => void;
  selectedFile?: FsItem;
  level: number;
  showFileExtensions: boolean;
  thumbnailSize: string;
  baseFolder: string;
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
          <LazyThumbnail path={item.path} size={size} baseFolder={baseFolder} />
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

function LazyThumbnail({ path: filePath, size, baseFolder }: { path: string; size: number; baseFolder: string }) {
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
          src={`/api/thumbnail?path=${encodeURIComponent(filePath)}&size=${size * 2}&baseFolder=${encodeURIComponent(baseFolder)}`}
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

function sortItems(items: FsItem[], sortBy: 'name' | 'date' | 'size'): FsItem[] {
  const sorted = [...items];

  // Always keep directories first
  const dirs = sorted.filter(i => i.isDirectory);
  const files = sorted.filter(i => !i.isDirectory);

  const sortFn = (a: FsItem, b: FsItem) => {
    switch (sortBy) {
      case 'date':
        return (b.mtime || 0) - (a.mtime || 0); // Newest first
      case 'size':
        return (b.size || 0) - (a.size || 0); // Largest first
      case 'name':
      default:
        return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
    }
  };

  return [...dirs.sort(sortFn), ...files.sort(sortFn)];
}

export function FileTree({ onFileSelect, onDirExpand, selectedFile, viewMode = "list" }: FileTreeProps) {
  const [rootItems, setRootItems] = useState<FsItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { settings, updateSettings } = useSettings();

  const fetchRoot = async () => {
    setIsLoading(true);
    setRootItems([]); // Clear stale items immediately
    try {
      const response = await fetch(`/api/fs?showHidden=${settings.showHiddenFiles}&baseFolder=${encodeURIComponent(settings.currentFolder)}`);
      if (!response.ok) {
          throw new Error('Failed to fetch root directory');
      }
      const data = await response.json();
      const items = data.map((item: FsItem) => ({
          ...item,
          path: item.name,
      }));
      setRootItems(sortItems(items, settings.sortBy));
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFolderSelect = async () => {
    try {
      // Use the File System Access API if available
      if ('showDirectoryPicker' in window) {
        const dirHandle = await (window as any).showDirectoryPicker();
        // Get the path from the handle (this is tricky in browser)
        // For now, we'll use a text input fallback
        const folderPath = prompt('Enter folder path:', settings.currentFolder);
        if (folderPath) {
          updateSettings({ currentFolder: folderPath });
        }
      } else {
        // Fallback: text input
        const folderPath = prompt('Enter folder path:', settings.currentFolder);
        if (folderPath) {
          updateSettings({ currentFolder: folderPath });
        }
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
    }
  };

  useEffect(() => {
    fetchRoot();
  }, [settings.showHiddenFiles, settings.sortBy, settings.currentFolder]);

  return (
    <aside className="h-full bg-muted/20 flex flex-col">
      <div className="h-10 border-b border-border px-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">File Browser</h2>
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={handleFolderSelect}
                className="p-1.5 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded transition-colors"
                title="Open Folder"
              >
                <FolderInput className="w-4 h-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Open Folder</TooltipContent>
          </Tooltip>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-1.5 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded transition-colors"
                title="Sort by"
              >
                <ArrowUpDown className="w-4 h-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Sort by</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => updateSettings({ sortBy: 'name' })}>
                Name {settings.sortBy === 'name' && '✓'}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => updateSettings({ sortBy: 'date' })}>
                Date Modified {settings.sortBy === 'date' && '✓'}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => updateSettings({ sortBy: 'size' })}>
                Size {settings.sortBy === 'size' && '✓'}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <button
            onClick={fetchRoot}
            disabled={isLoading}
            className="p-1.5 hover:bg-accent text-muted-foreground hover:text-accent-foreground rounded transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
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
                baseFolder={settings.currentFolder}
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
                    sortBy={settings.sortBy}
                    baseFolder={settings.currentFolder}
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
                        <FileImage className="w-4 h-4 text-accent-foreground" />
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
