"""Shared pytest helpers for the Wikimedica script tests.

The scripts use hyphenated file names (validate-metadata.py), so they cannot be
imported with a plain `import`; `load_script` loads them by path instead.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "articles"
SCHEMA_PATH = REPO / "data" / "metadata" / "article-schema.yaml"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "publishing"))

DELETE = object()  # sentinel: remove a key from the frontmatter


def load_script(relative: str, name: str):
    """Import a script from a path relative to the repository root."""
    path = REPO / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="session")
def vm():
    return load_script("scripts/validation/validate-metadata.py", "validate_metadata")


@pytest.fixture(scope="session")
def schema(vm):
    return vm.load_schema(SCHEMA_PATH)


def read_fixture(name: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body) of a fixture article."""
    text = (FIXTURES / name).read_text(encoding="utf-8")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end]), text[end + 5:]


def render(fm: dict, body: str) -> str:
    dumped = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    return f"---\n{dumped}---\n{body}"


@pytest.fixture
def check(tmp_path, vm, schema):
    """check(fixture, body=None, filename=None, **changes) -> validated Article.

    Starts from a known-good fixture, applies `changes` (DELETE removes a key)
    and validates the result, so every test isolates exactly one rule.
    """

    def _check(fixture: str, body: str | None = None, filename: str | None = None, **changes):
        fm, fixture_body = read_fixture(fixture)
        for key, value in changes.items():
            if value is DELETE:
                fm.pop(key, None)
            else:
                fm[key] = value
        path = tmp_path / (filename or f"{fm.get('slug', 'x')}.md")
        path.write_text(render(fm, fixture_body if body is None else body), encoding="utf-8")
        article = vm.parse_article(path)
        vm.validate_article(article, schema)
        return article

    return _check


def has(article, field: str, text: str, level: str = "ERROR") -> bool:
    """True if a finding of `level` exists for `field` containing `text`."""
    return any(
        f.field.startswith(field) and f.level == level and text.lower() in f.message.lower()
        for f in article.findings
    )
