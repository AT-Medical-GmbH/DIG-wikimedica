"""
md2wiki.py — safe, dependency-free Markdown -> MediaWiki wikitext converter.

Design goals (in this order):

1. SAFE.  Article text is untrusted input. In wikitext, ``{{x}}`` transcludes a
   template, ``[[Category:x]]`` categorises a page, ``__NOTOC__`` is a magic
   word, ``{| ... |}`` is a table and ``<script>`` must never get through.
   Every character of *plain text* is therefore entity-escaped; wikitext markup
   is produced only by this module, from the recognised Markdown constructs.
   Categories, infoboxes and notices are added by the page builder, never by
   the author.
2. Faithful for the Markdown subset used by the Wikimedica templates:
   headings, paragraphs, bold/italic/strike/code, links, ordered/unordered
   (nested) lists, task items, pipe tables, block quotes, fenced code,
   horizontal rules.
3. Deterministic: identical input gives identical output (needed for the
   idempotent import).

Not supported on purpose: raw HTML (escaped), images (replaced by their
alternative text; uploads are restricted), footnotes, Setext headings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
SAFE_URL_RE = re.compile(r"^(https?://|mailto:)", re.IGNORECASE)

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
HR_RE = re.compile(r"^[ \t]{0,3}([-*_])([ \t]*\1){2,}[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*([A-Za-z0-9_+-]*)[ \t]*$")
LIST_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[-*+]|\d+[.)])[ \t]+(?P<text>.*)$")
TABLE_SEP_RE = re.compile(r"^[ \t]*\|?[ \t]*:?-{1,}:?[ \t]*(\|[ \t]*:?-{1,}:?[ \t]*)*\|?[ \t]*$")
QUOTE_RE = re.compile(r"^[ \t]{0,3}>[ \t]?(.*)$")
TASK_RE = re.compile(r"^\[([ xX])\][ \t]+(.*)$")

# Characters that make a *line start* meaningful in wikitext.
LINE_START_SPECIAL = " *#:;=-"


@dataclass
class ConvertContext:
    """Information the converter needs from the outside."""

    title: str = ""
    # slug -> page title, for relative links such as [x](andere-seite.md)
    internal_pages: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    drop_first_h1: bool = True
    _h1_seen: bool = False


# ---------------------------------------------------------------------------
# Escaping
# ---------------------------------------------------------------------------

def esc(text: str) -> str:
    """Entity-escape everything in plain text that wikitext/HTML could interpret."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("{", "&#123;").replace("}", "&#125;")
    text = text.replace("[", "&#91;").replace("]", "&#93;")
    text = text.replace("|", "&#124;")
    text = text.replace("__", "&#95;&#95;")
    text = text.replace("~~~", "&#126;&#126;&#126;")
    text = re.sub(r"'{2,}", lambda m: "&#39;" * len(m.group()), text)
    return text


def esc_url(url: str) -> str:
    """Make a URL safe inside ``[url text]``."""
    out = []
    for ch in url:
        if ch in " []|<>\"'{}\\^`":
            out.append("%%%02X" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def esc_line_start(line: str) -> str:
    """Neutralise a leading character that would start a list/heading/pre block."""
    if line and line[0] in LINE_START_SPECIAL:
        return f"&#{ord(line[0])};" + line[1:]
    return line


# ---------------------------------------------------------------------------
# Placeholders
# ---------------------------------------------------------------------------

def substitute_placeholders(text: str, values: dict[str, str]) -> tuple[str, list[str]]:
    """Replace ``{{ name }}`` using ``values``. Returns (text, unknown_names).

    Unknown placeholders are left in place (and reported) so the caller can
    refuse to publish: a forgotten ``{{ x }}`` must never reach MediaWiki,
    where it would transclude ``Template:X``.
    """
    unknown: list[str] = []

    def repl(match: re.Match) -> str:
        name = match.group(1)
        if name in values:
            return values[name]
        unknown.append(name)
        return match.group(0)

    return PLACEHOLDER_RE.sub(repl, text), sorted(set(unknown))


# ---------------------------------------------------------------------------
# Inline conversion
# ---------------------------------------------------------------------------

_INLINE = re.compile(
    r"""
      (?P<code>(?P<tick>`+)(?P<codetext>.+?)(?P=tick))
    | (?P<image>!\[(?P<alt>[^\]]*)\]\((?P<imgurl>[^)\s]*)(?:\s+"[^"]*")?\))
    | (?P<link>\[(?P<ltext>[^\]]*)\]\((?P<lurl>[^)\s]*)(?:\s+"[^"]*")?\))
    | (?P<auto><(?P<autourl>https?://[^>\s]+)>)
    | (?P<bold>(?<![\w*])\*\*(?=\S)(?P<boldtext>.+?)(?<=\S)\*\*(?!\*))
    | (?P<bold2>(?<![\w_])__(?=[^\s_])(?P<bold2text>.+?)(?<=[^\s_])__(?![\w_]))
    | (?P<strike>~~(?=\S)(?P<striketext>.+?)(?<=\S)~~)
    | (?P<ital>(?<![\w*])\*(?=[^\s*])(?P<ialtext>.+?)(?<=[^\s*])\*(?![\w*]))
    | (?P<ital2>(?<![\w_])_(?=[^\s_])(?P<ital2text>.+?)(?<=[^\s_])_(?![\w_]))
    """,
    re.VERBOSE,
)


def inline(text: str, ctx: ConvertContext) -> str:
    """Convert inline Markdown to wikitext; plain text is always escaped."""
    out: list[str] = []
    pos = 0
    for m in _INLINE.finditer(text):
        out.append(esc(text[pos:m.start()]))
        pos = m.end()
        if m.group("code"):
            out.append("<code>" + esc(m.group("codetext").strip()) + "</code>")
        elif m.group("image"):
            alt = m.group("alt").strip()
            ctx.warnings.append(f"image '{m.group('imgurl')}' replaced by its alternative text")
            out.append(esc(alt))
        elif m.group("link"):
            out.append(_link(m.group("ltext"), m.group("lurl"), ctx))
        elif m.group("auto"):
            out.append(f"[{esc_url(m.group('autourl'))}]")
        elif m.group("bold") or m.group("bold2"):
            inner = m.group("boldtext") or m.group("bold2text")
            out.append("'''" + inline(inner, ctx) + "'''")
        elif m.group("strike"):
            out.append("<s>" + inline(m.group("striketext"), ctx) + "</s>")
        elif m.group("ital") or m.group("ital2"):
            inner = m.group("ialtext") or m.group("ital2text")
            out.append("''" + inline(inner, ctx) + "''")
    out.append(esc(text[pos:]))
    return "".join(out)


def _link(label: str, url: str, ctx: ConvertContext) -> str:
    rendered = inline(label, ctx) if label else ""
    if SAFE_URL_RE.match(url):
        target = esc_url(url)
        return f"[{target} {rendered}]" if rendered else f"[{target}]"
    base = url.split("#", 1)[0]
    if base.lower().endswith(".md"):
        slug = PurePosixPath(base).stem
        page = ctx.internal_pages.get(slug)
        if page:
            return f"[[{page}|{rendered or esc(page)}]]"
        ctx.warnings.append(f"link to unknown page '{url}' rendered as plain text")
        return rendered
    if url.startswith("#") or not url:
        return rendered
    ctx.warnings.append(f"link with disallowed target '{url[:40]}' rendered as plain text")
    return rendered


# ---------------------------------------------------------------------------
# Block conversion
# ---------------------------------------------------------------------------

def strip_comments(text: str) -> str:
    """Remove HTML comments outside fenced code blocks."""
    out: list[str] = []
    buf: list[str] = []
    fence: str | None = None

    def flush() -> None:
        if buf:
            out.append(HTML_COMMENT_RE.sub("", "\n".join(buf)))
            buf.clear()

    for line in text.split("\n"):
        m = FENCE_RE.match(line)
        if fence is None and m:
            flush()
            fence = m.group(1)[0]
            out.append(line)
        elif fence is not None:
            out.append(line)
            if m and m.group(1)[0] == fence and not m.group(2):
                fence = None
        else:
            buf.append(line)
    flush()
    return "\n".join(out)


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.replace("\\|", "|").strip() for c in cells]


def convert(markdown: str, ctx: ConvertContext | None = None) -> str:
    """Convert Markdown (placeholders already substituted) to wikitext."""
    ctx = ctx or ConvertContext()
    text = strip_comments(markdown.replace("\r\n", "\n").replace("\r", "\n"))
    lines = text.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append("\n".join(esc_line_start(inline(p, ctx)) for p in para))
            out.append("")
            para.clear()

    while i < n:
        line = lines[i]

        if not line.strip():
            flush_para()
            i += 1
            continue

        fence = FENCE_RE.match(line)
        if fence:
            flush_para()
            marker, i = fence.group(1)[0], i + 1
            code: list[str] = []
            while i < n:
                end = FENCE_RE.match(lines[i])
                if end and end.group(1)[0] == marker and not end.group(2):
                    i += 1
                    break
                code.append(lines[i])
                i += 1
            # Defence in depth: <pre> is not parsed, but never rely on a single mechanism.
            body = "\n".join(code).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            for ch, ent in (("{", "&#123;"), ("}", "&#125;"), ("[", "&#91;"), ("]", "&#93;")):
                body = body.replace(ch, ent)
            out += ["<pre>" + body + "</pre>", ""]
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush_para()
            level, title = len(heading.group(1)), heading.group(2).strip()
            if level == 1 and ctx.drop_first_h1 and not ctx._h1_seen:
                ctx._h1_seen = True
            else:
                level = max(level, 2)
                marks = "=" * level
                clean = inline(title, ctx).replace("=", "&#61;")
                out += [f"{marks} {clean} {marks}", ""]
            i += 1
            continue

        if HR_RE.match(line) and not LIST_RE.match(line):
            flush_para()
            out += ["----", ""]
            i += 1
            continue

        if QUOTE_RE.match(line):
            flush_para()
            quote: list[str] = []
            while i < n and QUOTE_RE.match(lines[i]):
                quote.append(QUOTE_RE.match(lines[i]).group(1))
                i += 1
            out += _quote(quote, ctx)
            continue

        if "|" in line and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]:
            flush_para()
            header = split_table_row(line)
            i += 2
            rows: list[list[str]] = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(split_table_row(lines[i]))
                i += 1
            out += _table(header, rows, ctx)
            continue

        if LIST_RE.match(line):
            flush_para()
            block: list[str] = []
            while i < n:
                cur = lines[i]
                if LIST_RE.match(cur):
                    block.append(cur)
                    i += 1
                elif cur.strip() and cur.startswith((" ", "\t")) and block:
                    block[-1] += " " + cur.strip()  # continuation line
                    i += 1
                elif not cur.strip() and i + 1 < n and LIST_RE.match(lines[i + 1]):
                    i += 1  # blank line inside a list
                else:
                    break
            out += _list(block, ctx)
            continue

        para.append(line.strip())
        i += 1

    flush_para()
    return "\n".join(out).strip("\n") + "\n"


def _quote(lines: list[str], ctx: ConvertContext) -> list[str]:
    paragraphs, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            paragraphs.append(" ".join(cur))
            cur = []
    if cur:
        paragraphs.append(" ".join(cur))
    body = "\n\n".join(esc_line_start(inline(p, ctx)) for p in paragraphs)
    return ["<blockquote>", body, "</blockquote>", ""]


def _table(header: list[str], rows: list[list[str]], ctx: ConvertContext) -> list[str]:
    width = len(header)
    out = ['{| class="wikitable"', "|-"]
    for cell in header:
        out.append("! " + (inline(cell, ctx) or "&#32;"))
    for row in rows:
        row = (row + [""] * width)[:width]
        out.append("|-")
        for cell in row:
            out.append("| " + (inline(cell, ctx) or "&#32;"))
    out += ["|}", ""]
    return out


def _list(block: list[str], ctx: ConvertContext) -> list[str]:
    out: list[str] = []
    stack: list[tuple[int, str]] = []  # (indent width, '*' or '#')
    for raw in block:
        m = LIST_RE.match(raw.replace("\t", "    "))
        indent = len(m.group("indent"))
        kind = "#" if m.group("marker")[0].isdigit() else "*"
        while stack and indent < stack[-1][0]:
            stack.pop()
        if not stack or indent > stack[-1][0]:
            stack.append((indent, kind))
        elif stack[-1][1] != kind:
            stack[-1] = (stack[-1][0], kind)
        text = m.group("text")
        task = TASK_RE.match(text)
        prefix = ""
        if task:
            prefix = "&#9746; " if task.group(1) in "xX" else "&#9744; "
            text = task.group(2)
        marks = "".join(k for _, k in stack)
        out.append(f"{marks} {prefix}{inline(text, ctx)}")
    out.append("")
    return out
