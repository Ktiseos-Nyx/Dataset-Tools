"use client"

import { useState, useEffect, useRef } from "react"
import { Copy, Camera, FileText, Sparkles, Code, Check, Loader2, ListTree, Tag, ImageIcon } from "lucide-react"
import type { ImageMetadata } from "@/types/metadata"
import type { Rule, RuleEvaluationResult } from "@/types/rules"
import { useSettings } from "@/hooks/use-settings"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription } from "@/components/ui/empty"

interface MetadataPanelProps {
  metadata: ImageMetadata | null
  isLoading: boolean
}

// Keys hidden from the generic parameter grid (shown in dedicated UI)
const HIDDEN_KEYS = new Set([
  'prompt', 'negative_prompt', 'workflow_type', 'loras',
  'comfyui_workflow', '_drawthings_params',
])

// Display order for the parameter grid
const PARAM_ORDER = [
  'model', 'sampler', 'scheduler', 'steps', 'cfg_scale', 'seed',
  'size', 'denoise', 'vae', 'clip_skip', 'strength',
]

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

// Defensive coercion for any value that the metadata API might hand us. The
// server already normalises NovelAI/Draw Things JSON into strings, but new
// formats can sneak object-shaped fields ({ content, image, ... }) into
// `ai.prompt` and similar — and rendering one of those as a React child
// triggers React error #31 and blanks the whole panel. This stringifies
// anything non-string so the UI degrades gracefully instead of crashing.
function toDisplayString(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') return String(value)
  if (Array.isArray(value)) return value.map(toDisplayString).filter(Boolean).join(', ')
  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>
    for (const k of ['content', 'text', 'prompt', 'caption', 'value']) {
      if (typeof obj[k] === 'string') return obj[k] as string
    }
    try { return JSON.stringify(value) } catch { return '' }
  }
  return ''
}

const FONT_SIZE_MAP = {
  sm: { prompt: 'text-xs', param: 'text-xs', label: 'text-[10px]' },
  md: { prompt: 'text-sm', param: 'text-sm', label: 'text-xs' },
  lg: { prompt: 'text-base', param: 'text-base', label: 'text-sm' },
} as const

export function MetadataPanel({ metadata, isLoading }: MetadataPanelProps) {
  const [activeTab, setActiveTab] = useState<"basic" | "exif" | "iptc" | "xmp" | "ai" | "rules">("basic")
  const [copiedValue, setCopiedValue] = useState<string | null>(null)
  const [ruleCondition, setRuleCondition] = useState<string>("exif.Make === 'Canon'")
  const [ruleResults, setRuleResults] = useState<RuleEvaluationResult[] | null>(null)
  const [isApplyingRules, setIsApplyingRules] = useState(false)
  const { settings } = useSettings()
  const prevFileRef = useRef<string | null>(null)

  const fs = FONT_SIZE_MAP[settings.fontSize] || FONT_SIZE_MAP.md

  // Auto-switch to the best tab when a new file's metadata loads
  useEffect(() => {
    if (!metadata || metadata.fileName === prevFileRef.current) return
    prevFileRef.current = metadata.fileName

    const hasAi = Object.keys(metadata.ai || {}).length > 0
    const hasExif = Object.keys(metadata.exif || {}).length > 0

    if (hasAi) {
      setActiveTab("ai")
    } else if (hasExif) {
      setActiveTab("exif")
    } else {
      setActiveTab("basic")
    }
  }, [metadata])

  const handleApplyRules = async () => {
    if (!metadata) return
    setIsApplyingRules(true)
    setRuleResults(null)
    try {
      const mockRule: Rule = {
        id: "rule-1",
        name: "Check Camera Make",
        condition: ruleCondition,
        action: "flag",
        value: "CameraMakeFlag",
      }
      const response = await fetch('/api/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rules: [mockRule], metadata }),
      })
      if (!response.ok) throw new Error('Failed to apply rules')
      const results: RuleEvaluationResult[] = await response.json()
      setRuleResults(results)
    } catch (error) {
      setRuleResults([{
        ruleId: "error",
        ruleName: "Error",
        passed: false,
        message: (error as Error).message,
      }])
    } finally {
      setIsApplyingRules(false)
    }
  }

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedValue(key)
    setTimeout(() => setCopiedValue(null), 2000)
  }

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-muted-foreground mx-auto mb-2 animate-spin" />
            <p className="text-sm text-muted-foreground">Loading metadata...</p>
          </div>
        </div>
      )
    }

    if (!metadata) {
      return (
        <Empty className="flex-1 border-0">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <ImageIcon />
            </EmptyMedia>
            <EmptyTitle>No file selected</EmptyTitle>
            <EmptyDescription>Select an image to view its metadata</EmptyDescription>
          </EmptyHeader>
        </Empty>
      )
    }

    const tabs = [
      { id: "basic" as const, label: "Basic", icon: FileText },
      { id: "exif" as const, label: "EXIF", icon: Camera },
      { id: "iptc" as const, label: "IPTC", icon: FileText },
      { id: "xmp" as const, label: "XMP", icon: Code },
      { id: "ai" as const, label: "AI", icon: Sparkles },
      { id: "rules" as const, label: "Rules", icon: ListTree },
    ]

    const formatFileSize = (bytes: number) => {
      if (bytes < 1024) return bytes + " B"
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB"
      return (bytes / (1024 * 1024)).toFixed(2) + " MB"
    }

    return (
      <>
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
                  fontSize={fs.param}
                  labelSize={fs.label}
                />
                <MetadataRow label="File Size" value={formatFileSize(metadata.fileSize)} fontSize={fs.param} labelSize={fs.label} />
                <MetadataRow label="File Type" value={metadata.fileType} fontSize={fs.param} labelSize={fs.label} />
                <MetadataRow label="Last Modified" value={new Date(metadata.lastModified).toLocaleString()} fontSize={fs.param} labelSize={fs.label} />
              </>
            )}

            {activeTab === "exif" && (
              <>
                {Object.keys(metadata.exif || {}).length === 0 ? (
                  <Empty className="border-0 py-6">
                    <EmptyHeader>
                      <EmptyMedia variant="icon"><Camera /></EmptyMedia>
                      <EmptyTitle>No EXIF data</EmptyTitle>
                      <EmptyDescription>Camera settings will appear here</EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                ) : (
                  <>
                    <FileBasics metadata={metadata} formatFileSize={formatFileSize} fontSize={fs} />
                    {Object.entries(metadata.exif || {}).map(([key, value]) => {
                      const display = toDisplayString(value)
                      if (!display) return null
                      return (
                        <MetadataRow
                          key={key}
                          label={key}
                          value={display}
                          onCopy={() => copyToClipboard(display, `exif-${key}`)}
                          copied={copiedValue === `exif-${key}`}
                          fontSize={fs.param}
                          labelSize={fs.label}
                        />
                      )
                    })}
                  </>
                )}
              </>
            )}

            {activeTab === "iptc" && (
              <>
                {Object.keys(metadata.iptc || {}).length === 0 ? (
                  <Empty className="border-0 py-6">
                    <EmptyHeader>
                      <EmptyMedia variant="icon"><FileText /></EmptyMedia>
                      <EmptyTitle>No IPTC data</EmptyTitle>
                      <EmptyDescription>Copyright and keywords will appear here</EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                ) : (
                  Object.entries(metadata.iptc || {}).map(([key, value]) => {
                    const display = toDisplayString(value)
                    if (!display) return null
                    return (
                      <MetadataRow
                        key={key}
                        label={key}
                        value={display}
                        onCopy={() => copyToClipboard(display, `iptc-${key}`)}
                        copied={copiedValue === `iptc-${key}`}
                        fontSize={fs.param}
                        labelSize={fs.label}
                      />
                    )
                  })
                )}
              </>
            )}

            {activeTab === "xmp" && (
              <>
                {Object.keys(metadata.xmp || {}).length === 0 ? (
                  <Empty className="border-0 py-6">
                    <EmptyHeader>
                      <EmptyMedia variant="icon"><Code /></EmptyMedia>
                      <EmptyTitle>No XMP data</EmptyTitle>
                      <EmptyDescription>Adobe metadata will appear here</EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                ) : (
                  Object.entries(metadata.xmp || {}).map(([key, value]) => {
                    const display = toDisplayString(value)
                    if (!display) return null
                    return (
                      <MetadataRow
                        key={key}
                        label={key}
                        value={display}
                        onCopy={() => copyToClipboard(display, `xmp-${key}`)}
                        copied={copiedValue === `xmp-${key}`}
                        mono
                        fontSize={fs.param}
                        labelSize={fs.label}
                      />
                    )
                  })
                )}
              </>
            )}

            {activeTab === "ai" && (
              <AITab
                ai={metadata.ai}
                metadata={metadata}
                copiedValue={copiedValue}
                onCopy={copyToClipboard}
                fontSize={fs}
                formatFileSize={formatFileSize}
              />
            )}

            {activeTab === "rules" && (
              <div className="space-y-4">
                <div>
                  <label htmlFor="rule-condition" className="block text-sm font-medium text-muted-foreground mb-1">
                    Rule Condition (e.g., exif.Make === &apos;Canon&apos;)
                  </label>
                  <input
                    id="rule-condition"
                    type="text"
                    value={ruleCondition}
                    onChange={(e) => setRuleCondition(e.target.value)}
                    className="w-full p-2 border border-border rounded-md bg-background text-foreground"
                    placeholder="Enter rule condition"
                  />
                </div>
                <button
                  onClick={handleApplyRules}
                  disabled={isApplyingRules}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                >
                  {isApplyingRules && <Loader2 className="w-4 h-4 animate-spin" />}
                  Apply Rules
                </button>

                {ruleResults && (
                  <div className="mt-4 space-y-2">
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                      Rule Evaluation Results
                    </h3>
                    {ruleResults.map((result) => (
                      <div key={result.ruleId} className="p-3 border border-border rounded-md bg-muted/50">
                        <p className="text-sm font-medium">{result.ruleName}</p>
                        <p className={`text-xs ${result.passed ? "text-green-500" : "text-red-500"}`}>
                          Status: {result.passed ? "PASSED" : "FAILED"}
                        </p>
                        {result.message && <p className="text-xs text-muted-foreground">{result.message}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-10 border-b border-border px-4 flex items-center bg-muted/20">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Metadata</h2>
      </div>

      {renderContent()}
    </div>
  )
}

// --- AI Tab ---

interface AITabProps {
  ai: Record<string, unknown>
  metadata: ImageMetadata
  copiedValue: string | null
  onCopy: (text: string, key: string) => void
  fontSize: { prompt: string; param: string; label: string }
  formatFileSize: (bytes: number) => string
}

function AITab({ ai, metadata, copiedValue, onCopy, fontSize: fs, formatFileSize }: AITabProps) {
  if (Object.keys(ai || {}).length === 0) {
    return (
      <Empty className="border-0 py-6">
        <EmptyHeader>
          <EmptyMedia variant="icon"><Sparkles /></EmptyMedia>
          <EmptyTitle>No AI data</EmptyTitle>
          <EmptyDescription>
            Generation prompts, model info, and sampling parameters will appear here
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }

  const workflowType = toDisplayString(ai.workflow_type) || undefined
  const prompt = toDisplayString(ai.prompt) || undefined
  const negativePrompt = toDisplayString(ai.negative_prompt) || undefined
  const loras = Array.isArray(ai.loras)
    ? (ai.loras as unknown[]).map(toDisplayString).filter(Boolean)
    : undefined

  // Build ordered params from known keys first, then remaining
  const knownParams: [string, string][] = []
  for (const key of PARAM_ORDER) {
    if (ai[key] !== undefined && !HIDDEN_KEYS.has(key)) {
      const display = toDisplayString(ai[key])
      if (display) knownParams.push([key, display])
    }
  }
  // Remaining keys not in known order or hidden
  const shownKeys = new Set([...PARAM_ORDER, ...HIDDEN_KEYS])
  const extraParams: [string, string][] = []
  for (const [key, val] of Object.entries(ai)) {
    if (shownKeys.has(key)) continue
    const display = toDisplayString(val)
    if (display) extraParams.push([key, display])
  }

  return (
    <div className="space-y-4">
      {/* File Basics */}
      <FileBasics metadata={metadata} formatFileSize={formatFileSize} fontSize={fs} />

      {/* Workflow Type Badge */}
      {workflowType && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
            <Sparkles className="w-3 h-3" />
            {workflowType}
          </span>
        </div>
      )}

      {/* Prompt */}
      {prompt && (
        <PromptSection
          label="Prompt"
          text={prompt}
          copyKey="ai-prompt"
          copiedValue={copiedValue}
          onCopy={onCopy}
          fontSize={fs.prompt}
          labelSize={fs.label}
        />
      )}

      {/* Negative Prompt */}
      {negativePrompt && (
        <PromptSection
          label="Negative Prompt"
          text={negativePrompt}
          copyKey="ai-negative_prompt"
          copiedValue={copiedValue}
          onCopy={onCopy}
          fontSize={fs.prompt}
          labelSize={fs.label}
          negative
        />
      )}

      {/* LoRAs as chips */}
      {loras && loras.length > 0 && (
        <div className="space-y-1.5">
          <p className={`font-medium text-muted-foreground uppercase tracking-wide ${fs.label}`}>LoRAs</p>
          <div className="flex flex-wrap gap-1.5">
            {loras.map((lora, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-accent text-accent-foreground border border-border"
              >
                <Tag className="w-3 h-3" />
                {lora}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Parameter Grid */}
      {(knownParams.length > 0 || extraParams.length > 0) && (
        <div className="space-y-1">
          <p className={`font-medium text-muted-foreground uppercase tracking-wide mb-2 ${fs.label}`}>Parameters</p>
          <div className="grid grid-cols-2 gap-x-3 gap-y-2">
            {[...knownParams, ...extraParams].map(([key, value]) => (
              <div key={key} className="min-w-0">
                <p className={`text-muted-foreground truncate ${fs.label}`}>{formatLabel(key)}</p>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <p className={`font-mono truncate ${fs.param}`}>{value}</p>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs break-all">{value}</TooltipContent>
                </Tooltip>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// --- Prompt Section ---

function PromptSection({
  label,
  text,
  copyKey,
  copiedValue,
  onCopy,
  fontSize,
  labelSize,
  negative = false,
}: {
  label: string
  text: string
  copyKey: string
  copiedValue: string | null
  onCopy: (text: string, key: string) => void
  fontSize: string
  labelSize: string
  negative?: boolean
}) {
  const copied = copiedValue === copyKey

  return (
    <div className={`rounded-lg border p-3 ${negative ? 'border-red-500/20 bg-red-500/5' : 'border-border bg-muted/30'}`}>
      <div className="flex items-center justify-between mb-1.5">
        <p className={`font-medium text-muted-foreground uppercase tracking-wide ${labelSize}`}>{label}</p>
        <button
          onClick={() => onCopy(text, copyKey)}
          className="p-1 hover:bg-accent rounded transition-colors"
          aria-label={`Copy ${label}`}
        >
          {copied ? (
            <Check className="w-3.5 h-3.5 text-green-500" />
          ) : (
            <Copy className="w-3.5 h-3.5 text-muted-foreground" />
          )}
        </button>
      </div>
      <p className={`whitespace-pre-wrap break-words leading-relaxed ${fontSize}`}>{text}</p>
    </div>
  )
}

// --- Shared Components ---

function FileBasics({
  metadata,
  formatFileSize,
  fontSize: fs,
}: {
  metadata: ImageMetadata
  formatFileSize: (bytes: number) => string
  fontSize: { prompt: string; param: string; label: string }
}) {
  return (
    <div className="rounded-lg border border-border bg-muted/20 p-2.5">
      <div className="grid grid-cols-2 gap-x-3 gap-y-1">
        <div className="min-w-0">
          <p className={`text-muted-foreground ${fs.label}`}>File</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className={`font-medium truncate ${fs.param}`}>{metadata.fileName}</p>
            </TooltipTrigger>
            <TooltipContent>{metadata.fileName}</TooltipContent>
          </Tooltip>
        </div>
        <div className="min-w-0">
          <p className={`text-muted-foreground ${fs.label}`}>Size</p>
          <p className={`font-mono ${fs.param}`}>{formatFileSize(metadata.fileSize)}</p>
        </div>
        <div className="min-w-0">
          <p className={`text-muted-foreground ${fs.label}`}>Type</p>
          <p className={`${fs.param}`}>{metadata.fileType}</p>
        </div>
        <div className="min-w-0">
          <p className={`text-muted-foreground ${fs.label}`}>Modified</p>
          <p className={`${fs.param}`}>{new Date(metadata.lastModified).toLocaleDateString()}</p>
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
  fontSize?: string
  labelSize?: string
}

function MetadataRow({ label, value, onCopy, copied, mono = false, fontSize = 'text-sm', labelSize = 'text-xs' }: MetadataRowProps) {
  return (
    <div className="flex items-start gap-2 py-2 px-3 rounded-lg hover:bg-accent/50 transition-colors group">
      <div className="flex-1 min-w-0">
        <p className={`font-medium text-muted-foreground uppercase tracking-wide mb-1 ${labelSize}`}>{label}</p>
        <p className={`break-words ${fontSize} ${mono ? "font-mono" : ""}`}>{value}</p>
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
