#!/usr/bin/env python3
"""Schematische Zeichnungen (SVG) für Operationsartikel, selbst erzeugt, einheitlicher Stil.

Grundsatz (Auftrag Andreas 14.10.2026): lieber keine Zeichnung als eine falsche. Eine Zeichnung entsteht nur für Artikel,
die in ``data/media/op-figures/registry.json`` mit ``approved: true`` und einer Vorlage eingetragen sind. Die Einträge
beschreiben ausschließlich Zugangswege und Punkte, die in der Fachliteratur als Standard gelten, und werden relativ zu
anatomischen Orientierungspunkten (Landmarken) gesetzt, nicht frei gezeichnet.

Befehle:
  build    SVG-Dateien nach media/op/<slug>-schema.svg erzeugen (deterministisch)
  insert   Abschnitt „Schematische Darstellung“ in die Artikel einfügen, die eine Zeichnung haben
  check    OP-Artikel ohne Registereintrag oder mit offener Freigabe auflisten
  suggest  Vorschläge (approved=false) für OP-Artikel ohne Eintrag aus Schlüsselwortregeln; keine automatische Freigabe

Neue OP-Artikel: ``check`` zeigt sie an, ``suggest`` legt einen Vorschlag an, nach fachlicher Durchsicht wird ``approved`` auf true
gesetzt; ``build`` und ``insert`` erzeugen dann Zeichnung und Abschnitt. Ohne Freigabe bleibt der Artikel ohne Zeichnung.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "data/media/op-figures/registry.json"
OUT_DIR = REPO / "media/op"
W, H = 680, 790
CX = 300  # Körpermitte (im Körpersystem; der Körper wird um OFFX/OFFY verschoben)
OFFX, OFFY = 40, 62
LABEL_PX = 8.4  # geschätzte Zeichenbreite der fetten Beschriftung (Schriftgröße 13)
INK, SKIN, SKIN_LINE, MARK, MARK_ALT, LANDMARK, TEXT = "#26323a", "#f3ece4", "#6b6b6b", "#b3261e", "#d9822b", "#8a8a8a", "#26323a"
FIG_NOTE = "Schematische Darstellung, nicht maßstabsgetreu. Kein Ersatz für anatomische Atlanten oder Operationsanleitungen."

# ---------------------------------------------------------------------------
# Vorlagen: Körperumriss und Landmarken (Koordinaten im SVG)
# ---------------------------------------------------------------------------
TEMPLATES: dict[str, dict] = {
    "torso": {
        "view": "Vorderansicht",
        "outline": (f"M{CX-22},112 L{CX-22},150 C{CX-52},156 {CX-100},164 {CX-120},188 C{CX-124},194 {CX-122},204 {CX-120},210 "
                    f"C{CX-114},262 {CX-108},304 {CX-92},344 C{CX-100},384 {CX-108},414 {CX-106},444 C{CX-104},474 {CX-102},504 {CX-100},548 "
                    f"L{CX-14},548 C{CX-12},528 {CX-6},512 {CX},506 C{CX+6},512 {CX+12},528 {CX+14},548 L{CX+100},548 "
                    f"C{CX+102},504 {CX+104},474 {CX+106},444 C{CX+108},414 {CX+100},384 {CX+92},344 C{CX+108},304 {CX+114},262 {CX+120},210 "
                    f"C{CX+122},204 {CX+124},194 {CX+120},188 C{CX+100},164 {CX+52},156 {CX+22},150 L{CX+22},112 Z"),
        "extra": [f'<ellipse cx="{CX}" cy="64" rx="40" ry="50" fill="{SKIN}" stroke="{SKIN_LINE}" stroke-width="2"/>'],
        "landmarks": {
            "jugulum": (CX, 152), "xiphoid": (CX, 268), "nabel": (CX, 356), "symphyse": (CX, 478),
            "sias_r": (CX - 70, 424), "sias_l": (CX + 70, 424),
            "rippenbogen_r": (CX - 92, 330), "rippenbogen_l": (CX + 92, 330),
            "mamille_r": (CX - 52, 236), "mamille_l": (CX + 52, 236),
            "hals_r": (CX - 14, 128), "hals_l": (CX + 14, 128),
        },
        "guides": [  # Orientierungslinien (grau, dünn)
            ("path", f"M{CX},152 L{CX},268", "Sternum"),
            ("path", f"M{CX},268 C{CX-30},276 {CX-70},292 {CX-92},330", None),
            ("path", f"M{CX},268 C{CX+30},276 {CX+70},292 {CX+92},330", None),
            ("path", f"M{CX-70},424 L{CX-8},476", None), ("path", f"M{CX+70},424 L{CX+8},476", None),
        ],
        "guide_labels": [("Jugulum", CX + 8, 150, "start"), ("Nabel", CX + 10, 360, "start"), ("Symphyse", CX + 10, 492, "start")],
        "sides": {"patient_right": "left"},  # rechte Körperseite liegt im Bild links
    },
    "neck": {
        "view": "Vorderansicht",
        "outline": (f"M{CX-70},40 C{CX-72},100 {CX-60},150 {CX-48},190 C{CX-60},200 {CX-100},206 {CX-150},228 L{CX-150},330 "
                    f"L{CX+150},330 L{CX+150},228 C{CX+100},206 {CX+60},200 {CX+48},190 C{CX+60},150 {CX+72},100 {CX+70},40 Z"),
        "extra": [
            f'<path d="M{CX-70},40 C{CX-40},62 {CX+40},62 {CX+70},40" fill="none" stroke="{SKIN_LINE}" stroke-width="2"/>',
            # Zungenbein
            f'<path d="M{CX-30},94 L{CX+30},94" stroke="{LANDMARK}" stroke-width="5" stroke-linecap="round"/>',
            # Schildknorpel
            f'<path d="M{CX-26},116 L{CX},108 L{CX+26},116 L{CX+22},148 L{CX},154 L{CX-22},148 Z" fill="#e6ddd2" stroke="{LANDMARK}" stroke-width="2"/>',
            # Ringknorpel
            f'<rect x="{CX-17}" y="160" width="34" height="14" rx="5" fill="#dcd2c6" stroke="{LANDMARK}" stroke-width="2"/>',
            # Schlüsselbeine
            f'<path d="M{CX-148},236 C{CX-90},222 {CX-40},224 {CX-10},242" fill="none" stroke="{LANDMARK}" stroke-width="3" stroke-linecap="round"/>',
            f'<path d="M{CX+148},236 C{CX+90},222 {CX+40},224 {CX+10},242" fill="none" stroke="{LANDMARK}" stroke-width="3" stroke-linecap="round"/>',
        ] + [f'<path d="M{CX-13},{182 + i * 11} Q{CX},{186 + i * 11} {CX+13},{182 + i * 11}" fill="none" stroke="{LANDMARK}" stroke-width="2.4"/>' for i in range(5)],
        "landmarks": {"ringknorpel": (CX, 167), "trachealspange_2": (CX, 193), "trachealspange_4": (CX, 215), "jugulum": (CX, 244)},
        "guides": [],
        "guide_labels": [("Zungenbein", CX + 100, 98, "start", (CX + 32, 94)), ("Schildknorpel", CX + 100, 134, "start", (CX + 27, 130)),
                         ("Ringknorpel", CX + 100, 172, "start", (CX + 18, 167)), ("Jugulum", CX + 100, 250, "start", (CX + 6, 244))],
        "height": 520,
        "sides": {"patient_right": "left"},
    },
    "knee": {
        "view": "rechtes Knie, Ansicht von vorn",
        "outline": (f"M{CX-86},40 C{CX-84},140 {CX-76},230 {CX-68},300 C{CX-64},350 {CX-58},420 {CX-46},520 C{CX-44},560 {CX-42},600 {CX-40},650 "
                    f"L{CX+40},650 C{CX+42},600 {CX+44},560 {CX+46},520 C{CX+58},420 {CX+64},350 {CX+68},300 C{CX+76},230 {CX+84},140 {CX+86},40 Z"),
        "extra": [
            f'<ellipse cx="{CX}" cy="292" rx="30" ry="34" fill="#ece3d8" stroke="{LANDMARK}" stroke-width="2.4"/>',  # Patella
            f'<path d="M{CX},326 L{CX},384" stroke="{LANDMARK}" stroke-width="7" stroke-linecap="round" opacity=".7"/>',  # Patellarsehne
            f'<ellipse cx="{CX}" cy="392" rx="12" ry="8" fill="#e0d6ca" stroke="{LANDMARK}" stroke-width="2"/>',  # Tuberositas tibiae
            f'<path d="M{CX-66},340 L{CX+66},340" stroke="{LANDMARK}" stroke-width="2" stroke-dasharray="6 5"/>',  # Gelenkspalt
        ],
        "landmarks": {"patella_oben": (CX, 256), "patella_mitte": (CX, 292), "patella_unten": (CX, 326), "tuberositas": (CX, 392),
                      "gelenkspalt_lateral": (CX - 46, 340), "gelenkspalt_medial": (CX + 46, 340)},
        "guides": [],
        "guide_labels": [("Patella", CX + 38, 288, "start"), ("Patellarsehne", CX + 18, 360, "start"), ("Tuberositas tibiae", CX + 20, 396, "start"),
                         ("Gelenkspalt", CX - 70, 336, "end")],
        "sides": {"lateral": "left", "medial": "right"},
    },
}


# ---------------------------------------------------------------------------
# Elemente
# ---------------------------------------------------------------------------
def pt(tpl: dict, ref) -> tuple[float, float]:
    if isinstance(ref, str):
        return tpl["landmarks"][ref]
    return float(ref[0]), float(ref[1])


def resolve(tpl: dict, ref, dx: float = 0, dy: float = 0) -> tuple[float, float]:
    x, y = pt(tpl, ref)
    return x + dx, y + dy


def _svg_text(x: float, y: float, text: str, anchor: str = "start", size: int = 14, weight: str = "normal", color: str = TEXT) -> str:
    lines = text.split("\n")
    out = [f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{size}" font-weight="{weight}" '
           f'fill="{color}" text-anchor="{anchor}">']
    for i, ln in enumerate(lines):
        out.append(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else size + 3}">{escape(ln)}</tspan>')
    out.append("</text>")
    return "".join(out)


def render_elements(tpl: dict, elements: list[dict]) -> tuple[list[str], list[str]]:
    """Gibt (Markierungen, Beschriftungen) zurück."""
    marks, labels = [], []
    for e in elements:
        color = MARK_ALT if e.get("alt") else MARK
        dash = ' stroke-dasharray="9 6"' if e.get("alt") else ""
        t = e["type"]
        anchor_xy = None
        if t == "line":
            pts = [resolve(tpl, p, *(e.get("offset") or (0, 0))) for p in e["points"]]
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            marks.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"{dash}/>')
            anchor_xy = pts[len(pts) // 2] if len(pts) % 2 else ((pts[len(pts)//2 - 1][0] + pts[len(pts)//2][0]) / 2, (pts[len(pts)//2 - 1][1] + pts[len(pts)//2][1]) / 2)
        elif t == "curve":  # quadratische Kurve zwischen zwei Punkten, bulge = senkrechte Auslenkung
            (x1, y1), (x2, y2) = [resolve(tpl, p) for p in e["points"][:2]]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + e.get("bulge", 0)
            marks.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round"{dash}/>')
            anchor_xy = ((x1 + x2) / 2, (y1 + y2) / 2 + e.get("bulge", 0) / 2)
        elif t == "port":
            x, y = resolve(tpl, e["at"], *(e.get("offset") or (0, 0)))
            r = e.get("r", 7)
            marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="#fff" stroke-width="1.5"/>')
            anchor_xy = (x, y)
        elif t == "cross":  # Punktionsstelle
            x, y = resolve(tpl, e["at"], *(e.get("offset") or (0, 0)))
            marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#fff" stroke="{color}" stroke-width="3"/>'
                         f'<path d="M{x-5:.1f},{y:.1f} L{x+5:.1f},{y:.1f} M{x:.1f},{y-5:.1f} L{x:.1f},{y+5:.1f}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>')
            anchor_xy = (x, y)
        elif t == "bracket":  # Bereich entlang der Mittellinie
            (x1, y1), (x2, y2) = [resolve(tpl, p) for p in e["points"][:2]]
            xo = e.get("xoffset", 24)
            marks.append(f'<path d="M{x1+xo:.1f},{y1:.1f} L{x1+xo+8:.1f},{y1:.1f} L{x1+xo+8:.1f},{y2:.1f} L{x1+xo:.1f},{y2:.1f}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                         f'<path d="M{x1:.1f},{y1:.1f} L{x1+xo:.1f},{y1:.1f} M{x1:.1f},{y2:.1f} L{x1+xo:.1f},{y2:.1f}" stroke="{color}" stroke-width="2" stroke-dasharray="3 3"/>')
            anchor_xy = (x1 + xo + 8, (y1 + y2) / 2)
        else:
            raise ValueError(f"unbekannter Elementtyp {t}")
        if e.get("label"):
            side = e.get("side", "right")
            ly = e.get("label_y", anchor_xy[1]) + OFFY
            ax, ay = anchor_xy[0] + OFFX, anchor_xy[1] + OFFY
            width = max(len(x) for x in e["label"].split("\n")) * LABEL_PX
            if side == "left":
                lx, anchor, edge = 16, "start", 16 + width + 8
            else:
                lx, anchor, edge = W - 16, "end", W - 16 - width - 8
            labels.append(f'<path d="M{edge:.1f},{ly - 4:.1f} L{ax:.1f},{ay:.1f}" stroke="{color}" stroke-width="1.2" fill="none" opacity=".85"/>')
            labels.append(_svg_text(lx, ly, e["label"], anchor=anchor, size=13, weight="bold", color=color))
    return marks, labels


def build_svg(slug: str, entry: dict) -> str:
    tpl = TEMPLATES[entry["template"]]
    H = tpl.get("height", 790)
    marks, labels = render_elements(tpl, entry["elements"])
    title = entry["title"]
    desc = entry["caption"]
    guides = []
    for kind, d, _ in tpl.get("guides", []):
        guides.append(f'<path d="{d}" fill="none" stroke="{LANDMARK}" stroke-width="1.6" stroke-dasharray="2 4" opacity=".8"/>')
    glabels = []
    for gl in tpl.get("guide_labels", []):
        t, x, y, a = gl[:4]
        glabels.append(_svg_text(x, y, t, anchor=a, size=11, color=LANDMARK))
        if len(gl) > 4:
            glabels.append(f'<path d="M{x - 4},{y - 4} L{gl[4][0]},{gl[4][1]}" stroke="{LANDMARK}" stroke-width="1" opacity=".8"/>')
    sides = tpl.get("sides", {})
    orient = ""
    if "patient_right" in sides:
        orient = (_svg_text(OFFX + CX - 150, H - 52, "Patient rechts", "end", 11, color=LANDMARK) + _svg_text(OFFX + CX + 150, H - 52, "Patient links", "start", 11, color=LANDMARK))
    elif "lateral" in sides:
        orient = (_svg_text(OFFX + CX - 150, H - 52, "lateral", "end", 11, color=LANDMARK) + _svg_text(OFFX + CX + 150, H - 52, "medial", "start", 11, color=LANDMARK))
    body = [f'<g transform="translate({OFFX},{OFFY})">',
            f'<path d="{tpl["outline"]}" fill="{SKIN}" stroke="{SKIN_LINE}" stroke-width="2.4" stroke-linejoin="round"/>',
            *tpl["extra"], *guides, *glabels, *marks, "</g>"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        f"<title id=\"t\">{escape(title)}</title><desc id=\"d\">{escape(desc)}</desc>",
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="#d5d8da" stroke-width="2" rx="8"/>',
        _svg_text(W / 2, 28, title, "middle", 17, "bold", INK),
        _svg_text(W / 2, 47, f"Schema, {tpl['view']}", "middle", 12, color=LANDMARK),
        *body, *labels, orient,
        _svg_text(W / 2, H - 30, "Schematische Darstellung, nicht maßstabsgetreu.", "middle", 11, color="#555555"),
        _svg_text(W / 2, H - 15, "Kein Ersatz für anatomische Atlanten oder Operationsanleitungen.", "middle", 11, color="#555555"),
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Register, Einfügen in Artikel
# ---------------------------------------------------------------------------
def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def op_articles() -> dict[str, Path]:
    """Alle Operationsartikel: Artikel mit WM-OP-Bezug über die Planungstabelle sind nicht im Frontmatter vermerkt;
    deshalb gelten Registereinträge sowie Artikel, deren Frontmatter ``ops`` nutzt oder deren Slug im Register steht."""
    found = {}
    for p in (REPO / "content/specialties").rglob("*.md"):
        found[p.stem] = p
    return found


SECTION_RE = re.compile(r"\n## Schematische Darstellung\n.*?(?=\n## |\Z)", re.S)


def figure_section(slug: str, entry: dict) -> str:
    alt = entry["title"]
    return (f"\n## Schematische Darstellung\n\n![{alt}](../../../media/op/{slug}-schema.svg)\n\n"
            f"*{entry['caption']} {FIG_NOTE}*\n")


def cmd_build(args) -> int:
    reg = load_registry()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for slug, entry in sorted(reg["articles"].items()):
        if not entry.get("approved"):
            continue
        (OUT_DIR / f"{slug}-schema.svg").write_text(build_svg(slug, entry), encoding="utf-8")
        n += 1
    print(f"{n} Zeichnungen erzeugt")
    return 0


def cmd_insert(args) -> int:
    reg = load_registry()
    arts = op_articles()
    n = 0
    for slug, entry in sorted(reg["articles"].items()):
        if not entry.get("approved"):
            continue
        path = arts.get(slug)
        if not path:
            print(f"Artikel fehlt: {slug}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        section = figure_section(slug, entry)
        if "## Schematische Darstellung" in text:
            new = SECTION_RE.sub(lambda m: section.rstrip("\n"), text)
        else:  # vor der Literatur einfügen
            m = re.search(r"\n## Literatur", text)
            new = text[:m.start()] + section + text[m.start():] if m else text.rstrip("\n") + "\n" + section
        if new != text:
            path.write_text(new, encoding="utf-8")
            n += 1
    print(f"{n} Artikel aktualisiert")
    return 0


KEYWORD_RULES = [  # (Schlüsselwort im Slug, Vorlage, Hinweis) nur für Vorschläge
    ("sternotomie", "torso", "mediane Sternotomie prüfen"), ("klappenersatz", "torso", "Zugang prüfen"),
    ("kaiserschnitt", "torso", "Pfannenstiel prüfen"), ("hysterektomie", "torso", "Zugang/Ports prüfen"),
    ("tracheotomie", "neck", "Trachealspangen prüfen"), ("arthroskopie", "knee", "Portale prüfen"),
    ("endoprothese", "knee", "nur Knie: mediane Inzision prüfen"),
]


def cmd_check(args) -> int:
    reg = load_registry()
    arts = op_articles()
    todo = []
    for slug in sorted(arts):
        if not any(m in str(arts[slug]) for m in ("chirurgie", "orthopaedie", "neurologie", "gynaekologie", "urologie", "pneumologie",
                                                  "augenheilkunde", "intensivmedizin", "kardiologie", "nephrologie", "gastroenterologie",
                                                  "haematologie-onkologie")):
            continue
        e = reg["articles"].get(slug)
        if e is None:
            todo.append((slug, "kein Eintrag"))
        elif not e.get("approved"):
            todo.append((slug, "Freigabe offen"))
    keys = [s for s, _ in todo]
    ops = [s for s in keys if arts[s] and _is_op(arts[s])]
    for s, why in todo:
        if s in ops:
            print(f"{s}: {why}")
    print(f"{len(ops)} OP-Artikel ohne freigegebene Zeichnung", file=sys.stderr)
    return 0


def _is_op(path: Path) -> bool:
    txt = path.read_text(encoding="utf-8")[:2500]
    return bool(re.search(r"^(change_summary|title):.*(Operation|operativ|Chirurg|ektomie|plastik|Transplantation|Implantation|Resektion|Drainage|Kanülierung|Thrombektomie)", txt, re.M | re.I))


def cmd_suggest(args) -> int:
    reg = load_registry()
    n = 0
    for slug, path in sorted(op_articles().items()):
        if slug in reg["articles"] or not _is_op(path):
            continue
        for key, tpl, note in KEYWORD_RULES:
            if key in slug:
                reg["articles"][slug] = {"approved": False, "template": tpl, "vorschlag": note, "title": "", "caption": "", "elements": []}
                n += 1
                break
    REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{n} Vorschläge angelegt (approved=false)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "insert", "check", "suggest"])
    args = ap.parse_args()
    return {"build": cmd_build, "insert": cmd_insert, "check": cmd_check, "suggest": cmd_suggest}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
