"use client";

import { usePathname } from "next/navigation";
import Header from "./header";

/** Skryje header na stránkách kde koliduje (dotazník — má vlastní progress bar, admin login). */
const HIDDEN_ON = ["/dotaznik", "/admin/login"];

export default function HeaderVisibility() {
    const pathname = usePathname();
    const hidden = HIDDEN_ON.some((p) => pathname === p || pathname.startsWith(p + "/"));
    if (hidden) return null;
    return <Header />;
}
