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

const ZERO: TimeLeft = { months: 0, weeks: 0, days: 0, hours: 0, minutes: 0, seconds: 0 };

function calcTimeLeft(): TimeLeft {
    const deadline = new Date("2026-08-02T00:00:00Z").getTime();
    const now = Date.now();
    const diff = Math.max(0, deadline - now);

    const totalSeconds = Math.floor(diff / 1000);
    const totalMinutes = Math.floor(totalSeconds / 60);
    const totalHours = Math.floor(totalMinutes / 60);
    const totalDays = Math.floor(totalHours / 24);

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
            <div className="relative w-14 h-14 sm:w-20 sm:h-20 rounded-xl bg-white/[0.04] border border-white/[0.08] backdrop-blur-sm flex items-center justify-center">
                <span suppressHydrationWarning className="text-xl sm:text-3xl font-bold tabular-nums text-white">
                    {String(value).padStart(2, "0")}
                </span>
            </div>
            <span className="mt-1.5 sm:mt-2 text-[10px] sm:text-xs font-medium uppercase tracking-wider text-slate-400">
                {label}
            </span>
        </div>
    );
}

function Separator() {
    return (
        <div className="hidden sm:flex flex-col items-center justify-center pb-6">
            <span className="text-2xl font-bold text-slate-600">:</span>
        </div>
    );
}

const labels: (keyof TimeLeft)[] = ["months", "weeks", "days", "hours", "minutes", "seconds"];
const labelsCz: Record<keyof TimeLeft, string> = {
    months: "Měsíce",
    weeks: "Týdny",
    days: "Dny",
    hours: "Hodiny",
    minutes: "Minuty",
    seconds: "Sekundy",
};

function CountdownInner({ time, className }: { time: TimeLeft; className: string }) {
    return (
        <>
            <div className={`grid grid-cols-3 gap-3 sm:hidden ${className}`}>
                {labels.map((key) => (
                    <CountdownUnit key={key} value={time[key]} label={labelsCz[key]} />
                ))}
            </div>
            <div className={`hidden sm:flex items-center justify-center gap-2 ${className}`}>
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
        </>
    );
}

export default function Countdown({ className = "" }: { className?: string }) {
    const [time, setTime] = useState<TimeLeft>(ZERO);

    useEffect(() => {
        setTime(calcTimeLeft());
        const id = setInterval(() => setTime(calcTimeLeft()), 1000);
        return () => clearInterval(id);
    }, []);

    return <CountdownInner time={time} className={className} />;
}
