"""Tests for scripts/publishing/md2wiki.py — correctness and, above all, safety."""

from __future__ import annotations

import re

import pytest

from conftest import load_script

m2w = load_script("scripts/publishing/md2wiki.py", "md2wiki")


def conv(md: str, **kw) -> str:
    ctx = m2w.ConvertContext(**kw)
    return m2w.convert(md, ctx)


# ---------------------------------------------------------------------------
# Safety: untrusted text must never create wikitext/HTML constructs
# ---------------------------------------------------------------------------

DANGEROUS = [
    "{{Vorlage}}",
    "{{#invoke:Module|fn}}",
    "{{subst:User:Evil}}",
    "[[Category:Gesperrt]]",
    "[[Datei:Evil.svg]]",
    "[[Kategorie:Hack|x]]",
    "~~~~",
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<nowiki>",
    "{| class=\"x\" |- | a |}",
    "<ref>x</ref>",
    "<references/>",
    "<templatestyles src=\"x\"/>",
    "<syntaxhighlight lang=php>x</syntaxhighlight>",
    "<math>x</math>",
    "<noinclude>x</noinclude>",
    "<onlyinclude>x</onlyinclude>",
    "<includeonly>x</includeonly>",
    "&lt;script&gt;",
    "'''fett''' und ''kursiv''",
    "ISBN 123",
]


@pytest.mark.parametrize("payload", DANGEROUS)
def test_plain_text_never_becomes_markup(payload):
    """The converter's own markup uses only ' = * # : ; | and a few tags; none may survive from input."""
    out = conv("Text " + payload + " Ende")
    assert "{{" not in out and "}}" not in out
    assert "[[" not in out and "]]" not in out
    assert "__" not in out
    assert "~~~" not in out
    assert not re.search(r"<(?!/?(?:code|s|pre|blockquote)\b|br\b)", out), out
    assert "'''" not in out and "''" not in out
    assert "{|" not in out


@pytest.mark.parametrize("magic", ["__NOTOC__", "__FORCETOC__", "__TOC__", "__NOEDITSECTION__", "__NOINDEX__"])
def test_magic_words_are_neutralised(magic):
    """In Markdown __x__ is bold; either way no double underscore may reach MediaWiki."""
    for md in (f"Text {magic} Ende", f"- {magic}", f"## {magic}", f"| a |\n|---|\n| {magic} |"):
        assert "__" not in conv(md), md


@pytest.mark.parametrize("payload", ["{{x}}", "[[Category:A]]", "<script>", "__TOC__"])
def test_dangerous_text_inside_constructs_is_escaped(payload):
    for md in (f"# T\n\n## H {payload}\n", f"- item {payload}\n", f"| a | b |\n|---|---|\n| {payload} | x |\n",
               f"> quote {payload}\n", f"**bold {payload}**\n", f"[link {payload}](https://example.org)\n",
               f"`code {payload}`\n"):
        out = conv(md)
        assert "{{" not in out and "[[Cat" not in out and "<script" not in out and "__TOC__" not in out, md


def test_code_fence_content_is_inert():
    out = conv("```\n{{x}} <script>alert(1)</script> </pre><b>\n```\n")
    assert out.count("<pre>") == 1 and out.count("</pre>") == 1
    assert "<script" not in out
    assert "{{" not in out and "[[" not in out        # braces/brackets escaped even inside <pre>
    assert "&#123;&#123;x&#125;&#125;" in out


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,x", "vbscript:x", "file:///etc/passwd",
                                 "//evil.example/x", "JaVaScRiPt:alert(1)"])
def test_unsafe_link_targets_become_plain_text(url):
    ctx = m2w.ConvertContext()
    out = m2w.convert(f"[klick]({url})\n", ctx)
    assert "klick" in out and "javascript" not in out.lower().replace("javascript:", "") or "[" not in out
    assert "[" not in out and "]" not in out
    assert ctx.warnings


def test_url_characters_cannot_break_out_of_the_link():
    out = conv("[x](https://example.org/a|b]c'd\"e)\n")
    assert out.count("[") == 1 and out.count("]") == 1
    assert "|" not in out and "'" not in out and '"' not in out


def test_table_syntax_in_input_cannot_inject_cell_attributes():
    """A multi-line wikitable in the input is just a Markdown table; its cells stay inert."""
    out = conv('Text {| class="x"\n|-\n| a\n|} Ende\n')
    for line in out.splitlines():
        if line.startswith(("! ", "| ")):
            assert "|" not in line[2:], line  # a '|' would split cell attributes from content
    assert "{{" not in out and "&#123;" in out


def test_images_are_replaced_by_alt_text_and_warned():
    ctx = m2w.ConvertContext()
    out = m2w.convert("![Herz](https://example.org/herz.png)\n", ctx)
    assert "Herz" in out and "png" not in out and ctx.warnings


def test_line_start_characters_cannot_create_blocks():
    # a paragraph line starting with ':' or ';' or ' ' must not become an indent/definition/pre
    out = conv("Absatz\n:eingerückt\n;definition\n")
    for line in out.splitlines():
        assert not line.startswith((":", ";", " ", "*", "#")), line


def test_heading_text_cannot_inject_equals():
    out = conv("## A = B\n")
    assert out.strip() == "== A &#61; B =="


# ---------------------------------------------------------------------------
# Placeholders
# ---------------------------------------------------------------------------

def test_known_placeholders_are_substituted_before_conversion():
    text, unknown = m2w.substitute_placeholders("Titel: {{ title }} / {{version}}", {"title": "A", "version": "1.0.0"})
    assert text == "Titel: A / 1.0.0" and unknown == []


def test_unknown_placeholders_are_reported_not_hidden():
    text, unknown = m2w.substitute_placeholders("{{ title }} {{ evil }} {{evil}} {{ other }}", {"title": "A"})
    assert unknown == ["evil", "other"] and "{{ evil }}" in text


def test_substituted_values_are_still_escaped():
    text, _ = m2w.substitute_placeholders("{{ title }}", {"title": "[[Category:X]] {{y}}"})
    out = conv(text)
    assert "[[" not in out and "{{" not in out


# ---------------------------------------------------------------------------
# Correct conversion of the supported subset
# ---------------------------------------------------------------------------

def test_first_h1_is_dropped_because_it_is_the_page_title():
    assert conv("# Titel\n\n## Abschnitt\n\nText\n") == "== Abschnitt ==\n\nText\n"


def test_second_h1_becomes_level_two():
    assert "== Zweite ==" in conv("# Erste\n\n# Zweite\n")


def test_heading_levels():
    out = conv("## A\n\n### B\n\n#### C\n")
    assert "== A ==" in out and "=== B ===" in out and "==== C ====" in out


@pytest.mark.parametrize("md,expected", [
    ("**fett**", "'''fett'''"),
    ("*kursiv*", "''kursiv''"),
    ("_kursiv_", "''kursiv''"),
    ("~~weg~~", "<s>weg</s>"),
    ("`code`", "<code>code</code>"),
    ("**fett *und kursiv***", "'''fett ''und kursiv'''''"),
])
def test_inline_markup(md, expected):
    assert conv(md).strip() == expected


def test_snake_case_and_underscore_lines_are_not_italic():
    out = conv("Datei mein_datei_name.txt\n")
    assert "''" not in out
    assert "&#95;" not in out  # single underscores are fine; only '__' is escaped


def test_external_link():
    assert conv("[PubMed](https://pubmed.ncbi.nlm.nih.gov/1/)").strip() == "[https://pubmed.ncbi.nlm.nih.gov/1/ PubMed]"


def test_internal_markdown_link_resolves_to_wiki_page():
    out = conv("Siehe [Herz](herzinsuffizienz.md#x).", internal_pages={"herzinsuffizienz": "Herzinsuffizienz"})
    assert "[[Herzinsuffizienz|Herz]]" in out


def test_unknown_internal_link_is_text_with_warning():
    ctx = m2w.ConvertContext()
    out = m2w.convert("[Weg](gibt-es-nicht.md)", ctx)
    assert "[" not in out and ctx.warnings


def test_lists_nested_and_ordered():
    md = "- a\n  - b\n    - c\n- d\n\n1. eins\n2. zwei\n   - sub\n"
    out = conv(md).splitlines()
    assert out[:4] == ["* a", "** b", "*** c", "* d"]
    assert "# eins" in out and "# zwei" in out and "#* sub" in out


def test_task_list_items():
    out = conv("- [ ] offen\n- [x] erledigt\n")
    assert "&#9744; offen" in out and "&#9746; erledigt" in out


def test_table():
    out = conv("| A | B |\n|---|---|\n| 1 | **2** |\n| 3 |\n")
    assert out.startswith('{| class="wikitable"')
    assert "! A" in out and "! B" in out and "| '''2'''" in out
    assert out.count("|-") == 3 and out.strip().endswith("|}")


def test_table_cell_with_pipe_and_empty_cells():
    out = conv("| A | B |\n|---|---|\n| a\\|b |  |\n")
    assert "a&#124;b" in out and "| &#32;" in out


def test_blockquote():
    out = conv("> Zeile eins\n> Zeile zwei\n")
    assert out.startswith("<blockquote>") and "Zeile eins Zeile zwei" in out


def test_horizontal_rule_and_code_block():
    out = conv("a\n\n---\n\n```python\nx = 1 < 2\n```\n")
    assert "----" in out and "<pre>x = 1 &lt; 2</pre>" in out


def test_html_comments_are_removed_but_not_inside_code():
    out = conv("Text <!-- weg -->\n\n<!--\nmehrzeilig\n-->\n\n```\n<!-- bleibt -->\n```\n")
    assert "weg" not in out and "mehrzeilig" not in out and "bleibt" in out


def test_conversion_is_deterministic():
    md = "# T\n\n## A\n\n- x\n- y\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
    assert conv(md) == conv(md)


def test_empty_input():
    assert conv("") == "\n"


def test_every_template_body_converts_without_markup_leaks(tmp_path):
    """The real templates (after placeholder substitution) convert cleanly."""
    from conftest import REPO
    for path in sorted((REPO / "content" / "templates").glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        body = text[text.index("\n---\n", 4) + 5:]
        body, unknown = m2w.substitute_placeholders(body, {k: f"<{k}>" for k in
            ["title", "specialty", "status", "version", "updated", "license", "procedure", "parent_slug",
             "qr_media_url", "clinic_name", "clinic_address", "clinic_phone"]})
        assert not unknown, (path.name, unknown)
        out = m2w.convert(body)
        assert "{{" not in out and "[[" not in out and "<script" not in out and "__" not in out, path.name
        assert out.count("{|") == out.count("|}"), path.name
