"use client"

import { ChevronRight, ChevronDown, Folder, FolderOpen, FileImage, Loader2 } from "lucide-react"
import { useState, useEffect } from "react"
import type { FsItem } from "@/types/fs"

interface FileTreeProps {
  onFileSelect: (file: FsItem) => void;
  selectedFile?: FsItem;
}

function Directory({
  item,
  onFileSelect,
  selectedFile,
  level = 0,
}: {
  item: FsItem;
  onFileSelect: (file: FsItem) => void;
  selectedFile?: FsItem;
  level?: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [children, setChildren] = useState<FsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchChildren = async () => {
    if (!isExpanded) {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/fs?path=${encodeURIComponent(item.path)}`);
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
        // Handle error display to the user
      } finally {
        setIsLoading(false);
      }
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
        <div className="space-y-0.5">
          {children.map((child) =>
            child.isDirectory ? (
              <Directory
                key={child.path}
                item={child}
                onFileSelect={onFileSelect}
                selectedFile={selectedFile}
                level={level + 1}
              />
            ) : (
              <button
                key={child.path}
                onClick={() => onFileSelect(child)}
                className={`w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-accent rounded text-sm group ${
                  selectedFile?.path === child.path ? "bg-accent" : ""
                }`}
                style={{ paddingLeft: `${(level + 1) * 1.5 + 0.5}rem` }}
              >
                <FileImage className="w-4 h-4 text-muted-foreground" />
                <span className="truncate text-left flex-1">{child.name}</span>
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
}


export function FileTree({ onFileSelect, selectedFile }: FileTreeProps) {
  const [rootItems, setRootItems] = useState<FsItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchRoot = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/fs');
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
        // You might want to set an error state here and display it to the user
      } finally {
        setIsLoading(false);
      }
    };
    fetchRoot();
  }, []);

  return (
    <aside className="w-64 border-r border-border bg-muted/20 flex flex-col">
      <div className="h-10 border-b border-border px-3 flex items-center">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">File Browser</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="w-6 h-6 text-muted-foreground animate-spin" />
          </div>
        ) : rootItems.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-sm text-muted-foreground">No files found</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {rootItems.map((item) => (
              item.isDirectory ? (
                <Directory
                    key={item.path}
                    item={item}
                    onFileSelect={onFileSelect}
                    selectedFile={selectedFile}
                />
              ) : (
                <button
                    key={item.path}
                    onClick={() => onFileSelect(item)}
                    className={`w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-accent rounded text-sm group ${
                        selectedFile?.path === item.path ? "bg-accent" : ""
                    }`}
                >
                    <FileImage className="w-4 h-4 text-muted-foreground" />
                    <span className="truncate text-left flex-1">{item.name}</span>
                </button>
              )
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
