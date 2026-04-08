"use client"

import { useState } from "react"
import { Brain, ChevronDown, ChevronRight, Copy, Check } from "lucide-react"
import type { SafetensorsMetadata } from "@/types/safetensors"
import { cn } from "@/lib/utils"

interface SafetensorsPanelProps {
  data: SafetensorsMetadata | null
  isLoading: boolean
  fileName?: string
}

function Section({
  title,
  children,
  defaultOpen = true,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 bg-muted/40 hover:bg-muted/70 transition-colors text-left"
      >
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</span>
        {open ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" /> : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />}
      </button>
      {open && <div className="p-3 space-y-1.5">{children}</div>}
    </div>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  if (value === undefined || value === null || value === "") return null
  return (
    <div className="flex gap-2 text-xs">
      <span className="text-muted-foreground shrink-0 w-32">{label}</span>
      <span className="font-medium break-all">{String(value)}</span>
    </div>
  )
}

function TagCloud({ tagFrequency }: { tagFrequency: Record<string, Record<string, number>> }) {
  // Merge all directory tag counts
  const merged: Record<string, number> = {}
  for (const tags of Object.values(tagFrequency)) {
    for (const [tag, count] of Object.entries(tags)) {
      merged[tag] = (merged[tag] ?? 0) + count
    }
  }

  const sorted = Object.entries(merged)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 40)

  if (sorted.length === 0) return null

  const max = sorted[0][1]

  return (
    <div className="flex flex-wrap gap-1">
      {sorted.map(([tag, count]) => {
        const intensity = count / max
        return (
          <span
            key={tag}
            title={`${tag}: ${count}`}
            className={cn(
              "px-1.5 py-0.5 rounded text-[10px] font-medium border",
              intensity > 0.66
                ? "bg-primary/20 border-primary/40 text-primary"
                : intensity > 0.33
                ? "bg-muted border-border text-muted-foreground"
                : "bg-muted/50 border-border/50 text-muted-foreground/70"
            )}
          >
            {tag}
          </span>
        )
      })}
    </div>
  )
}

function RawJson({ data }: { data: Record<string, unknown> }) {
  const [copied, setCopied] = useState(false)
  const text = JSON.stringify(data, null, 2)

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="relative">
      <button
        onClick={handleCopy}
        className="absolute top-1 right-1 p-1 rounded hover:bg-accent transition-colors z-10"
        title="Copy JSON"
      >
        {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3 text-muted-foreground" />}
      </button>
      <pre className="text-[10px] leading-relaxed overflow-x-auto bg-muted/30 rounded p-2 pr-6 max-h-64 whitespace-pre-wrap break-all">
        {text}
      </pre>
    </div>
  )
}

export function SafetensorsPanel({ data, isLoading, fileName }: SafetensorsPanelProps) {
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-2">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-muted-foreground">Reading model metadata…</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Select a .safetensors file to view metadata</p>
      </div>
    )
  }

  const displayName = data.outputName
    ? String(data.outputName)
    : fileName?.replace(/\.safetensors$/i, "") ?? "Unknown"

  const hasLoraData = !!data.lora
  const hasTraining = !!data.training
  const hasDataset = !!data.dataset
  const hasModelSpec = !!data.modelSpec && Object.keys(data.modelSpec).length > 0

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      {/* Header */}
      <div className="flex items-start gap-2.5">
        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
          <Brain className="w-5 h-5 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold truncate" title={displayName}>{displayName}</p>
          <p className="text-xs text-muted-foreground">
            {data.tensorCount.toLocaleString()} tensors
            {data.baseModel?.version && ` · ${data.baseModel.version}`}
            {data.lora && ` · LoRA`}
          </p>
        </div>
      </div>

      {/* Base Model */}
      {data.baseModel && (
        <Section title="Base Model">
          <Row label="Model" value={data.baseModel.name} />
          <Row label="Version" value={data.baseModel.version} />
          <Row label="Hash" value={data.baseModel.hash} />
          {data.baseModel.isV2 && <Row label="SD v2" value="Yes" />}
        </Section>
      )}

      {/* LoRA Architecture */}
      {hasLoraData && (
        <Section title="LoRA Architecture">
          <Row label="Rank (dim)" value={data.lora!.dim} />
          <Row label="Alpha" value={data.lora!.alpha} />
          <Row label="Network" value={data.lora!.networkModule} />
          {data.lora!.networkArgs && (
            <Row label="Network Args" value={JSON.stringify(data.lora!.networkArgs)} />
          )}
        </Section>
      )}

      {/* Training */}
      {hasTraining && (
        <Section title="Training">
          <Row label="Epochs" value={data.training!.epoch !== undefined
            ? `${data.training!.epoch} / ${data.training!.epochs ?? "?"}`
            : data.training!.epochs} />
          <Row label="Steps" value={data.training!.steps?.toLocaleString()} />
          <Row label="Batch Size" value={data.training!.batchSize} />
          <Row label="Grad Accum" value={data.training!.gradientAccumulationSteps} />
          <Row label="Learning Rate" value={data.training!.learningRate} />
          <Row label="UNet LR" value={data.training!.unetLr} />
          <Row label="TE LR" value={data.training!.textEncoderLr} />
          <Row label="LR Scheduler" value={data.training!.lrScheduler} />
          <Row label="LR Warmup" value={data.training!.lrWarmupSteps} />
          <Row label="Optimizer" value={data.training!.optimizer} />
          <Row label="Precision" value={data.training!.mixedPrecision} />
          <Row label="Noise Offset" value={data.training!.noiseOffset} />
          <Row label="Max Grad Norm" value={data.training!.maxGradNorm} />
          {data.training!.fullFp16 && <Row label="Full FP16" value="Yes" />}
        </Section>
      )}

      {/* Dataset */}
      {hasDataset && (
        <Section title="Dataset">
          <Row label="Train Images" value={data.dataset!.numTrainImages?.toLocaleString()} />
          <Row label="Reg Images" value={data.dataset!.numRegImages?.toLocaleString()} />
          {data.dataset!.tagFrequency && (
            <div className="pt-1 space-y-1.5">
              <p className="text-xs text-muted-foreground">Top Tags</p>
              <TagCloud tagFrequency={data.dataset!.tagFrequency} />
            </div>
          )}
        </Section>
      )}

      {/* Model Spec */}
      {hasModelSpec && (
        <Section title="Model Spec" defaultOpen={false}>
          {Object.entries(data.modelSpec!).map(([k, v]) => (
            <Row key={k} label={k} value={typeof v === 'object' ? JSON.stringify(v) : String(v ?? '')} />
          ))}
        </Section>
      )}

      {/* AutoV2 Hash */}
      {data.autoV2Hash && (
        <Section title="Civitai" defaultOpen={false}>
          <Row label="AutoV2 Hash" value={data.autoV2Hash} />
        </Section>
      )}

      {/* Raw Metadata */}
      <Section title="All Fields" defaultOpen={false}>
        <RawJson data={data.raw} />
      </Section>
    </div>
  )
}
