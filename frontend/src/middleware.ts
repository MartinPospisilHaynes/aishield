import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

// Routy vyžadující přihlášení (Supabase session)
// /admin routes mají vlastní CRM autentizaci — nepotřebují Supabase
const PROTECTED_ROUTES = ["/dashboard", "/dotaznik"];

export async function middleware(request: NextRequest) {
    let supabaseResponse = NextResponse.next({ request });

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
                    supabaseResponse = NextResponse.next({ request });
                    cookiesToSet.forEach(({ name, value, options }) =>
                        supabaseResponse.cookies.set(name, value, options),
                    );
                },
            },
        },
    );

    // Refresh session (důležité pro SSR)
    const {
        data: { user },
    } = await supabase.auth.getUser();

    // Pokud jde o chráněnou routu a uživatel není přihlášen → redirect na login
    const isProtected = PROTECTED_ROUTES.some((route) =>
        request.nextUrl.pathname.startsWith(route),
    );

    if (isProtected && !user) {
        const loginUrl = new URL("/login", request.url);
        // Preserve full path including query string for redirect after login
        const redirectPath = request.nextUrl.pathname + request.nextUrl.search;
        if (redirectPath.startsWith("/") && !redirectPath.startsWith("//") && !redirectPath.includes("://")) {
            loginUrl.searchParams.set("redirect", redirectPath);
        }
        return NextResponse.redirect(loginUrl);
    }

    // Pokud je přihlášený a jde na login/registraci → redirect na dashboard
    if (user && (request.nextUrl.pathname === "/login" || request.nextUrl.pathname === "/registrace")) {
        return NextResponse.redirect(new URL("/dashboard", request.url));
    }

    return supabaseResponse;
}

export const config = {
    matcher: ["/dashboard/:path*", "/dotaznik/:path*", "/login", "/registrace"],
};
