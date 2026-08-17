"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { FileStack, LogOut, Mail, Moon, Receipt, Sun, Tag } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth"
import { useTheme } from "@/lib/theme"

const LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: FileStack },
  { href: "/boletos/novo", label: "Novo boleto", icon: Receipt },
  { href: "/categorias", label: "Categorias", icon: Tag },
  { href: "/contas-email", label: "Contas de e-mail", icon: Mail },
]

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("")
}

export function Navbar() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-soft">
            <Receipt className="h-4 w-4" />
          </span>
          <span className="brand-gradient-text">BoletoHub</span>
        </Link>

        <nav className="flex items-center gap-1">
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            )
          })}

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="text-muted-foreground"
            aria-label="Alternar tema"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          <div className="mx-2 h-6 w-px bg-border" />

          {user && (
            <div className="flex items-center gap-2 pr-1">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
                {initials(user.full_name || user.email)}
              </span>
              <span className="hidden text-sm text-muted-foreground sm:inline">
                {user.full_name || user.email}
              </span>
            </div>
          )}
          <Button variant="ghost" size="sm" onClick={logout} className="gap-1.5 text-muted-foreground">
            <LogOut className="h-4 w-4" />
            Sair
          </Button>
        </nav>
      </div>
    </header>
  )
}
