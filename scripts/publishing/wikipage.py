"""
wikipage.py — assemble the final MediaWiki page of an article.

Input: validated frontmatter + Markdown body.  Output: wikitext made of

  1. a machine-readable marker (slug, version, content hash) for idempotency
  2. notice boxes (emergency / disclaimers) from data/legal/disclaimers.yaml
  3. an information box generated from the metadata
  4. the converted article body
  5. source links generated from pubmed_ids / references / guidelines
  6. a version box
  7. categories derived from the metadata

Authors never write categories, boxes or disclaimers; this module is the only
place that produces them (see content/templates/README.md).
Also builds the replacement pages for withdrawn content (safety hold,
retracted, archived).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date

import md2wiki as m2w

MARKER_RE = re.compile(
    r'^<!-- wikimedica-managed slug="(?P<slug>[a-z0-9-]+)" version="(?P<version>[^"]*)" '
    r'sha256="(?P<sha>[0-9a-f]{64})" -->'
)

TYPE_LABEL = {
    "professional": "Fachartikel", "patient": "Patienteninformation",
    "consent": "Aufklärungsmodul", "discharge": "Entlassinformation",
    "pharmaka": "Arzneimittel (Pharmaka)", "therapy": "Therapieprotokoll",
}
KIND_LABEL = {"guideline-summary": "Leitlinien-Zusammenfassung", "qr-media-reference": "Medienverweis"}
AUDIENCE_LABEL = {
    "physicians": "Ärztinnen und Ärzte", "nursing": "Pflegefachpersonen",
    "emergency-services": "Rettungsdienst", "pharmacists": "Apothekerinnen und Apotheker",
    "medical-professionals": "Medizinisches Fachpersonal", "patients": "Patientinnen und Patienten",
    "relatives": "Angehörige", "clinical-teams": "Klinische Teams",
}
RISK_LABEL = {"low": "niedrig", "moderate": "mittel", "high": "hoch"}
STATUS_LABEL = {"approved": "Freigegeben (Vorabversion)", "published": "Veröffentlicht"}

# Neutral text for clinic-branding placeholders in the PUBLIC wiki version.
CLINIC_PLACEHOLDERS = {
    "clinic_name": "[Name der Einrichtung]",
    "clinic_address": "[Anschrift der Einrichtung]",
    "clinic_phone": "[Telefonnummer der Einrichtung]",
}
TITLE_FORBIDDEN = re.compile(r"[#<>\[\]|{}:\x00-\x1f]|~~~|^\s|\s$|^/|\s{2,}")
SAFE_CSS = re.compile(r"^[a-z0-9 _-]+$")


@dataclass
class Page:
    title: str
    slug: str
    version: str
    wikitext: str = ""
    sha256: str = ""
    kind: str = "article"  # article | withdrawal
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_date(value) -> str:
    if not value:
        return "—"
    try:
        return date.fromisoformat(str(value)).strftime("%d.%m.%Y")
    except ValueError:
        return m2w.esc(str(value))


def validate_title(title: str) -> list[str]:
    problems = []
    if not isinstance(title, str) or not title.strip():
        return ["title is empty"]
    if len(title.encode("utf-8")) > 240:
        problems.append("title is longer than 240 bytes")
    if TITLE_FORBIDDEN.search(title):
        problems.append(
            f"title '{title}' contains characters that are not allowed in a page title "
            "(# < > [ ] | { } : leading/trailing/double spaces, leading '/'); "
            "a colon would address another namespace — use a dash instead"
        )
    return problems


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _with_marker(slug: str, version: str, body_wikitext: str) -> tuple[str, str]:
    digest = _sha(body_wikitext)
    marker = f'<!-- wikimedica-managed slug="{slug}" version="{version}" sha256="{digest}" -->'
    return marker + "\n" + body_wikitext, digest


def parse_marker(wikitext: str) -> dict | None:
    first = wikitext.split("\n", 1)[0] if wikitext else ""
    m = MARKER_RE.match(first)
    return m.groupdict() if m else None


def marker_is_intact(wikitext: str) -> bool:
    """True if the stored hash matches the stored content (nobody edited it by hand)."""
    marker = parse_marker(wikitext)
    if not marker:
        return False
    rest = wikitext.split("\n", 1)[1] if "\n" in wikitext else ""
    return _sha(rest) == marker["sha"]


# ---------------------------------------------------------------------------
# Notices (disclaimers)
# ---------------------------------------------------------------------------

def select_blocks(fm: dict, disclaimers: dict) -> list[str]:
    names = list(disclaimers["profiles"].get(fm.get("article_type"), ["general"]))
    rules = disclaimers.get("rules", {})
    names += rules.get("by_content_kind", {}).get(fm.get("content_kind", "article"), [])
    names += rules.get("by_risk_level", {}).get(fm.get("risk_level"), [])
    if fm.get("ai_assisted") is True:
        names += rules.get("by_ai_assisted", {}).get(True, [])
    seen: list[str] = []
    for name in names:
        if name not in seen:
            seen.append(name)
    return seen


def render_notice(block: dict) -> str:
    css = block.get("css_class", "wm-disclaimer")
    if not SAFE_CSS.match(css):
        css = "wm-disclaimer"
    return (f'<div class="wm-notice {css}">\n\'\'\'{m2w.esc(block["title"])}\'\'\'<br />\n'
            f'{m2w.esc(block["text"])}\n</div>')


def render_notices(fm: dict, disclaimers: dict) -> str:
    blocks = [render_notice(disclaimers["blocks"][n]) for n in select_blocks(fm, disclaimers)]
    return '<div class="wm-notices">\n' + "\n".join(blocks) + "\n</div>"


# ---------------------------------------------------------------------------
# Information box, sources, version box, categories
# ---------------------------------------------------------------------------

def _cat_link(name: str) -> str:
    return f"[[:Category:{name}|{m2w.esc(name)}]]"


def render_infobox(fm: dict, show_names: bool) -> str:
    rows: list[tuple[str, str]] = []
    specialties = [fm["specialty"], *(fm.get("secondary_specialties") or [])]
    rows.append(("Fachgebiet", ", ".join(_cat_link(s) for s in specialties)))
    kind = KIND_LABEL.get(fm.get("content_kind", "article"))
    rows.append(("Artikeltyp", m2w.esc(TYPE_LABEL.get(fm["article_type"], fm["article_type"]) + (f" · {kind}" if kind else ""))))
    audience = [AUDIENCE_LABEL.get(a, a) for a in fm.get("target_audience") or []]
    rows.append(("Zielgruppe", m2w.esc(", ".join(audience)) or "—"))
    rows.append(("Risikoklasse", m2w.esc(RISK_LABEL.get(fm.get("risk_level"), "—"))))
    if fm.get("icd10"):
        rows.append(("ICD-10-GM", m2w.esc(", ".join(map(str, fm["icd10"])))))
    if fm.get("active_substances"):
        rows.append(("Wirkstoff(e)", m2w.esc(", ".join(map(str, fm["active_substances"])))))
    if fm.get("atc_codes"):
        rows.append(("ATC-Code(s)", m2w.esc(", ".join(map(str, fm["atc_codes"])))))
    reviewers = fm.get("reviewers") or []
    review = f"Fachlich geprüft ({len(reviewers)} Gutachten)"
    if fm.get("risk_level") == "high" and fm.get("medical_advisor"):
        review += "; Medical-Advisor-Freigabe " + _fmt_date(fm.get("medical_advisor_signoff_date"))
    rows.append(("Redaktionelle Prüfung", m2w.esc(review)))
    if show_names:
        authors = ", ".join(a["name"] for a in fm.get("authors") or [] if isinstance(a, dict) and a.get("name"))
        rows.append(("Autorenschaft", m2w.esc(authors)))
        names = ", ".join(r["name"] for r in reviewers if isinstance(r, dict) and r.get("name"))
        rows.append(("Gutachten von", m2w.esc(names)))
    rows.append(("Status", m2w.esc(STATUS_LABEL.get(fm.get("status"), str(fm.get("status"))))))
    lic = fm.get("license") or fm.get("licence")
    rows.append(("Lizenz", m2w.esc(str(lic)) if lic else "—"))
    out = ['{| class="wikitable wm-infobox"', "|+ Artikelinformationen"]
    for label, value in rows:
        out += ["|-", f"! {label}", f"| {value}"]
    out.append("|}")
    return "\n".join(out)


def render_sources(fm: dict) -> str:
    items: list[str] = []
    for ref in fm.get("references") or []:
        if not isinstance(ref, dict):
            continue
        line = m2w.esc(str(ref.get("citation", "")))
        if ref.get("pmid") and re.fullmatch(r"\d{1,9}", str(ref["pmid"])):
            line += f" [https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/ PubMed]"
        if ref.get("doi") and re.fullmatch(r"10\.\d{4,9}/[^\s\]\[|<>\"']+", str(ref["doi"])):
            line += f" [https://doi.org/{ref['doi']} DOI]"
        if ref.get("url") and m2w.SAFE_URL_RE.match(str(ref["url"])):
            line += f" [{m2w.esc_url(str(ref['url']))} Link]"
        items.append("* " + line)
    for pmid in fm.get("pubmed_ids") or []:
        if re.fullmatch(r"\d{1,9}", str(pmid)):
            items.append(f"* PMID [https://pubmed.ncbi.nlm.nih.gov/{pmid}/ {pmid}]")
    for g in fm.get("guidelines") or []:
        if not isinstance(g, dict):
            continue
        detail = ", ".join(str(x) for x in (g.get("issuer"), g.get("year")) if x)
        if g.get("awmf_register"):
            detail += (", " if detail else "") + f"AWMF-Reg.-Nr. {g['awmf_register']}"
        line = m2w.esc(str(g.get("title", ""))) + (f" ({m2w.esc(detail)})" if detail else "")
        if g.get("url") and m2w.SAFE_URL_RE.match(str(g["url"])):
            line += f" [{m2w.esc_url(str(g['url']))} Link]"
        items.append("* " + line)
    if not items:
        return ""
    return "== Quellenverweise ==\n\n" + "\n".join(items)


def render_versionbox(fm: dict) -> str:
    summary = m2w.esc(str(fm.get("change_summary") or "—"))
    return "\n".join([
        '{| class="wikitable wm-versionbox"',
        "! Version !! Stand !! Änderung !! Nächste Prüfung",
        "|-",
        f"| {m2w.esc(str(fm.get('version')))} || {_fmt_date(fm.get('updated'))} || {summary} || {_fmt_date(fm.get('next_review'))}",
        "|}",
    ])


def categories(fm: dict) -> list[str]:
    cats = [fm["specialty"], *(fm.get("secondary_specialties") or [])]
    cats.append("Artikeltyp: " + TYPE_LABEL.get(fm["article_type"], fm["article_type"]))
    if fm.get("content_kind") in KIND_LABEL:
        cats.append("Artikeltyp: " + KIND_LABEL[fm["content_kind"]])
    if fm.get("sex_gender_relevance") == "relevant" and "Gender-Medizin" not in cats:
        cats.append("Gender-Medizin")  # cross-cutting flagship category
    if fm.get("risk_level") == "high":
        cats.append("Risikoklasse: hoch")
    seen: list[str] = []
    for c in cats:
        if c not in seen:
            seen.append(c)
    return seen


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------

_BANNER_RE = re.compile(r"(?:^[ \t]{0,3}>.*\n?)+", re.MULTILINE)


def strip_status_banner(markdown: str) -> str:
    """Remove the template's status banner (> **Status:** … **Version:** …): the info box replaces it."""
    def drop(match: re.Match) -> str:
        block = match.group(0)
        return "" if "**Status:**" in block and "**Version:**" in block else block
    return _BANNER_RE.sub(drop, markdown)


def placeholder_values(fm: dict) -> dict[str, str]:
    values = {
        "title": str(fm.get("title", "")), "specialty": str(fm.get("specialty", "")),
        "status": STATUS_LABEL.get(fm.get("status"), str(fm.get("status", ""))),
        "version": str(fm.get("version", "")), "updated": _fmt_date(fm.get("updated")),
        "license": str(fm.get("license") or fm.get("licence") or "—"),
        "procedure": str(fm.get("procedure", "")), "parent_slug": str(fm.get("parent_slug", "")),
        "qr_media_url": str(fm.get("qr_media_url", "")),
    }
    values.update(CLINIC_PLACEHOLDERS)
    return values


def build_article_page(
    fm: dict, body_md: str, *, slug: str, disclaimers: dict,
    internal_pages: dict[str, str] | None = None, show_names: bool = False,
) -> Page:
    page = Page(title=str(fm.get("title", "")).strip(), slug=slug, version=str(fm.get("version", "")))
    page.errors += validate_title(page.title)

    text, unknown = m2w.substitute_placeholders(strip_status_banner(body_md), placeholder_values(fm))
    if unknown:
        page.errors.append("unresolved placeholders (would transclude templates): "
                           + ", ".join("{{ " + n + " }}" for n in unknown))
    if page.title and page.title[0].islower():
        page.warnings.append("title starts with a lowercase letter; MediaWiki capitalises the first letter")

    ctx = m2w.ConvertContext(title=page.title, internal_pages=internal_pages or {})
    body_wikitext = m2w.convert(text, ctx).rstrip("\n")
    page.warnings += ctx.warnings

    parts = [render_notices(fm, disclaimers), render_infobox(fm, show_names), body_wikitext]
    sources = render_sources(fm)
    if sources:
        parts.append(sources)
    parts.append(render_versionbox(fm))
    parts.append("\n".join(f"[[Category:{c}]]" for c in categories(fm)))
    page.wikitext, page.sha256 = _with_marker(slug, page.version, "\n\n".join(parts) + "\n")
    return page


def build_withdrawal_page(fm: dict, *, slug: str, reason: str, disclaimers: dict) -> Page:
    """Replacement page for content that must not be shown (safety hold, retracted, archived)."""
    page = Page(title=str(fm.get("title", "")).strip(), slug=slug,
                version=str(fm.get("version", "")), kind="withdrawal")
    page.errors += validate_title(page.title)
    if reason == "safety_hold":
        title, text = ("Vorübergehend nicht verfügbar",
                       "Dieser Artikel ist vorübergehend nicht verfügbar, weil er derzeit einer "
                       "Sicherheitsprüfung unterzogen wird.")
        cat = "Gesperrt (Sicherheitsprüfung)"
    elif reason == "retracted":
        title, text = ("Artikel zurückgezogen",
                       str(fm.get("retraction_notice") or "Dieser Artikel wurde zurückgezogen."))
        cat = "Zurückgezogen"
    else:
        title, text = ("Artikel archiviert",
                       "Dieser Artikel wurde archiviert und gibt nicht den aktuellen Stand wieder.")
        cat = "Archiviert"
    emergency = disclaimers["blocks"]["emergency"]
    body = "\n\n".join([
        render_notice({"title": title, "text": text, "css_class": "wm-withdrawn"}),
        render_notice(emergency),
        f"[[Category:{cat}]]",
    ]) + "\n"
    page.wikitext, page.sha256 = _with_marker(slug, page.version, body)
    return page
