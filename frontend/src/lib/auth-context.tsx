/**
 * AIshield.cz — Auth Context
 * Globální stav přihlášeného uživatele.
 */

"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { createClient } from "@/lib/supabase-browser";
import type { User, Session } from "@supabase/supabase-js";

interface AuthContextType {
    user: User | null;
    session: Session | null;
    loading: boolean;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    session: null,
    loading: true,
    signOut: async () => { },
});

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);

    const supabase = createClient();

    useEffect(() => {
        // Ověřit uživatele serverově (getUser) — ne jen z cookies (getSession)
        // getSession jen čte JWT z cookies a NEVALIDUJE proti Supabase.
        // Po smazání uživatelů z DB by getSession stále vracelo "platnou" session.
        supabase.auth.getUser().then(({ data: { user }, error }) => {
            if (error || !user) {
                // Neplatný/smazaný uživatel → vyčistit session
                setSession(null);
                setUser(null);
                setLoading(false);
                // Vyčistit stale cookies
                supabase.auth.signOut().catch(() => {});
                return;
            }
            // Uživatel existuje → načíst session pro token
            supabase.auth.getSession().then(({ data: { session } }) => {
                setSession(session);
                setUser(session?.user ?? null);
                setLoading(false);
            });
        });

        // Poslouchat změny auth stavu
        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        return () => subscription.unsubscribe();
    }, []);

    const signOut = async () => {
        await supabase.auth.signOut();
        setUser(null);
        setSession(null);
    };

    return (
        <AuthContext.Provider value={{ user, session, loading, signOut }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth musí být použit uvnitř AuthProvider");
    }
    return context;
}
