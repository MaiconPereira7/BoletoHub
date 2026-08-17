import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const TOKEN_COOKIE = "boletohub_token"
const PROTECTED_PREFIXES = ["/dashboard", "/boletos", "/contas-email", "/categorias"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix))

  if (!isProtected) {
    return NextResponse.next()
  }

  const token = request.cookies.get(TOKEN_COOKIE)?.value
  if (!token) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set("next", pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/boletos/:path*", "/categorias/:path*"],
}
