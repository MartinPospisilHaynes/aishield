import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const PROTECTED_ROUTES = ["/dashboard", "/dotaznik", "/platba"];
const NOINDEX_ROUTES = ["/login", "/registrace", "/nove-heslo", "/zapomenute-heslo", "/admin", "/onboarding", "/platba", "/dotaznik", "/objednavka", "/dashboard"];

export async function middleware(request: NextRequest) {
    // ── 1. www → non-www 301 redirect ──
    const hostname = request.headers.get("host") || "";
    if (hostname.startsWith("www.")) {
        const url = request.nextUrl.clone();
        url.host = url.host.replace(/^www\./, "");
        return NextResponse.redirect(url, 301);
    }

    // ── 2. Auth (pouze pro chráněné routy) ──
    const isProtected = PROTECTED_ROUTES.some((r) =>
        request.nextUrl.pathname.startsWith(r),
    );
    const isAuthRoute =
        request.nextUrl.pathname === "/login" ||
        request.nextUrl.pathname === "/registrace";

    let response: NextResponse;

    if (isProtected || isAuthRoute) {
        response = NextResponse.next({ request });

        const supabase = createServerClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL!,
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            {
                cookies: {
                    getAll() {
                        return request.cookies.getAll();
                    },
                    setAll(cookiesToSet) {
                        cookiesToSet.forEach(({ name, value }) =>
                            request.cookies.set(name, value),
                        );
                        response = NextResponse.next({ request });
                        cookiesToSet.forEach(({ name, value, options }) =>
                            response.cookies.set(name, value, options),
                        );
                    },
                },
            },
        );

        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (isProtected && !user) {
            const loginUrl = new URL("/login", request.url);
            const redirectPath =
                request.nextUrl.pathname + request.nextUrl.search;
            if (
                redirectPath.startsWith("/") &&
                !redirectPath.startsWith("//") &&
                !redirectPath.includes("://")
            ) {
                loginUrl.searchParams.set("redirect", redirectPath);
            }
            return NextResponse.redirect(loginUrl);
        }

        if (user && isAuthRoute) {
            return NextResponse.redirect(
                new URL("/dashboard", request.url),
            );
        }
    } else {
        response = NextResponse.next({ request });
    }

    // ── 3. Canonical URL (strip query params) ──
    const canonical = `https://aishield.cz${request.nextUrl.pathname}`;
    response.headers.set("Link", `<${canonical}>; rel="canonical"`);

    // ── 4. noindex pro utility stránky ──
    if (NOINDEX_ROUTES.some((r) => request.nextUrl.pathname.startsWith(r))) {
        response.headers.set("X-Robots-Tag", "noindex, nofollow");
    }

    return response;
}

export const config = {
    matcher: [
        "/((?!_next/static|_next/image|favicon\\.ico|icon\\.svg|apple-icon\\.png|og-image|robots\\.txt|sitemap\\.xml|api/).*)",
    ],
};
