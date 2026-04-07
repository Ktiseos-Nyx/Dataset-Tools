"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

interface ThemeToggleProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: number;
}

/**
 * ThemeToggle — a simple button that cycles between light and dark mode.
 * Uses next-themes for theme state. Shows a sun icon in dark mode and a
 * moon icon in light mode (tap to switch).
 */
export function ThemeToggle({
  size = 20,
  className,
  ...props
}: ThemeToggleProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Render a placeholder until mounted to avoid hydration mismatch
  if (!mounted) {
    return (
      <button
        type="button"
        aria-label="Toggle theme"
        className={cn(
          "inline-flex items-center justify-center transition-colors",
          className,
        )}
        {...props}
      >
        <Sun size={size} />
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "inline-flex items-center justify-center transition-colors hover:bg-accent cursor-pointer",
        className,
      )}
      {...props}
    >
      {isDark ? <Sun size={size} /> : <Moon size={size} />}
    </button>
  );
}
