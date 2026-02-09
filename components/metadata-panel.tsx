"use client"

import { useState } from "react"
import { Copy, Camera, FileText, Sparkles, Code, Check, Loader2, ListTree } from "lucide-react"
import type { ImageMetadata } from "@/types/metadata"
import type { Rule, RuleEvaluationResult } from "@/types/rules"

interface MetadataPanelProps {
  metadata: ImageMetadata | null
  isLoading: boolean
}

export function MetadataPanel({ metadata, isLoading }: MetadataPanelProps) {
  const [activeTab, setActiveTab] = useState<"basic" | "exif" | "iptc" | "xmp" | "ai" | "rules">("basic")
  const [copiedValue, setCopiedValue] = useState<string | null>(null)
  const [ruleCondition, setRuleCondition] = useState<string>("exif.Make === 'Canon'")
  const [ruleResults, setRuleResults] = useState<RuleEvaluationResult[] | null>(null)
  const [isApplyingRules, setIsApplyingRules] = useState(false)
  const [civitaiModelId, setCivitaiModelId] = useState<string>("")
  const [isFetchingCivitai, setIsFetchingCivitai] = useState(false)
  const [civitaiError, setCivitaiError] = useState<string | null>(null)
  const [civitaiData, setCivitaiData] = useState<any>(null)

  const handleApplyRules = async () => {
    if (!metadata) return;

    setIsApplyingRules(true);
    setRuleResults(null);

    try {
      const mockRule: Rule = {
        id: "rule-1",
        name: "Check Camera Make",
        condition: ruleCondition,
        action: "flag",
        value: "CameraMakeFlag",
      };

      const response = await fetch('/api/rules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rules: [mockRule], metadata }),
      });

      if (!response.ok) {
        throw new Error('Failed to apply rules');
      }

      const results: RuleEvaluationResult[] = await response.json();
      setRuleResults(results);
    } catch (error) {
      console.error("Error applying rules:", error);
      setRuleResults([{
        ruleId: "error",
        ruleName: "Error",
        passed: false,
        message: (error as Error).message,
      }]);
    } finally {
      setIsApplyingRules(false);
    }
  };

  const fetchCivitaiData = async () => {
    if (!civitaiModelId) return;

    setIsFetchingCivitai(true);
    setCivitaiError(null);
    setCivitaiData(null);

    try {
      const response = await fetch(`https://civitai.com/api/v1/models/${civitaiModelId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch Civitai data: ${response.statusText}`);
      }

      const data = await response.json();
      setCivitaiData(data);
    } catch (error) {
      console.error("Error fetching Civitai data:", error);
      setCivitaiError((error as Error).message);
    } finally {
      setIsFetchingCivitai(false);
    }
  };


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
        <div className="flex-1 flex items-center justify-center p-6">
          <p className="text-sm text-muted-foreground">Select a file to view metadata</p>
        </div>
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
  
    const copyToClipboard = (text: string, key: string) => {
      navigator.clipboard.writeText(text)
      setCopiedValue(key)
      setTimeout(() => setCopiedValue(null), 2000)
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
                  Object.entries(metadata.ai || {})
                    .filter(([key]) => key !== 'comfyui_workflow') // raw workflow shown separately if needed
                    .map(([key, value]) => {
                      const display = (typeof value === 'object' && value !== null)
                        ? (Array.isArray(value) ? value.join(', ') : JSON.stringify(value, null, 2))
                        : String(value);
                      return (
                        <MetadataRow
                          key={key}
                          label={key}
                          value={display}
                          onCopy={() => copyToClipboard(display, `ai-${key}`)}
                          copied={copiedValue === `ai-${key}`}
                          mono
                        />
                      );
                    })
                )}
                <div className="border-t border-border pt-4 mt-4">
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">Civitai Integration</h3>
                  <div className="space-y-2">
                    <div>
                      <label htmlFor="civitai-model-id" className="block text-sm font-medium text-muted-foreground mb-1">
                        Civitai Model ID
                      </label>
                      <input
                        id="civitai-model-id"
                        type="text"
                        value={civitaiModelId}
                        onChange={(e) => setCivitaiModelId(e.target.value)}
                        className="w-full p-2 border border-border rounded-md bg-background text-foreground"
                        placeholder="Enter Civitai Model ID"
                      />
                    </div>
                    <button
                      onClick={fetchCivitaiData}
                      disabled={isFetchingCivitai || !civitaiModelId}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                    >
                      {isFetchingCivitai && <Loader2 className="w-4 h-4 animate-spin" />}
                      Fetch Civitai Data
                    </button>

                    {civitaiError && (
                      <div className="text-red-500 text-sm mt-2">{civitaiError}</div>
                    )}

                    {civitaiData && (
                      <div className="mt-4 space-y-2">
                        <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                          Civitai Model Details
                        </h4>
                        <MetadataRow label="Name" value={civitaiData.name} />
                        <MetadataRow label="Type" value={civitaiData.type} />
                        <MetadataRow label="Creator" value={civitaiData.creator.username} />
                        <MetadataRow label="Downloads" value={String(civitaiData.downloadCount)} />
                        {/* You can add more fields from civitaiData here */}
                        <details className="text-sm text-muted-foreground">
                          <summary>Raw Data</summary>
                          <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                            {JSON.stringify(civitaiData, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {activeTab === "rules" && (
              <div className="space-y-4">
                <div>
                  <label htmlFor="rule-condition" className="block text-sm font-medium text-muted-foreground mb-1">
                    Rule Condition (e.g., exif.Make === 'Canon')
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
