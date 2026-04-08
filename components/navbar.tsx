"use client"

import { useState, useEffect } from "react"
import { FolderOpen, Settings, Home, Save, Eye, EyeOff, Check } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTheme } from "next-themes"
import { useSettings } from "@/hooks/use-settings"
import type { AppSettings, AccentColor } from "@/types/settings"
import {
  Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from "@/components/ui/sheet"

export function Navbar() {
  const pathname = usePathname()
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <nav className="h-12 border-b border-border bg-card flex items-center px-4 gap-6">
      {/* App Title */}
      <Link href="/" className="flex items-center gap-2 shrink-0">
        <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center">
          <FolderOpen className="w-3.5 h-3.5 text-primary" />
        </div>
        <span className="text-sm font-semibold">Dataset Tools</span>
      </Link>

      {/* Nav Links */}
      <div className="flex items-center gap-1">
        <Link
          href="/"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            pathname === "/"
              ? "bg-accent text-accent-foreground"
              : "text-muted-foreground hover:text-accent-foreground hover:bg-accent/50"
          }`}
        >
          <Home className="w-3.5 h-3.5" />
          Browse
        </Link>

        <Sheet open={settingsOpen} onOpenChange={setSettingsOpen}>
          <SheetTrigger asChild>
            <button
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                settingsOpen
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-accent-foreground hover:bg-accent/50"
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              Settings
            </button>
          </SheetTrigger>
          <SheetContent className="overflow-y-auto w-[400px] sm:w-[450px] sm:max-w-[450px]">
            <SheetHeader className="px-6 pt-6 pb-2">
              <SheetTitle>Settings</SheetTitle>
              <SheetDescription className="sr-only">
                Configure appearance, file browser, and API keys.
              </SheetDescription>
            </SheetHeader>
            <SettingsContent />
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  )
}

function SettingsContent() {
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

  useEffect(() => {
    // Sync accent color to DOM on mount
    if (settings.accentColor && settings.accentColor !== 'zinc') {
      document.documentElement.setAttribute("data-accent", settings.accentColor)
    } else {
      document.documentElement.removeAttribute("data-accent")
    }
  }, [settings.accentColor])

  useEffect(() => {
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
      const response = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secrets: { civitaiApiKey: civitaiKey } }),
      })
      if (!response.ok) {
        const errBody = await response.text().catch(() => "")
        console.error(`Failed to save Civitai API key (${response.status}):`, errBody)
        return
      }
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
      const response = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secrets: { githubToken: githubToken } }),
      })
      if (!response.ok) {
        const errBody = await response.text().catch(() => "")
        console.error(`Failed to save GitHub token (${response.status}):`, errBody)
        return
      }
      setHasGithubToken(!!githubToken)
      setGithubToken("")
      setGithubSaved(true)
      setTimeout(() => setGithubSaved(false), 2000)
    } catch (err) {
      console.error("Failed to save GitHub token:", err)
    }
  }

  return (
    <div className="space-y-6 px-6 pb-6">
      {/* Appearance */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Appearance</h2>

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

        <div className="space-y-2">
          <label className="text-sm font-medium">Accent Color</label>
          <div className="flex gap-2">
            {([
              { value: "zinc", bg: "bg-zinc-500" },
              { value: "red", bg: "bg-red-500" },
              { value: "orange", bg: "bg-orange-500" },
              { value: "green", bg: "bg-green-500" },
              { value: "blue", bg: "bg-blue-500" },
              { value: "violet", bg: "bg-violet-500" },
              { value: "pink", bg: "bg-pink-500" },
            ] as const).map((c) => (
              <button
                key={c.value}
                onClick={() => {
                  updateSettings({ accentColor: c.value as AccentColor })
                  document.documentElement.setAttribute("data-accent", c.value)
                }}
                className={`relative w-8 h-8 rounded-full transition-transform hover:scale-110 ${c.bg} ${
                  settings.accentColor === c.value
                    ? "ring-2 ring-ring ring-offset-2 ring-offset-background"
                    : ""
                }`}
              >
                {settings.accentColor === c.value && (
                  <Check className="absolute inset-0 m-auto w-4 h-4 text-white" />
                )}
              </button>
            ))}
          </div>
        </div>

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
          <label htmlFor="navbar-civitai-key" className="text-sm font-medium">Civitai API Key</label>
          {hasCivitaiKey && (
            <p className="text-xs text-green-600 dark:text-green-400">Key is saved in .env.local</p>
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              handleSaveCivitaiKey()
            }}
          >
            <div className="relative flex-1">
              <input
                id="navbar-civitai-key"
                name="navbar-civitai-key"
                type={showCivitaiKey ? "text" : "password"}
                autoComplete="off"
                value={civitaiKey}
                onChange={(e) => setCivitaiKey(e.target.value)}
                placeholder={hasCivitaiKey ? "Enter new key to replace" : "Enter Civitai API key"}
                className="w-full p-2 pr-10 border border-border rounded-lg bg-background text-sm"
              />
              <button
                type="button"
                onClick={() => setShowCivitaiKey(!showCivitaiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
              >
                {showCivitaiKey ? <EyeOff className="w-3.5 h-3.5 text-muted-foreground" /> : <Eye className="w-3.5 h-3.5 text-muted-foreground" />}
              </button>
            </div>
            <button
              type="submit"
              disabled={!civitaiKey && !hasCivitaiKey}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {civitaiSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              {civitaiSaved ? "Saved" : !civitaiKey && hasCivitaiKey ? "Clear" : "Save"}
            </button>
          </form>
          <p className="text-xs text-muted-foreground">
            Stored server-side in .env.local. Never sent to the browser.
          </p>
        </div>

        {/* GitHub */}
        <div className="space-y-2">
          <label htmlFor="navbar-github-token" className="text-sm font-medium">GitHub Personal Access Token</label>
          {hasGithubToken && (
            <p className="text-xs text-green-600 dark:text-green-400">Token is saved in .env.local</p>
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              handleSaveGithubToken()
            }}
          >
            <div className="relative flex-1">
              <input
                id="navbar-github-token"
                name="navbar-github-token"
                type={showGithubToken ? "text" : "password"}
                autoComplete="off"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder={hasGithubToken ? "Enter new token to replace" : "Enter GitHub token"}
                className="w-full p-2 pr-10 border border-border rounded-lg bg-background text-sm"
              />
              <button
                type="button"
                onClick={() => setShowGithubToken(!showGithubToken)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
              >
                {showGithubToken ? <EyeOff className="w-3.5 h-3.5 text-muted-foreground" /> : <Eye className="w-3.5 h-3.5 text-muted-foreground" />}
              </button>
            </div>
            <button
              type="submit"
              disabled={!githubToken && !hasGithubToken}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {githubSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              {githubSaved ? "Saved" : !githubToken && hasGithubToken ? "Clear" : "Save"}
            </button>
          </form>
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
  )
}
