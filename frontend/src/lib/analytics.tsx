"use client";

/**
 * AIshield.cz — Analytics System
 *
 * Vlastní event tracking systém. Data zůstávají v Supabase (GDPR friendly).
 * Respektuje cookie consent — pokud uživatel odmítne cookies, netrackujeme.
 *
 * Použití:
 *   const { track, trackPageView } = useAnalytics();
 *   track("scan_started", { url: "example.com" });
 */

import React, {
  createContext,
  useContext,
  useCallback,
  useRef,
  useEffect,
  useState,
} from "react";
import { usePathname } from "next/navigation";

// ── Types ──

interface AnalyticsEvent {
  session_id: string;
  event_name: string;
  properties: Record<string, unknown>;
  page_url: string | null;
  referrer: string | null;
  user_email: string | null;
  duration_ms: number | null;
  timestamp: string;
}

interface AnalyticsContextType {
  track: (
    eventName: string,
    properties?: Record<string, unknown>,
    durationMs?: number
  ) => void;
  trackPageView: (url?: string) => void;
  setUserEmail: (email: string) => void;
  getSessionId: () => string;
}

// ── Constants ──

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const CONSENT_KEY = "aishield_consent_v1";
const SESSION_KEY = "aishield_session_id";
const BATCH_INTERVAL_MS = 3000; // Posílat eventy každé 3 sekundy
const MAX_BATCH_SIZE = 25;

// ── Context ──

const AnalyticsContext = createContext<AnalyticsContextType>({
  track: () => {},
  trackPageView: () => {},
  setUserEmail: () => {},
  getSessionId: () => "",
});

export const useAnalytics = () => useContext(AnalyticsContext);

// ── Session ID ──

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "";
  let sid = sessionStorage.getItem(SESSION_KEY);
  if (!sid) {
    sid = `s_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(SESSION_KEY, sid);
  }
  return sid;
}

// ── Consent check ──

function hasAnalyticsConsent(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) return false;
    const consent = JSON.parse(raw);
    return consent.cookies === true;
  } catch {
    return false;
  }
}

// ── Provider ──

export function AnalyticsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const queueRef = useRef<AnalyticsEvent[]>([]);
  const userEmailRef = useRef<string | null>(null);
  const sessionIdRef = useRef<string>("");
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

  // Initialize on client only
  useEffect(() => {
    setIsClient(true);
    sessionIdRef.current = getOrCreateSessionId();
  }, []);

  // ── Flush queue → backend ──
  const flush = useCallback(async () => {
    if (queueRef.current.length === 0) return;
    if (!hasAnalyticsConsent()) {
      queueRef.current = [];
      return;
    }

    const batch = queueRef.current.splice(0, MAX_BATCH_SIZE);

    try {
      const res = await fetch(`${API_URL}/api/analytics/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events: batch }),
        keepalive: true, // Ensure it sends even on page unload
      });
      if (!res.ok) {
        console.warn("[analytics] flush failed:", res.status);
      }
    } catch (e) {
      // Silent — analytics should never break the app
      console.warn("[analytics] flush error:", e);
    }
  }, []);

  // ── Periodic flush ──
  useEffect(() => {
    if (!isClient) return;
    const timer = setInterval(flush, BATCH_INTERVAL_MS);

    // Flush on page unload
    const handleUnload = () => flush();
    window.addEventListener("beforeunload", handleUnload);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") flush();
    });

    return () => {
      clearInterval(timer);
      window.removeEventListener("beforeunload", handleUnload);
      flush(); // Final flush on unmount
    };
  }, [isClient, flush]);

  // ── Track function ──
  const track = useCallback(
    (
      eventName: string,
      properties: Record<string, unknown> = {},
      durationMs?: number
    ) => {
      if (!isClient) return;
      // Always enqueue — consent check happens at flush time
      const event: AnalyticsEvent = {
        session_id: sessionIdRef.current,
        event_name: eventName,
        properties,
        page_url: typeof window !== "undefined" ? window.location.pathname : null,
        referrer:
          typeof document !== "undefined" ? document.referrer || null : null,
        user_email: userEmailRef.current,
        duration_ms: durationMs ?? null,
        timestamp: new Date().toISOString(),
      };
      queueRef.current.push(event);

      // Flush immediately if queue is getting large
      if (queueRef.current.length >= MAX_BATCH_SIZE) {
        flush();
      }
    },
    [isClient, flush]
  );

  // ── Page view tracking ──
  const trackPageView = useCallback(
    (url?: string) => {
      const pageUrl = url || (typeof window !== "undefined" ? window.location.pathname : "");
      // Capture UTM parameters
      const params =
        typeof window !== "undefined"
          ? new URLSearchParams(window.location.search)
          : new URLSearchParams();
      const utm: Record<string, string> = {};
      for (const key of ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]) {
        const val = params.get(key);
        if (val) utm[key] = val;
      }
      track("page_view", {
        url: pageUrl,
        referrer: typeof document !== "undefined" ? document.referrer : "",
        ...utm,
      });
    },
    [track]
  );

  // ── Auto-track page views on route change ──
  useEffect(() => {
    if (!isClient) return;
    trackPageView(pathname);
  }, [pathname, isClient, trackPageView]);

  // ── Set user email ──
  const setUserEmail = useCallback((email: string) => {
    userEmailRef.current = email;
  }, []);

  const getSessionId = useCallback(() => sessionIdRef.current, []);

  return (
    <AnalyticsContext.Provider
      value={{ track, trackPageView, setUserEmail, getSessionId }}
    >
      {children}
    </AnalyticsContext.Provider>
  );
}

// ── Scroll depth tracker (standalone hook) ──

export function useScrollTracking() {
  const { track } = useAnalytics();
  const trackedRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    trackedRef.current = new Set(); // Reset on route change

    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (docHeight <= 0) return;

      const percent = Math.round((scrollTop / docHeight) * 100);

      for (const milestone of [25, 50, 75, 100]) {
        if (percent >= milestone && !trackedRef.current.has(milestone)) {
          trackedRef.current.add(milestone);
          track("scroll_depth", {
            percentage: milestone,
            page: window.location.pathname,
          });
        }
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [track]);
}
