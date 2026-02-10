/**
 * AIshield.cz — Supabase Auth callback
 * Zpracování potvrzení emailu a OAuth redirectů.
 *
 * Supabase flow:
 *  1. Uživatel klikne na potvrzovací odkaz v emailu
 *  2. Supabase ověří token a přesměruje sem s ?code=xxx
 *  3. Vyměníme code za session (PKCE flow)
 *  4. Pokud PKCE selže (např. jiný prohlížeč), email JE potvrzen —
 *     přesměrujeme na login s úspěchovou hláškou
 */

import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
    const { searchParams, origin } = new URL(request.url);
    const code = searchParams.get("code");
    const next = searchParams.get("next") ?? "/dashboard";

    if (code) {
        const cookieStore = cookies();
        const supabase = createServerClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL!,
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            {
                cookies: {
                    get(name: string) {
                        return cookieStore.get(name)?.value;
                    },
                    set(name: string, value: string, options: CookieOptions) {
                        cookieStore.set({ name, value, ...options });
                    },
                    remove(name: string, options: CookieOptions) {
                        cookieStore.delete(name);
                    },
                },
            },
        );

        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (!error) {
            // PKCE výměna úspěšná — uživatel je přihlášen
            return NextResponse.redirect(`${origin}${next}`);
        }

        // PKCE selhalo (jiný prohlížeč / cookies smazány) —
        // email JE potvrzen Supabase, jen nelze vytvořit session.
        // Přesměrujeme na login s pozitivní hláškou.
        return NextResponse.redirect(`${origin}/login?verified=true`);
    }

    // Žádný code parametr — neplatný callback
    return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
