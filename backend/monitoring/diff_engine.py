"""
AIshield.cz — Diff Engine (Úkol 30)
Porovnává dva skeny stejného webu a identifikuje ROZDÍLY.

Výstup: strukturovaný diff se 4 kategoriemi:
  - PŘIDÁNO: nové AI systémy, které předtím nebyly
  - ODEBRÁNO: AI systémy, které zmizely
  - ZMĚNĚNO: systémy se změněnými atributy
  - BEZE ZMĚNY: stabilní findings
"""

from dataclasses import dataclass, field
from datetime import datetime
from backend.database import get_supabase


@dataclass
class FindingChange:
    """Jedna změna v nálezu."""
    finding_name: str
    category: str
    risk_level: str
    ai_act_article: str
    change_type: str  # "added" | "removed" | "changed" | "unchanged"
    details: str = ""
    old_value: dict = field(default_factory=dict)
    new_value: dict = field(default_factory=dict)


@dataclass
class ScanDiff:
    """Kompletní diff mezi dvěma skeny."""
    company_id: str
    company_name: str
    url: str
    previous_scan_id: str
    current_scan_id: str
    previous_scan_date: str
    current_scan_date: str
    added: list[FindingChange] = field(default_factory=list)
    removed: list[FindingChange] = field(default_factory=list)
    changed: list[FindingChange] = field(default_factory=list)
    unchanged: list[FindingChange] = field(default_factory=list)
    has_changes: bool = False
    summary: str = ""

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)


# Atributy, které sledujeme pro "changed" detekci
TRACKED_ATTRIBUTES = [
    "risk_level",
    "ai_act_article",
    "action_required",
    "category",
]


def _finding_key(f: dict) -> str:
    """Unikátní klíč pro matching findings mezi skeny."""
    # Matchujeme primárně dle name + category
    name = (f.get("name") or "").strip().lower()
    cat = (f.get("category") or "").strip().lower()
    return f"{name}|{cat}"


def _compare_attributes(old: dict, new: dict) -> list[str]:
    """Porovná sledované atributy a vrátí seznam změn."""
    changes = []
    for attr in TRACKED_ATTRIBUTES:
        old_val = (old.get(attr) or "").strip()
        new_val = (new.get(attr) or "").strip()
        if old_val != new_val:
            changes.append(f"{attr}: '{old_val}' → '{new_val}'")
    return changes


async def compare_scans(previous_scan_id: str, current_scan_id: str) -> ScanDiff:
    """
    Porovná dva skeny a vrátí strukturovaný diff.

    Args:
        previous_scan_id: ID staršího skenu
        current_scan_id: ID novějšího skenu

    Returns:
        ScanDiff s kategorizovanými změnami
    """
    supabase = get_supabase()

    # Načteme oba skeny
    prev_scan = supabase.table("scans").select(
        "id, company_id, url_scanned, started_at, finished_at"
    ).eq("id", previous_scan_id).limit(1).execute()

    curr_scan = supabase.table("scans").select(
        "id, company_id, url_scanned, started_at, finished_at"
    ).eq("id", current_scan_id).limit(1).execute()

    if not prev_scan.data or not curr_scan.data:
        raise ValueError("Jeden nebo oba skeny nenalezeny")

    prev = prev_scan.data[0]
    curr = curr_scan.data[0]

    # Ověříme, že jde o stejnou firmu
    if prev["company_id"] != curr["company_id"]:
        raise ValueError("Skeny patří různým firmám — nelze porovnat")

    # Načteme firmu
    company = supabase.table("companies").select(
        "name, url"
    ).eq("id", prev["company_id"]).limit(1).execute()
    company_name = company.data[0]["name"] if company.data else "Neznámá"
    url = company.data[0]["url"] if company.data else prev["url_scanned"]

    # Načteme findings (jen deployed, ne false positives)
    prev_findings = supabase.table("findings").select("*").eq(
        "scan_id", previous_scan_id
    ).neq("source", "ai_classified_fp").execute()

    curr_findings = supabase.table("findings").select("*").eq(
        "scan_id", current_scan_id
    ).neq("source", "ai_classified_fp").execute()

    # Indexujeme dle klíčů
    prev_dict: dict[str, dict] = {}
    for f in (prev_findings.data or []):
        key = _finding_key(f)
        prev_dict[key] = f

    curr_dict: dict[str, dict] = {}
    for f in (curr_findings.data or []):
        key = _finding_key(f)
        curr_dict[key] = f

    # Porovnáme
    diff = ScanDiff(
        company_id=prev["company_id"],
        company_name=company_name,
        url=url,
        previous_scan_id=previous_scan_id,
        current_scan_id=current_scan_id,
        previous_scan_date=prev.get("finished_at") or prev.get("started_at", ""),
        current_scan_date=curr.get("finished_at") or curr.get("started_at", ""),
    )

    prev_keys = set(prev_dict.keys())
    curr_keys = set(curr_dict.keys())

    # PŘIDÁNO: v novém, ne ve starém
    for key in (curr_keys - prev_keys):
        f = curr_dict[key]
        diff.added.append(FindingChange(
            finding_name=f.get("name", ""),
            category=f.get("category", ""),
            risk_level=f.get("risk_level", ""),
            ai_act_article=f.get("ai_act_article", ""),
            change_type="added",
            details=f"Nový AI systém detekován: {f.get('name', '')}",
            new_value=f,
        ))

    # ODEBRÁNO: ve starém, ne v novém
    for key in (prev_keys - curr_keys):
        f = prev_dict[key]
        diff.removed.append(FindingChange(
            finding_name=f.get("name", ""),
            category=f.get("category", ""),
            risk_level=f.get("risk_level", ""),
            ai_act_article=f.get("ai_act_article", ""),
            change_type="removed",
            details=f"AI systém zmizel: {f.get('name', '')}",
            old_value=f,
        ))

    # ZMĚNĚNO nebo BEZE ZMĚNY: v obou skenech
    for key in (prev_keys & curr_keys):
        old = prev_dict[key]
        new = curr_dict[key]
        attr_changes = _compare_attributes(old, new)

        if attr_changes:
            diff.changed.append(FindingChange(
                finding_name=new.get("name", ""),
                category=new.get("category", ""),
                risk_level=new.get("risk_level", ""),
                ai_act_article=new.get("ai_act_article", ""),
                change_type="changed",
                details="; ".join(attr_changes),
                old_value=old,
                new_value=new,
            ))
        else:
            diff.unchanged.append(FindingChange(
                finding_name=new.get("name", ""),
                category=new.get("category", ""),
                risk_level=new.get("risk_level", ""),
                ai_act_article=new.get("ai_act_article", ""),
                change_type="unchanged",
            ))

    diff.has_changes = bool(diff.added or diff.removed or diff.changed)

    # Generuj summary
    parts = []
    if diff.added:
        parts.append(f"+{len(diff.added)} nových")
    if diff.removed:
        parts.append(f"-{len(diff.removed)} odebraných")
    if diff.changed:
        parts.append(f"~{len(diff.changed)} změněných")
    if not parts:
        parts.append("Beze změn")

    diff.summary = f"{company_name}: {', '.join(parts)} (celkem {len(curr_dict)} AI systémů)"

    return diff


async def get_previous_scan(company_id: str, before_scan_id: str) -> str | None:
    """Najde předchozí sken pro danou firmu (před aktuálním)."""
    supabase = get_supabase()

    # Zjistíme datum aktuálního skenu
    curr = supabase.table("scans").select(
        "created_at"
    ).eq("id", before_scan_id).limit(1).execute()

    if not curr.data:
        return None

    curr_date = curr.data[0]["created_at"]

    # Najdeme předchozí sken
    prev = supabase.table("scans").select(
        "id"
    ).eq("company_id", company_id).eq(
        "status", "done"
    ).lt("created_at", curr_date).order(
        "created_at", desc=True
    ).limit(1).execute()

    if prev.data:
        return prev.data[0]["id"]
    return None


async def run_diff_for_company(company_id: str) -> ScanDiff | None:
    """
    Porovná poslední dva skeny firmy.
    Vrátí None pokud má firma jen jeden sken.
    """
    supabase = get_supabase()

    scans = supabase.table("scans").select(
        "id"
    ).eq("company_id", company_id).eq(
        "status", "done"
    ).order("created_at", desc=True).limit(2).execute()

    if not scans.data or len(scans.data) < 2:
        return None  # Jen jeden sken — nelze porovnat

    current_id = scans.data[0]["id"]
    previous_id = scans.data[1]["id"]

    return await compare_scans(previous_id, current_id)


async def save_diff_to_db(diff: ScanDiff) -> str:
    """Uloží diff do tabulky scan_diffs pro historii."""
    supabase = get_supabase()

    import json

    result = supabase.table("scan_diffs").insert({
        "company_id": diff.company_id,
        "previous_scan_id": diff.previous_scan_id,
        "current_scan_id": diff.current_scan_id,
        "has_changes": diff.has_changes,
        "added_count": len(diff.added),
        "removed_count": len(diff.removed),
        "changed_count": len(diff.changed),
        "unchanged_count": len(diff.unchanged),
        "summary": diff.summary,
        "details": json.dumps({
            "added": [{"name": c.finding_name, "details": c.details} for c in diff.added],
            "removed": [{"name": c.finding_name, "details": c.details} for c in diff.removed],
            "changed": [{"name": c.finding_name, "details": c.details} for c in diff.changed],
        }),
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return result.data[0]["id"] if result.data else ""
