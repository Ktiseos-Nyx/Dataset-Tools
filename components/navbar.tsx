"use client"

import { FolderOpen, Settings, HelpCircle, Home } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV_LINKS = [
  { href: "/", label: "Browse", icon: Home },
  { href: "/settings", label: "Settings", icon: Settings },
  // { href: "/help", label: "Help", icon: HelpCircle },
]

export function Navbar() {
  const pathname = usePathname()

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
        {NAV_LINKS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
