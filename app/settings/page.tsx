"use client"

import { useState, useEffect } from "react"
import { useTheme } from "next-themes"
import { Save, Eye, EyeOff, Check } from "lucide-react"
import { useSettings } from "@/hooks/use-settings"
import type { AppSettings } from "@/types/settings"

export default function SettingsPage() {
  const { settings, updateSettings } = useSettings()
  const { theme, setTheme } = useTheme()
  const [civitaiKey, setCivitaiKey] = useState("")
  const [showCivitaiKey, setShowCivitaiKey] = useState(false)
  const [hasCivitaiKey, setHasCivitaiKey] = useState(false)
  const [civitaiSaved, setCivitaiSaved] = useState(false)

  const [githubToken, setGithubToken] = useState("")
  const [showGithubToken, setShowGithubToken] = useState(false)
  const [hasGithubToken, setHasGithubToken] = useState(false)
  const [githubSaved, setGithubSaved] = useState(false)

  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check if server has saved keys
    fetch("/api/settings")
      .then(res => res.json())
      .then(data => {
        setHasCivitaiKey(data.secrets?.hasCivitaiApiKey ?? false)
        setHasGithubToken(data.secrets?.hasGithubToken ?? false)
      })
      .catch(() => {})
  }, [])

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme)
    updateSettings({ theme: newTheme as AppSettings["theme"] })
  }

  const handleSaveCivitaiKey = async () => {
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secrets: { civitaiApiKey: civitaiKey } }),
      })
      setHasCivitaiKey(!!civitaiKey)
      setCivitaiKey("")
      setCivitaiSaved(true)
      setTimeout(() => setCivitaiSaved(false), 2000)
    } catch (err) {
      console.error("Failed to save Civitai API key:", err)
    }
  }

  const handleSaveGithubToken = async () => {
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secrets: { githubToken: githubToken } }),
      })
      setHasGithubToken(!!githubToken)
      setGithubToken("")
      setGithubSaved(true)
      setTimeout(() => setGithubSaved(false), 2000)
    } catch (err) {
      console.error("Failed to save GitHub token:", err)
    }
  }

  if (!mounted) return null

  return (
    <div className="h-full overflow-y-auto bg-background">
      <div className="max-w-2xl mx-auto p-6 space-y-8">
        <h1 className="text-lg font-semibold">Settings</h1>
        {/* Appearance */}
        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Appearance</h2>

          {/* Theme */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Theme</label>
            <div className="flex gap-2">
              {(["light", "dark", "system"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => handleThemeChange(t)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                    theme === t
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-accent text-foreground"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Font Size */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Metadata Font Size</label>
            <div className="flex gap-2">
              {([
                { value: "sm", label: "Small" },
                { value: "md", label: "Medium" },
                { value: "lg", label: "Large" },
              ] as const).map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => updateSettings({ fontSize: opt.value })}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    settings.fontSize === opt.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-accent text-foreground"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Thumbnail Size */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Thumbnail Size</label>
            <div className="flex gap-2">
              {([
                { value: "sm", label: "Small" },
                { value: "md", label: "Medium" },
                { value: "lg", label: "Large" },
              ] as const).map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => updateSettings({ thumbnailSize: opt.value })}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    settings.thumbnailSize === opt.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-accent text-foreground"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* File Browser */}
        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">File Browser</h2>

          {/* Hidden Files */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Show Hidden Files</p>
              <p className="text-xs text-muted-foreground">Display dotfiles and hidden directories</p>
            </div>
            <button
              onClick={() => updateSettings({ showHiddenFiles: !settings.showHiddenFiles })}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                settings.showHiddenFiles ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                  settings.showHiddenFiles ? "translate-x-5" : ""
                }`}
              />
            </button>
          </div>

          {/* File Extensions */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Show File Extensions</p>
              <p className="text-xs text-muted-foreground">Display file extensions in the tree</p>
            </div>
            <button
              onClick={() => updateSettings({ showFileExtensions: !settings.showFileExtensions })}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                settings.showFileExtensions ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                  settings.showFileExtensions ? "translate-x-5" : ""
                }`}
              />
            </button>
          </div>
        </section>

        {/* API Keys */}
        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">API Keys</h2>

          {/* Civitai */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Civitai API Key</label>
            {hasCivitaiKey && (
              <p className="text-xs text-green-600 dark:text-green-400">Key is saved in .env.local</p>
            )}
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showCivitaiKey ? "text" : "password"}
                  value={civitaiKey}
                  onChange={(e) => setCivitaiKey(e.target.value)}
                  placeholder={hasCivitaiKey ? "Enter new key to replace" : "Enter Civitai API key"}
                  className="w-full p-2 pr-10 border border-border rounded-lg bg-background text-sm"
                />
                <button
                  onClick={() => setShowCivitaiKey(!showCivitaiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                >
                  {showCivitaiKey ? <EyeOff className="w-3.5 h-3.5 text-muted-foreground" /> : <Eye className="w-3.5 h-3.5 text-muted-foreground" />}
                </button>
              </div>
              <button
                onClick={handleSaveCivitaiKey}
                disabled={!civitaiKey}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                {civitaiSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                {civitaiSaved ? "Saved" : "Save"}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              Stored server-side in .env.local. Never sent to the browser.
            </p>
          </div>

          {/* GitHub */}
          <div className="space-y-2">
            <label className="text-sm font-medium">GitHub Personal Access Token</label>
            {hasGithubToken && (
              <p className="text-xs text-green-600 dark:text-green-400">Token is saved in .env.local</p>
            )}
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showGithubToken ? "text" : "password"}
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder={hasGithubToken ? "Enter new token to replace" : "Enter GitHub token"}
                  className="w-full p-2 pr-10 border border-border rounded-lg bg-background text-sm"
                />
                <button
                  onClick={() => setShowGithubToken(!showGithubToken)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                >
                  {showGithubToken ? <EyeOff className="w-3.5 h-3.5 text-muted-foreground" /> : <Eye className="w-3.5 h-3.5 text-muted-foreground" />}
                </button>
              </div>
              <button
                onClick={handleSaveGithubToken}
                disabled={!githubToken}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                {githubSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                {githubSaved ? "Saved" : "Save"}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              Used for searching ComfyUI custom nodes not in the public registry.
              Only needs <code className="text-[10px] bg-muted px-1 rounded">public_repo</code> scope.
              Create one at{" "}
              <a
                href="https://github.com/settings/tokens/new?scopes=public_repo&description=Dataset-Tools"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                github.com/settings/tokens
              </a>
              . Stored server-side, never sent to the browser.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
