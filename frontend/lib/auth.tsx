"use client"

import Cookies from "js-cookie"
import { useRouter } from "next/navigation"
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"

import { api, TOKEN_COOKIE } from "@/lib/api"
import type { User } from "@/types"

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  const fetchMe = useCallback(async () => {
    const token = Cookies.get(TOKEN_COOKIE)
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const { data } = await api.get<User>("/auth/me")
      setUser(data)
    } catch {
      Cookies.remove(TOKEN_COOKIE)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  const login = useCallback(
    async (email: string, password: string) => {
      const form = new URLSearchParams()
      form.set("username", email)
      form.set("password", password)

      const { data } = await api.post<{ access_token: string }>("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })

      Cookies.set(TOKEN_COOKIE, data.access_token, { expires: 1, sameSite: "lax" })
      await fetchMe()
      router.push("/dashboard")
    },
    [fetchMe, router]
  )

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      await api.post("/auth/register", { email, password, full_name: fullName || undefined })
      await login(email, password)
    },
    [login]
  )

  const logout = useCallback(() => {
    Cookies.remove(TOKEN_COOKIE)
    setUser(null)
    router.push("/login")
  }, [router])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider")
  }
  return context
}
