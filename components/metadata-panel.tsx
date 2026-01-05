"use client"

import { useState } from "react"
import { Copy, Camera, FileText, Sparkles, Code, Check } from "lucide-react"
import type { ImageMetadata } from "@/types/metadata"

interface MetadataPanelProps {
  metadata: ImageMetadata | null
}

export function MetadataPanel({ metadata }: MetadataPanelProps) {
  const [activeTab, setActiveTab] = useState<"basic" | "exif" | "iptc" | "xmp" | "ai">("basic")
  const [copiedValue, setCopiedValue] = useState<string | null>(null)

  if (!metadata) {
    return (
      <div className="h-full flex flex-col">
        <div className="h-10 border-b border-border px-4 flex items-center bg-muted/20">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Metadata</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <p className="text-sm text-muted-foreground">Select a file to view metadata</p>
        </div>
      </div>
    )
  }

  const tabs = [
    { id: "basic" as const, label: "Basic", icon: FileText },
    { id: "exif" as const, label: "EXIF", icon: Camera },
    { id: "iptc" as const, label: "IPTC", icon: FileText },
    { id: "xmp" as const, label: "XMP", icon: Code },
    { id: "ai" as const, label: "AI", icon: Sparkles },
  ]

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB"
    return (bytes / (1024 * 1024)).toFixed(2) + " MB"
  }

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedValue(key)
    setTimeout(() => setCopiedValue(null), 2000)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-10 border-b border-border px-4 flex items-center bg-muted/20">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Metadata</h2>
      </div>

      {/* Tabs */}
      <div className="border-b border-border bg-card/50">
        <div className="flex gap-1 p-1.5 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          {activeTab === "basic" && (
            <>
              <MetadataRow
                label="File Name"
                value={metadata.fileName}
                onCopy={() => copyToClipboard(metadata.fileName, "fileName")}
                copied={copiedValue === "fileName"}
              />
              <MetadataRow label="File Size" value={formatFileSize(metadata.fileSize)} />
              <MetadataRow label="File Type" value={metadata.fileType} />
              <MetadataRow label="Last Modified" value={new Date(metadata.lastModified).toLocaleString()} />
            </>
          )}

          {activeTab === "exif" && (
            <>
              {Object.keys(metadata.exif || {}).length === 0 ? (
                <div className="text-center py-8">
                  <Camera className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No EXIF data found</p>
                  <p className="text-xs text-muted-foreground mt-1">Camera settings will appear here</p>
                </div>
              ) : (
                Object.entries(metadata.exif || {}).map(([key, value]) => (
                  <MetadataRow
                    key={key}
                    label={key}
                    value={String(value)}
                    onCopy={() => copyToClipboard(String(value), `exif-${key}`)}
                    copied={copiedValue === `exif-${key}`}
                  />
                ))
              )}
            </>
          )}

          {activeTab === "iptc" && (
            <>
              {Object.keys(metadata.iptc || {}).length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No IPTC data found</p>
                  <p className="text-xs text-muted-foreground mt-1">Copyright and keywords will appear here</p>
                </div>
              ) : (
                Object.entries(metadata.iptc || {}).map(([key, value]) => (
                  <MetadataRow
                    key={key}
                    label={key}
                    value={String(value)}
                    onCopy={() => copyToClipboard(String(value), `iptc-${key}`)}
                    copied={copiedValue === `iptc-${key}`}
                  />
                ))
              )}
            </>
          )}

          {activeTab === "xmp" && (
            <>
              {Object.keys(metadata.xmp || {}).length === 0 ? (
                <div className="text-center py-8">
                  <Code className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No XMP data found</p>
                  <p className="text-xs text-muted-foreground mt-1">Adobe metadata will appear here</p>
                </div>
              ) : (
                Object.entries(metadata.xmp || {}).map(([key, value]) => (
                  <MetadataRow
                    key={key}
                    label={key}
                    value={String(value)}
                    onCopy={() => copyToClipboard(String(value), `xmp-${key}`)}
                    copied={copiedValue === `xmp-${key}`}
                    mono
                  />
                ))
              )}
            </>
          )}

          {activeTab === "ai" && (
            <>
              {Object.keys(metadata.ai || {}).length === 0 ? (
                <div className="text-center py-8">
                  <Sparkles className="w-8 h-8 text-primary mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground mb-2">No AI generation data found</p>
                  <div className="text-xs text-muted-foreground text-left max-w-xs mx-auto space-y-1">
                    <p className="font-medium">This will display:</p>
                    <ul className="list-disc list-inside space-y-0.5 ml-2">
                      <li>Generation prompts</li>
                      <li>Model information</li>
                      <li>Sampling parameters</li>
                      <li>Seed values</li>
                    </ul>
                  </div>
                </div>
              ) : (
                Object.entries(metadata.ai || {}).map(([key, value]) => (
                  <MetadataRow
                    key={key}
                    label={key}
                    value={String(value)}
                    onCopy={() => copyToClipboard(String(value), `ai-${key}`)}
                    copied={copiedValue === `ai-${key}`}
                    mono
                  />
                ))
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

interface MetadataRowProps {
  label: string
  value: string
  onCopy?: () => void
  copied?: boolean
  mono?: boolean
}

function MetadataRow({ label, value, onCopy, copied, mono = false }: MetadataRowProps) {
  return (
    <div className="flex items-start gap-2 py-2 px-3 rounded-lg hover:bg-accent/50 transition-colors group">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
        <p className={`text-sm break-words ${mono ? "font-mono text-xs" : ""}`}>{value}</p>
      </div>
      {onCopy && (
        <button
          onClick={onCopy}
          className="p-1.5 hover:bg-accent rounded transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100"
          aria-label="Copy to clipboard"
        >
          {copied ? (
            <Check className="w-3.5 h-3.5 text-green-500" />
          ) : (
            <Copy className="w-3.5 h-3.5 text-muted-foreground" />
          )}
        </button>
      )}
    </div>
  )
}
