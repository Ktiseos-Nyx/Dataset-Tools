"use client"

import { ChevronRight, ChevronDown, Folder, FolderOpen, FileImage } from "lucide-react"
import { useState } from "react"
import type { FileItem } from "@/types/metadata"

interface FileTreeProps {
  files: FileItem[]
  onFileSelect: (file: FileItem) => void
  selectedFileId?: string
}

export function FileTree({ files, onFileSelect, selectedFileId }: FileTreeProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <aside className="w-64 border-r border-border bg-muted/20 flex flex-col">
      {/* Header */}
      <div className="h-10 border-b border-border px-3 flex items-center">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Files</h2>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {files.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-sm text-muted-foreground">No files loaded</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {/* Root folder */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-accent rounded text-sm group"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              )}
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-primary" />
              ) : (
                <Folder className="w-4 h-4 text-muted-foreground" />
              )}
              <span className="font-medium">Images ({files.length})</span>
            </button>

            {/* Files */}
            {isExpanded &&
              files.map((file) => (
                <button
                  key={file.id}
                  onClick={() => onFileSelect(file)}
                  className={`w-full flex items-center gap-1.5 px-2 py-1.5 pl-8 hover:bg-accent rounded text-sm group ${
                    selectedFileId === file.id ? "bg-accent" : ""
                  }`}
                >
                  <FileImage className="w-4 h-4 text-muted-foreground" />
                  <span className="truncate text-left flex-1">{file.name}</span>
                </button>
              ))}
          </div>
        )}
      </div>
    </aside>
  )
}
