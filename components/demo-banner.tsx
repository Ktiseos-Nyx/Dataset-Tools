"use client"

import { useState } from "react"
import { X, Info, Github, Coffee, Cloud } from "lucide-react"

export function DemoBanner() {
  const [dismissed, setDismissed] = useState(false)
  const [showAbout, setShowAbout] = useState(false)

  if (dismissed) return null

  return (
    <>
      <div className="flex items-center justify-between gap-3 px-4 py-1.5 bg-primary/10 border-b border-primary/20 text-xs">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-primary">Demo</span>
          <span className="text-muted-foreground hidden sm:inline">
            Single-image metadata viewer
          </span>
          <button
            onClick={() => setShowAbout(true)}
            className="flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors"
          >
            <Info className="w-3 h-3" /> About
          </button>
          <span className="flex items-center gap-2">
            <a
              href="https://github.com/Ktiseos-Nyx/Dataset-Tools"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors"
            >
              <Github className="w-3 h-3" /> GitHub
            </a>
            <a
              href="https://ko-fi.com/duskfallcrew"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors"
            >
              <Coffee className="w-3 h-3" /> Support
            </a>
            <a
              href="https://cloud.vast.ai/?ref_id=70354"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors"
            >
              <Cloud className="w-3 h-3" /> GPU Rentals
            </a>
          </span>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="p-0.5 hover:bg-primary/10 rounded transition-colors"
          aria-label="Dismiss banner"
        >
          <X className="w-3 h-3 text-muted-foreground" />
        </button>
      </div>

      {showAbout && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowAbout(false)}>
          <div className="bg-background border border-border rounded-xl shadow-xl max-w-md w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-lg font-semibold">About this demo</h2>
              <button onClick={() => setShowAbout(false)} className="p-1 hover:bg-accent rounded transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>
                This is a <strong className="text-foreground">single-image demo</strong> of Dataset Tools, an AI metadata viewer
                for images generated with Stable Diffusion, ComfyUI, NovelAI, and other tools.
              </p>
              <p>
                <strong className="text-foreground">What you can do here:</strong> Drop or select an image to see
                its full metadata — prompts, generation parameters, EXIF, IPTC, XMP, and AI-specific details
                like LoRA models and ComfyUI workflow info.
              </p>
              <p>
                <strong className="text-foreground">What&apos;s different from the full app:</strong> The desktop
                version lets you browse entire folders, view thumbnails, edit metadata inline, and manage
                image collections. This demo only shows one image at a time.
              </p>
              <p>
                <a
                  href="https://github.com/Ktiseos-Nyx/Dataset-Tools"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-medium"
                >
                  Get the full app on GitHub →
                </a>
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
