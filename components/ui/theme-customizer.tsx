"use client"

import { ArrowLeft, Check, Monitor, Moon, Paintbrush, Sun } from "lucide-react"
import { MotionConfig, motion } from "motion/react"
import { useTheme } from "next-themes"
import * as React from "react"
import { BrushCleaning } from "@/components/animate-ui/icons/brush-cleaning"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { useClickOutside } from "@/hooks/use-click-outside"
import { cn } from "@/lib/utils"

const colors = [
  { name: "zinc", class: "bg-zinc-500" },
  { name: "red", class: "bg-red-500" },
  { name: "orange", class: "bg-orange-500" },
  { name: "green", class: "bg-green-500" },
  { name: "blue", class: "bg-blue-500" },
  { name: "violet", class: "bg-violet-500" },
  { name: "pink", class: "bg-pink-500" },
]

function useThemeColor() {
  const [activeColor, setActiveColor] = React.useState("green")
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
    const saved = localStorage.getItem("theme-color")
    if (saved) setActiveColor(saved)
  }, [])

  const setColor = (colorName: string) => {
    setActiveColor(colorName)
    localStorage.setItem("theme-color", colorName)
    document.documentElement.setAttribute("data-theme-color", colorName)
  }

  return { activeColor, setColor, mounted }
}

// Variant 1: Floating Pill with Popup
export function ThemeCustomizerPill({
  className,
  inline,
}: {
  className?: string
  inline?: boolean
}) {
  const { activeColor, setColor, mounted } = useThemeColor()
  const [showColors, setShowColors] = React.useState(false)
  const containerRef = React.useRef<HTMLDivElement>(null)

  useClickOutside(containerRef, () => {
    setShowColors(false)
  })

  // Detect if using static positioning (inline mode)
  const isInline = inline || className?.includes("static")

  if (!mounted) {
    return (
      <nav
        className={cn(
          "fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 gap-1 rounded-full border bg-background/70 p-1 shadow-lg backdrop-blur-xl",
          className,
        )}
      >
        <div className="size-9 animate-pulse rounded-full bg-muted" />
        <div className="size-9 animate-pulse rounded-full bg-muted" />
      </nav>
    )
  }

  return (
    <div ref={containerRef} className={isInline ? "relative" : undefined}>
      <nav
        className={cn(
          "fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-1 rounded-full border bg-background/70 p-1 shadow-lg backdrop-blur-xl transition-all",
          className,
        )}
      >
        <ThemeToggle size={20} className="size-9 rounded-full p-2" />
        <button
          className="flex size-9 items-center justify-center rounded-full transition-colors hover:bg-accent cursor-pointer"
          onClick={() => setShowColors(!showColors)}
        >
          <BrushCleaning size={20} animateOnHover />
        </button>
      </nav>

      {showColors && (
        <div
          className={cn(
            "z-50 flex justify-center gap-1.5 rounded-xl border bg-background/70 p-2 shadow-lg backdrop-blur-xl animate-in fade-in slide-in-from-bottom-2",
            isInline
              ? "absolute bottom-full left-0 sm:left-auto sm:right-0 mb-2"
              : "fixed bottom-20 left-1/2 -translate-x-1/2 gap-2 rounded-full px-3 py-2",
          )}
        >
          {colors.map((c) => (
            <button
              key={c.name}
              onClick={() => setColor(c.name)}
              className={cn(
                "relative rounded-full transition-transform hover:scale-110 cursor-pointer",
                isInline ? "size-6" : "size-7",
                c.class,
              )}
            >
              {activeColor === c.name && (
                <Check
                  className={cn(
                    "absolute inset-0 m-auto text-white",
                    isInline ? "size-3" : "size-4",
                  )}
                />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Variant 2: Inline Bar with All Options
export function ThemeCustomizerBar({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme()
  const { activeColor, setColor, mounted } = useThemeColor()

  if (!mounted) {
    return (
      <div
        className={cn(
          "flex items-center gap-4 rounded-full border bg-background/70 px-4 py-2 shadow-lg backdrop-blur-xl",
          className,
        )}
      >
        <div className="flex gap-1">
          {[1, 2, 3].map((i) => (
            <div key={i} className="size-8 animate-pulse rounded-md bg-muted" />
          ))}
        </div>
        <div className="h-6 w-px bg-border" />
        <div className="flex gap-1.5">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="size-6 animate-pulse rounded-full bg-muted"
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex items-center gap-4 rounded-full border bg-background/70 px-4 py-2 shadow-lg backdrop-blur-xl",
        className,
      )}
    >
      <div className="flex gap-1">
        {[
          { value: "light", icon: Sun },
          { value: "dark", icon: Moon },
          { value: "system", icon: Monitor },
        ].map(({ value, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setTheme(value)}
            className={cn(
              "flex size-8 items-center justify-center rounded-md transition-colors",
              theme === value ? "bg-primary text-white" : "hover:bg-accent",
            )}
          >
            <Icon className="size-4" />
          </button>
        ))}
      </div>

      <div className="h-6 w-px bg-border" />

      <div className="flex gap-1.5">
        {colors.map((c) => (
          <button
            key={c.name}
            onClick={() => setColor(c.name)}
            className={cn(
              "size-6 rounded-full transition-all hover:scale-110",
              c.class,
              activeColor === c.name &&
                "ring-2 ring-ring ring-offset-2 ring-offset-background",
            )}
          />
        ))}
      </div>
    </div>
  )
}

// Variant 3: Vertical Sidebar
export function ThemeCustomizerSidebar({ className }: { className?: string }) {
  const { activeColor, setColor, mounted } = useThemeColor()

  if (!mounted) {
    return (
      <div
        className={cn(
          "fixed right-4 top-1/2 z-50 flex -translate-y-1/2 flex-col gap-2 rounded-2xl border bg-background/70 p-2 shadow-lg backdrop-blur-xl",
          className,
        )}
      >
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
          <div key={i} className="size-8 animate-pulse rounded-full bg-muted" />
        ))}
      </div>
    )
  }

  return (
    <div
      className={cn(
        "fixed right-4 top-1/2 z-50 flex -translate-y-1/2 flex-col items-center gap-2 rounded-2xl border bg-background/70 p-2 shadow-lg backdrop-blur-xl",
        className,
      )}
    >
      <ThemeToggle size={16} className="size-8 rounded-full p-2" />

      <div className="mx-auto h-px w-6 bg-border" />

      {colors.map((c) => (
        <button
          key={c.name}
          onClick={() => setColor(c.name)}
          className={cn(
            "relative size-8 rounded-full transition-transform hover:scale-110 cursor-pointer",
            c.class,
          )}
        >
          {activeColor === c.name && (
            <Check className="absolute inset-0 m-auto size-4 text-white" />
          )}
        </button>
      ))}
    </div>
  )
}

// Variant 4: Bottom Dock (macOS style)
export function ThemeCustomizerDock({ className }: { className?: string }) {
  const { activeColor, setColor, mounted } = useThemeColor()

  if (!mounted) {
    return (
      <div
        className={cn(
          "fixed bottom-4 left-1/2 z-50 flex -translate-x-1/2 gap-1 rounded-2xl border bg-background/80 p-1.5 shadow-2xl backdrop-blur-xl",
          className,
        )}
      >
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="size-10 animate-pulse rounded-xl bg-muted" />
        ))}
      </div>
    )
  }

  return (
    <div
      className={cn(
        "fixed bottom-4 left-1/2 z-50 flex -translate-x-1/2 items-center gap-1 rounded-2xl border bg-background/80 p-1.5 shadow-2xl backdrop-blur-xl",
        className,
      )}
    >
      <ThemeToggle
        size={20}
        className="size-10 rounded-xl bg-muted/50 p-2 transition-all hover:-translate-y-1"
      />

      <div className="mx-1 w-px bg-border" />

      {colors.map((c) => (
        <button
          key={c.name}
          onClick={() => setColor(c.name)}
          className={cn(
            "relative size-10 rounded-xl transition-all hover:-translate-y-1 cursor-pointer",
            c.class,
            activeColor === c.name &&
              "ring-2 ring-primary ring-offset-2 ring-offset-background",
          )}
        >
          {activeColor === c.name && (
            <Check className="absolute inset-0 m-auto size-5 text-white drop-shadow-md dark:text-black" />
          )}
        </button>
      ))}
    </div>
  )
}

// Variant 5: Minimal Corner
export function ThemeCustomizerCorner({ className }: { className?: string }) {
  const { activeColor, setColor, mounted } = useThemeColor()
  const [expanded, setExpanded] = React.useState(false)

  if (!mounted) {
    return (
      <div className={cn("fixed bottom-4 right-4 z-50", className)}>
        <div className="size-12 animate-pulse rounded-full bg-muted shadow-lg" />
      </div>
    )
  }

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 flex flex-col-reverse items-end gap-2",
        className,
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex size-12 items-center justify-center rounded-full border bg-background shadow-lg transition-transform hover:scale-105 cursor-pointer"
      >
        <Paintbrush
          className={cn("size-5 transition-transform", expanded && "rotate-45")}
        />
      </button>

      {expanded && (
        <div className="flex flex-col items-center gap-2 rounded-2xl border bg-background/90 p-2 shadow-lg backdrop-blur-xl animate-in fade-in slide-in-from-bottom-2">
          <ThemeToggle size={20} className="size-10 rounded-xl p-2" />

          <div className="h-px w-full bg-border" />

          {colors.map((c) => (
            <button
              key={c.name}
              onClick={() => setColor(c.name)}
              className={cn(
                "relative size-10 rounded-xl transition-transform hover:scale-105 cursor-pointer",
                c.class,
              )}
            >
              {activeColor === c.name && (
                <Check className="absolute inset-0 m-auto size-5 text-white" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Variant 6: Dynamic Toolbar with animation
const toolbarTransition = {
  type: "spring" as const,
  bounce: 0.1,
  duration: 0.2,
}

function ToolbarButton({
  children,
  onClick,
  disabled,
  ariaLabel,
}: {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  ariaLabel?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className="relative flex size-9 shrink-0 cursor-pointer select-none appearance-none items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:ring-2 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50"
    >
      {children}
    </button>
  )
}

export function ThemeCustomizerToolbar({ className }: { className?: string }) {
  const { setTheme, resolvedTheme } = useTheme()
  const { activeColor, setColor, mounted } = useThemeColor()
  const [isOpen, setIsOpen] = React.useState(false)
  const containerRef = React.useRef<HTMLDivElement>(null)

  useClickOutside(containerRef, () => {
    setIsOpen(false)
  })

  if (!mounted) {
    return (
      <div
        className={cn(
          "fixed bottom-4 left-1/2 z-50 hidden -translate-x-1/2 sm:block",
          className,
        )}
      >
        <div className="h-[52px] w-[100px] animate-pulse rounded-xl border bg-background" />
      </div>
    )
  }

  return (
    <MotionConfig transition={toolbarTransition}>
      <div
        className={cn(
          "fixed bottom-4 left-1/2 z-50 hidden -translate-x-1/2 sm:block",
          className,
        )}
        ref={containerRef}
      >
        <div className="rounded-xl border bg-background/80 shadow-lg backdrop-blur-xl">
          <motion.div
            animate={{
              width: isOpen ? "320px" : "100px",
            }}
            initial={false}
          >
            <div className="overflow-hidden p-2">
              {!isOpen ? (
                <div className="flex items-center space-x-1">
                  <ThemeToggle size={24} className="size-9 rounded-lg p-1.5" />
                  <ToolbarButton
                    onClick={() => setIsOpen(true)}
                    ariaLabel="Open color picker"
                  >
                    <BrushCleaning size={20} animateOnHover />
                  </ToolbarButton>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <ToolbarButton
                    onClick={() => setIsOpen(false)}
                    ariaLabel="Back"
                  >
                    <ArrowLeft className="size-5" />
                  </ToolbarButton>
                  <div className="flex flex-1 items-center justify-center gap-2">
                    {colors.map((c) => (
                      <button
                        key={c.name}
                        onClick={() => setColor(c.name)}
                        className={cn(
                          "relative size-7 cursor-pointer rounded-full transition-transform hover:scale-110",
                          c.class,
                          activeColor === c.name &&
                            "ring-2 ring-ring ring-offset-2 ring-offset-background",
                        )}
                      >
                        {activeColor === c.name && (
                          <Check className="absolute inset-0 m-auto size-4 text-white" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </MotionConfig>
  )
}

// Default export - the pill variant
export { ThemeCustomizerPill as ThemeCustomizer }
