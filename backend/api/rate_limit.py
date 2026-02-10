"""
AIshield.cz — Rate Limiter
In-memory rate limiting pro scan endpoint.

Tři vrstvy ochrany:
1. URL cache: stejná URL max 1x za 24 hodin (vrátí existující výsledky)
2. IP limit: max 5 skenů/hodinu pro anon, 10 pro přihlášené
3. Globální limit: max 200 skenů/hodinu celkem
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)

# ── Konfigurace ──
URL_COOLDOWN_SECONDS = 24 * 60 * 60   # 24 hodin
IP_LIMIT_ANON = 5                      # skenů za hodinu pro nepřihlášené
IP_LIMIT_AUTH = 10                     # skenů za hodinu pro přihlášené
IP_WINDOW_SECONDS = 60 * 60           # 1 hodina
GLOBAL_LIMIT = 200                     # skenů za hodinu globálně
GLOBAL_WINDOW_SECONDS = 60 * 60       # 1 hodina


@dataclass
class URLCacheEntry:
    """Záznam o posledním skenu dané URL."""
    scan_id: str
    company_id: str
    scanned_at: float  # time.time()


@dataclass
class RateLimitResult:
    """Výsledek rate limit kontroly."""
    allowed: bool
    reason: str = ""
    cached_scan_id: str | None = None
    cached_company_id: str | None = None
    retry_after: int = 0  # sekundy do dalšího povoleného pokusu


class ScanRateLimiter:
    """
    Thread-safe in-memory rate limiter pro scan endpoint.
    Čistí se automaticky — žádná DB závislost.
    """

    def __init__(self):
        self._lock = Lock()
        # URL cache: normalized_url -> URLCacheEntry
        self._url_cache: dict[str, URLCacheEntry] = {}
        # IP timestamps: ip -> list[timestamp]
        self._ip_timestamps: dict[str, list[float]] = defaultdict(list)
        # Global timestamps: list[timestamp]
        self._global_timestamps: list[float] = []
        # Last cleanup time
        self._last_cleanup = time.time()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalizuje URL pro porovnání (bez trailing slash, lowercase)."""
        url = url.lower().strip()
        # Odstraň protokol pro porovnání
        for prefix in ("https://", "http://"):
            if url.startswith(prefix):
                url = url[len(prefix):]
        # Odstraň www.
        if url.startswith("www."):
            url = url[4:]
        # Odstraň trailing slash
        url = url.rstrip("/")
        return url

    def _cleanup_old_entries(self, now: float) -> None:
        """Periodicky čistí staré záznamy (každých 10 minut)."""
        if now - self._last_cleanup < 600:
            return

        self._last_cleanup = now
        cutoff_url = now - URL_COOLDOWN_SECONDS
        cutoff_ip = now - IP_WINDOW_SECONDS

        # Čištění URL cache
        expired_urls = [
            url for url, entry in self._url_cache.items()
            if entry.scanned_at < cutoff_url
        ]
        for url in expired_urls:
            del self._url_cache[url]

        # Čištění IP timestamps
        empty_ips = []
        for ip, timestamps in self._ip_timestamps.items():
            self._ip_timestamps[ip] = [t for t in timestamps if t > cutoff_ip]
            if not self._ip_timestamps[ip]:
                empty_ips.append(ip)
        for ip in empty_ips:
            del self._ip_timestamps[ip]

        # Čištění global timestamps
        self._global_timestamps = [
            t for t in self._global_timestamps if t > cutoff_ip
        ]

        logger.debug(
            f"[RateLimit] Cleanup: {len(expired_urls)} expired URLs, "
            f"{len(empty_ips)} empty IPs, "
            f"{len(self._url_cache)} cached URLs"
        )

    def check(
        self,
        url: str,
        client_ip: str,
        is_authenticated: bool = False,
        is_admin: bool = False,
    ) -> RateLimitResult:
        """
        Zkontroluje, zda je scan povolen.

        Returns:
            RateLimitResult s allowed=True pokud OK, jinak důvod odmítnutí.
        """
        now = time.time()
        normalized = self.normalize_url(url)

        with self._lock:
            self._cleanup_old_entries(now)

            # Admin bypass — žádné limity
            if is_admin:
                return RateLimitResult(allowed=True)

            # 1. URL cache — pokud byl tento web skenován za posledních 24h
            if normalized in self._url_cache:
                entry = self._url_cache[normalized]
                age = now - entry.scanned_at
                if age < URL_COOLDOWN_SECONDS:
                    remaining = int(URL_COOLDOWN_SECONDS - age)
                    hours = remaining // 3600
                    mins = (remaining % 3600) // 60
                    logger.info(
                        f"[RateLimit] URL cache hit: {normalized} "
                        f"(scanned {int(age)}s ago, retry in {hours}h {mins}m)"
                    )
                    return RateLimitResult(
                        allowed=False,
                        reason=f"Tento web byl již skenován. Další sken bude možný za {hours}h {mins}min. "
                               f"Výsledky předchozího skenu jsou stále k dispozici.",
                        cached_scan_id=entry.scan_id,
                        cached_company_id=entry.company_id,
                        retry_after=remaining,
                    )

            # 2. IP limit
            ip_limit = IP_LIMIT_AUTH if is_authenticated else IP_LIMIT_ANON
            cutoff = now - IP_WINDOW_SECONDS
            recent_ip = [t for t in self._ip_timestamps[client_ip] if t > cutoff]
            self._ip_timestamps[client_ip] = recent_ip

            if len(recent_ip) >= ip_limit:
                oldest = min(recent_ip)
                retry_after = int(oldest + IP_WINDOW_SECONDS - now)
                mins = retry_after // 60
                logger.warning(
                    f"[RateLimit] IP limit reached: {client_ip} "
                    f"({len(recent_ip)}/{ip_limit} scans/h)"
                )
                return RateLimitResult(
                    allowed=False,
                    reason=f"Dosáhli jste limitu {ip_limit} skenů za hodinu. "
                           f"Další sken bude možný za {mins} minut.",
                    retry_after=retry_after,
                )

            # 3. Globální limit
            global_recent = [
                t for t in self._global_timestamps if t > cutoff
            ]
            self._global_timestamps = global_recent

            if len(global_recent) >= GLOBAL_LIMIT:
                logger.warning(
                    f"[RateLimit] Global limit reached: "
                    f"{len(global_recent)}/{GLOBAL_LIMIT} scans/h"
                )
                return RateLimitResult(
                    allowed=False,
                    reason="Systém je momentálně přetížen. Zkuste to prosím za pár minut.",
                    retry_after=300,
                )

            # ✅ Povoleno — zaznamenat
            self._ip_timestamps[client_ip].append(now)
            self._global_timestamps.append(now)

            return RateLimitResult(allowed=True)

    def register_scan(self, url: str, scan_id: str, company_id: str) -> None:
        """
        Zaregistruje dokončený scan do URL cache.
        Volat po úspěšném vytvoření skenu.
        """
        normalized = self.normalize_url(url)
        with self._lock:
            self._url_cache[normalized] = URLCacheEntry(
                scan_id=scan_id,
                company_id=company_id,
                scanned_at=time.time(),
            )
            logger.info(f"[RateLimit] Registered scan: {normalized} → {scan_id}")

    def get_stats(self) -> dict:
        """Vrátí statistiky pro admin/debug."""
        now = time.time()
        cutoff = now - IP_WINDOW_SECONDS
        with self._lock:
            return {
                "cached_urls": len(self._url_cache),
                "active_ips": len(self._ip_timestamps),
                "scans_last_hour": len(
                    [t for t in self._global_timestamps if t > cutoff]
                ),
                "global_limit": GLOBAL_LIMIT,
            }


# ── Singleton instance ──
scan_limiter = ScanRateLimiter()
