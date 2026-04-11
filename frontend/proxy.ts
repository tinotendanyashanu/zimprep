import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Route protection middleware.
 *
 * Responsibilities:
 * 1. Refresh the Supabase session cookie on every request (required by @supabase/ssr).
 * 2. Redirect unauthenticated users away from protected routes to /login.
 * 3. Redirect authenticated users away from auth pages (login, register) to /dashboard.
 *
 * Role-based authorisation (admin/employee/parent/student) is enforced
 * inside the individual route layouts which query the DB — that is the
 * server-authoritative check. Middleware handles the "are you logged in?" gate.
 */

/** Routes that do NOT require authentication. */
const PUBLIC_PATHS = new Set([
  "/",
  "/login",
  "/register",
  "/register-parent",
]);

/** Prefixes that are always public (auth callback, API, static, marketing). */
const PUBLIC_PREFIXES = ["/auth/", "/api/", "/_next/", "/favicon", "/(marketing)"];

/** Prefixes that require an active session. */
const PROTECTED_PREFIXES = ["/admin", "/workstation", "/dashboard", "/parent", "/student"];

function isPublic(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  if (PUBLIC_PREFIXES.some((p) => pathname.startsWith(p))) return true;
  // static file extensions
  if (/\.\w+$/.test(pathname)) return true;
  return false;
}

function isProtected(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Pass through public paths immediately — no session check needed.
  if (isPublic(pathname)) {
    return NextResponse.next();
  }

  let response = NextResponse.next({ request });

  // Build a server-side Supabase client that refreshes the session cookie.
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          // Write cookies to the outgoing request (for subsequent middleware)
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          // Re-create response so updated cookies are sent to the browser
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // IMPORTANT: use getUser() — not getSession() — for server-side validation.
  // getUser() re-validates the JWT with the Supabase Auth server on every call.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Unauthenticated user hitting a protected route → send to login
  if (!user && isProtected(pathname)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Authenticated user hitting a login/register page → send to dashboard
  if (user && (pathname === "/login" || pathname.startsWith("/register"))) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return response;
}

export const config = {
  /*
   * Match all routes EXCEPT:
   * - Next.js internals (_next/static, _next/image)
   * - Common static file extensions
   */
  matcher: [
    "/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)",
  ],
};
