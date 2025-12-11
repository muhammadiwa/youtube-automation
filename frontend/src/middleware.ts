import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// This middleware runs on every request
export function middleware(_request: NextRequest) {
    // For now, just pass through all requests
    // We can add auth checks, redirects, etc. here later
    return NextResponse.next()
}

// Configure which paths the middleware runs on
export const config = {
    // Match all paths except static files and API routes
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
}
