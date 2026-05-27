import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  const host = request.headers.get('host') || '';

  let changed = false;

  // 1. Force Redirection from www to non-www canonical domains
  if (host.startsWith('www.')) {
    const newHost = host.slice(4);
    request.headers.set('host', newHost);
    url.host = newHost;
    changed = true;
  }

  // 2. Enforce trailing slash removal (except for root path)
  if (url.pathname !== '/' && url.pathname.endsWith('/')) {
    url.pathname = url.pathname.slice(0, -1);
    changed = true;
  }

  if (changed) {
    // 301 Permanent Redirect for SEO health
    return NextResponse.redirect(url, 301);
  }

  return NextResponse.next();
}

export const config = {
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
};
