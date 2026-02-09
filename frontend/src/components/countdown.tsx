"use client";

import { useState, useEffect } from "react";

interface TimeLeft {
    months: number;
    weeks: number;
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
}

function calcTimeLeft(): TimeLeft {
    const deadline = new Date("2026-08-02T00:00:00Z").getTime();
    const now = Date.now();
    const diff = Math.max(0, deadline - now);

    const totalSeconds = Math.floor(diff / 1000);
    const totalMinutes = Math.floor(totalSeconds / 60);
    const totalHours = Math.floor(totalMinutes / 60);
    const totalDays = Math.floor(totalHours / 24);

    // Months = rough 30-day chunks
    const months = Math.floor(totalDays / 30);
    const afterMonths = totalDays - months * 30;
    const weeks = Math.floor(afterMonths / 7);
    const days = afterMonths - weeks * 7;
    const hours = totalHours % 24;
    const minutes = totalMinutes % 60;
    const seconds = totalSeconds % 60;

    return { months, weeks, days, hours, minutes, seconds };
}

function CountdownUnit({ value, label }: { value: number; label: string }) {
    return (
        <div className="flex flex-col items-center">
            <div className="relative w-16 h-16 sm:w-20 sm:h-20 rounded-xl bg-white/[0.04] border border-white/[0.08] backdrop-blur-sm flex items-center justify-center">
                <span className="text-2xl sm:text-3xl font-bold tabular-nums text-white">
                    {String(value).padStart(2, "0")}
                </span>
            </div>
            <span className="mt-2 text-[11px] sm:text-xs font-medium uppercase tracking-wider text-slate-500">
                {label}
            </span>
        </div>
    );
}

function Separator() {
    return (
        <div className="flex flex-col items-center justify-center pb-6">
            <span className="text-xl sm:text-2xl font-bold text-slate-600">:</span>
        </div>
    );
}

export default function Countdown({ className = "" }: { className?: string }) {
    const [time, setTime] = useState<TimeLeft>(calcTimeLeft);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const id = setInterval(() => setTime(calcTimeLeft()), 1000);
        return () => clearInterval(id);
    }, []);

    if (!mounted) {
        // SSR placeholder — avoid hydration mismatch
        return (
            <div className={`flex items-center justify-center gap-2 sm:gap-3 ${className}`}>
                {["Měsíce", "Týdny", "Dny", "Hodiny", "Minuty", "Sekundy"].map((label) => (
                    <CountdownUnit key={label} value={0} label={label} />
                ))}
            </div>
        );
    }

    return (
        <div className={`flex items-center justify-center gap-1.5 sm:gap-2 ${className}`}>
            <CountdownUnit value={time.months} label="Měsíce" />
            <Separator />
            <CountdownUnit value={time.weeks} label="Týdny" />
            <Separator />
            <CountdownUnit value={time.days} label="Dny" />
            <Separator />
            <CountdownUnit value={time.hours} label="Hodiny" />
            <Separator />
            <CountdownUnit value={time.minutes} label="Minuty" />
            <Separator />
            <CountdownUnit value={time.seconds} label="Sekundy" />
        </div>
    );
}
