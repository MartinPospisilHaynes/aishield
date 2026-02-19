"use client";

import { useRef, useState, useEffect } from "react";

/**
 * ScrollReveal — triggers a CSS keyframe animation when the element
 * scrolls into the viewport. Uses IntersectionObserver + double-rAF
 * to guarantee the browser paints the initial opacity:0 state first.
 */
export default function ScrollReveal({
    children,
    className = "",
    variant = "fade-up",
    delay = 0,
}: {
    children: React.ReactNode;
    className?: string;
    variant?: "fade-up" | "slide-left" | "slide-right" | "scale-up";
    delay?: number;
}) {
    const ref = useRef<HTMLDivElement>(null);
    const [animClass, setAnimClass] = useState("");

    useEffect(() => {
        const el = ref.current;
        if (!el) return;

        const animName = `anim-${variant}`;

        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    // Double-rAF ensures the browser has painted opacity:0 first,
                    // so the keyframe animation is always visible to the user.
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            setAnimClass(animName);
                        });
                    });
                    observer.unobserve(el);
                }
            },
            { threshold: 0.05, rootMargin: "0px 0px -30px 0px" }
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, [variant]);

    return (
        <div
            ref={ref}
            className={`scroll-reveal ${animClass} ${className}`}
            data-delay={delay}
        >
            {children}
        </div>
    );
}
