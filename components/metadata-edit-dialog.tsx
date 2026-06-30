"use client"

import { useState } from "react"
import { Pencil, Loader2, Save } from "lucide-react"
import { toast } from "sonner"
import { Button, buttonVariants } from "@/components/ui/button"
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
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog"

interface MetadataEditDialogProps {
  /** Server path of the selected file (relative or absolute, as the fs tree provides it). */
  filePath: string
  /** The folder the path is resolved against — passed straight to the API. */
  baseFolder: string
  fileName: string
  /** Called after a successful in-place overwrite so the panel can re-read the file. */
  onSaved?: () => void
}

// name.png -> name.edited.png (for the "save as copy" hint and toast preview)
function copyName(fileName: string): string {
  const dot = fileName.lastIndexOf(".")
  if (dot === -1) return `${fileName}.edited`
  return `${fileName.slice(0, dot)}.edited${fileName.slice(dot)}`
}

export function MetadataEditDialog({ filePath, baseFolder, fileName, onSaved }: MetadataEditDialogProps) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState("")
  const [original, setOriginal] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveAsCopy, setSaveAsCopy] = useState(true)
  const [confirmOpen, setConfirmOpen] = useState(false)

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
      setOpen(false)
      if (!saveAsCopy) onSaved?.()
    } catch (e) {
      toast.error(`Save failed: ${(e as Error).message}`)
    } finally {
      setSaving(false)
      setConfirmOpen(false)
    }
  }

  const handleSaveClick = () => {
    if (saveAsCopy) void doSave()
    else setConfirmOpen(true)
  }

  // Nothing to save until the text actually differs from what's on disk.
  const dirty = original !== null ? text !== original : text.trim().length > 0

  return (
    <>
      <Button variant="outline" size="xs" onClick={() => handleOpenChange(true)} title="Edit raw metadata">
        <Pencil />
        Edit
      </Button>

      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-2xl">
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
                spellCheck={false}
                aria-label="Raw metadata"
                className="font-mono text-xs min-h-[320px] max-h-[60vh] resize-y whitespace-pre overflow-auto"
                placeholder={"masterpiece, best quality, … <lora:Name:1.0>\nNegative prompt: …\nSteps: 30, Sampler: …"}
              />
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox
                  checked={saveAsCopy}
                  onCheckedChange={(v) => setSaveAsCopy(v === true)}
                />
                Save as a copy (<code className="text-foreground">{copyName(fileName)}</code>) — keeps the original untouched
              </label>
            </div>
          )}

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={saving}>
                Cancel
              </Button>
            </DialogClose>
            <Button onClick={handleSaveClick} disabled={loading || saving || !dirty}>
              {saving ? <Loader2 className="animate-spin" /> : <Save />}
              {saveAsCopy ? "Save copy" : "Overwrite original"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Overwrite the original?</AlertDialogTitle>
            <AlertDialogDescription>
              This writes directly over{" "}
              <span className="font-medium text-foreground">{fileName}</span>. The pixels stay
              untouched, but the previous metadata can&apos;t be recovered. Prefer “Save as a copy”
              if you&apos;re unsure.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={saving}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className={buttonVariants({ variant: "destructive" })}
              onClick={(e) => {
                e.preventDefault()
                void doSave()
              }}
              disabled={saving}
            >
              {saving ? <Loader2 className="animate-spin" /> : null}
              Overwrite
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
