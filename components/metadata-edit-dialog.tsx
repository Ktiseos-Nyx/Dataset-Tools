"use client"

import { useState } from "react"
import { Pencil, Loader2, Save, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"

interface MetadataEditDialogProps {
  /** Server path of the selected file (relative or absolute, as the fs tree provides it). */
  filePath: string
  /** The folder the path is resolved against — passed straight to the API. */
  baseFolder: string
  fileName: string
  /** Called after a successful save so the parent can refresh metadata/thumbnails. */
  onSaved?: () => void
}

// name.png -> name_edited.png (underscore keeps a single-extension stem so
// dataset/training tools that pair by stem don't orphan the file).
function copyName(fileName: string): string {
  const dot = fileName.lastIndexOf(".")
  if (dot === -1) return `${fileName}_edited`
  return `${fileName.slice(0, dot)}_edited${fileName.slice(dot)}`
}

export function MetadataEditDialog({ filePath, baseFolder, fileName, onSaved }: MetadataEditDialogProps) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState("")
  const [original, setOriginal] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveAsCopy, setSaveAsCopy] = useState(true)
  // Inline overwrite confirmation — kept in this single Dialog rather than a
  // nested AlertDialog, because stacking two Radix modals (and unmounting them
  // together) leaves `pointer-events: none` stuck on <body> and freezes the UI.
  const [confirmingOverwrite, setConfirmingOverwrite] = useState(false)

  const query = `path=${encodeURIComponent(filePath)}&baseFolder=${encodeURIComponent(baseFolder)}`

  const loadParameters = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/metadata-write?${query}`)
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "Failed to read metadata")
      setOriginal(data.text ?? null)
      setText(data.text ?? "")
    } catch (e) {
      toast.error(`Could not read metadata: ${(e as Error).message}`)
      setOriginal(null)
      setText("")
    } finally {
      setLoading(false)
    }
  }

  const handleOpenChange = (next: boolean) => {
    setOpen(next)
    if (next) {
      setSaveAsCopy(true)
      setConfirmingOverwrite(false)
      void loadParameters()
    }
  }

  const doSave = async () => {
    setSaving(true)
    try {
      const res = await fetch("/api/metadata-write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: filePath, baseFolder, text, saveAsCopy }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "Save failed")
      toast.success(saveAsCopy ? `Saved copy: ${data.path}` : `Saved ${data.path}`)
      // Re-baseline so reopening reflects the saved state (and Save disables).
      setOriginal(text)
      setConfirmingOverwrite(false)
      setOpen(false)
      onSaved?.()
    } catch (e) {
      toast.error(`Save failed: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveClick = () => {
    if (saveAsCopy) void doSave()
    else setConfirmingOverwrite(true)
  }

  // Nothing to save until the text actually differs from what's on disk.
  const dirty = original !== null ? text !== original : text.trim().length > 0

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <Button variant="outline" size="xs" onClick={() => handleOpenChange(true)} title="Edit raw metadata">
        <Pencil />
        Edit
      </Button>

      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit metadata</DialogTitle>
          <DialogDescription>
            Raw <code>parameters</code> text for{" "}
            <span className="font-medium text-foreground">{fileName}</span>. Pixels are never
            recompressed — only this block changes.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Reading…
          </div>
        ) : (
          <div className="space-y-3">
            {original === null && (
              <p className="text-xs text-amber-500">
                This PNG has no <code>parameters</code> block yet. Saving will create one.
              </p>
            )}
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={saving}
              spellCheck={false}
              aria-label="Raw metadata"
              className="font-mono text-xs min-h-[320px] max-h-[60vh] w-full min-w-0 resize-y [field-sizing:fixed] whitespace-pre-wrap break-words overflow-y-auto"
              placeholder={"masterpiece, best quality, … <lora:Name:1.0>\nNegative prompt: …\nSteps: 30, Sampler: …"}
            />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox
                checked={saveAsCopy}
                disabled={saving}
                onCheckedChange={(v) => {
                  setSaveAsCopy(v === true)
                  setConfirmingOverwrite(false)
                }}
              />
              Save as a copy (<code className="text-foreground">{copyName(fileName)}</code>) — keeps the original untouched
            </label>
          </div>
        )}

        {confirmingOverwrite && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0 text-destructive" />
            <span>
              Overwrite the original <span className="font-medium">{fileName}</span>? Pixels stay
              intact, but the previous metadata can&apos;t be recovered.
            </span>
          </div>
        )}

        <DialogFooter>
          {confirmingOverwrite ? (
            <>
              <Button variant="outline" onClick={() => setConfirmingOverwrite(false)} disabled={saving}>
                Back
              </Button>
              <Button variant="destructive" onClick={() => void doSave()} disabled={saving}>
                {saving ? <Loader2 className="animate-spin" /> : null}
                Yes, overwrite
              </Button>
            </>
          ) : (
            <>
              <DialogClose asChild>
                <Button variant="outline" disabled={saving}>
                  Cancel
                </Button>
              </DialogClose>
              <Button onClick={handleSaveClick} disabled={loading || saving || !dirty}>
                {saving ? <Loader2 className="animate-spin" /> : <Save />}
                {saveAsCopy ? "Save copy" : "Overwrite original"}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
