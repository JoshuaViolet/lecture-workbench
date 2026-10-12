"""Interface language: the string table, the builder's use of it, and the built page in English."""
import json
import os
import re
import subprocess
import sys

import pytest

from conftest import FRAMEWORK, build_guide

CJK = re.compile(r"[㐀-鿿！-～　-〿]")
# the skeleton with every module from framework/src/ pasted in
TEMPLATE = build_guide.assemble_template()
# the template without HTML, CSS and JS comments
CODE = re.sub(r"(^|\s)//.*", "", re.sub(r"<!--.*?-->|/\*.*?\*/", "", TEMPLATE, flags=re.S))
ENGLISH_CONFIG = {"lang": "en", "title": "Binary search", "sidebar_title": "Binary search", "search_placeholder": "",
                  "header_html": "<header class=\"doc-header\"><h1>Binary search</h1></header>",
                  "nav_html": "<li><a href=\"#bs-overview\">1.0 Overview</a></li>"}


def built(path):
    return open(path, encoding="utf-8").read()


def test_every_language_defines_the_same_strings():
    tables = build_guide.load_ui_strings()
    assert set(tables) == {"zh", "en"}
    assert not [k for k, v in tables["en"].items() if CJK.search(v)]


def test_every_string_is_used_and_every_use_is_defined():
    keys = set(build_guide.load_ui_strings()["zh"])
    builder = open(os.path.join(FRAMEWORK, "build_guide.py"), encoding="utf-8").read()
    used = set(re.findall(r"\{\{UI:(\w+)\}\}|\bUI\.(\w+)|\bt\(\"(\w+)\"", CODE))
    used = {k for group in used for k in group if k} | set(re.findall(r'ui\["(\w+)"\]', builder))
    assert used - keys == set(), "used but not defined"
    assert keys - used == set(), "defined but never used"


def test_template_has_no_hard_coded_chinese():
    assert [ln for ln in CODE.splitlines() if re.search(r"[\u4e00-\u9fff]", ln)] == []


def test_chinese_is_the_default(make_subject):
    out = built(build_guide.build(str(make_subject(config={"search_placeholder": ""}))))
    assert '<html lang="zh-CN"' in out
    assert 'placeholder="🔍 搜索目录…"' in out and ">收起目录<" in out


def test_english_build(make_subject):
    out = built(build_guide.build(str(make_subject(config={"lang": "en", "search_placeholder": ""}))))
    assert '<html lang="en"' in out
    assert 'placeholder="🔍 Search contents…"' in out and ">Hide contents<" in out
    ui = json.loads(re.search(r"^\s*const UI = (\{.*\});$", out, re.M).group(1))
    assert ui == build_guide.load_ui_strings()["en"]


def test_english_build_passes_the_validator(make_subject):
    out = build_guide.build(str(make_subject(config={"lang": "en"})))
    r = subprocess.run([sys.executable, os.path.join(FRAMEWORK, "validate_guide.py"), out],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_unsupported_language_is_rejected(make_subject):
    with pytest.raises(build_guide.BuildError, match=re.escape("config.lang 'fr' is not supported")):
        build_guide.build(str(make_subject(config={"lang": "fr"})))


def test_inconsistent_tables_are_rejected(tmp_path, monkeypatch):
    path = tmp_path / "ui_strings.json"
    path.write_text(json.dumps({"zh": {"a": "{n} 条", "b": "乙"}, "en": {"a": "{count} items", "c": "c"}}),
                    encoding="utf-8")
    monkeypatch.setattr(build_guide, "UI_STRINGS", str(path))
    with pytest.raises(build_guide.BuildError) as e:
        build_guide.load_ui_strings()
    msg = str(e.value)
    assert "ui_strings.en is missing 'b'" in msg
    assert "ui_strings.en.c is not in the 'zh' table" in msg
    assert "ui_strings.en.a must use the same {slots}" in msg


@pytest.fixture
def english_page(browser, make_subject):
    guide = build_guide.build(str(make_subject("english", config=ENGLISH_CONFIG)))
    context = browser.new_context()
    pg = context.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + guide)
    pg.page_errors = errors
    yield pg
    context.close()


def test_english_page_shows_no_chinese_interface_text(english_page):
    page = english_page
    page.click("#flashcard-element")
    page.click(".quiz-toggle >> nth=0")
    page.click("#theme-toggle-btn")
    page.click("#sidebar-toggle-pill")
    page.evaluate("buildPrintSheet()")
    texts = page.evaluate("""() => {
        const main = document.getElementById('main-content');
        const out = [];
        document.querySelectorAll('body *').forEach(el => {
            if (main.contains(el) || el.tagName === 'SCRIPT') return;
            for (const n of el.childNodes) if (n.nodeType === 3) out.push(n.nodeValue);
            for (const a of ['title', 'placeholder', 'aria-label', 'alt']) if (el.hasAttribute(a)) out.push(el.getAttribute(a));
        });
        ['#fc-type', '#fc-sub', '.mcq-explain strong', '.quiz-toggle', '#print-sheet h2', '#print-sheet h3']
            .forEach(s => out.push(document.querySelector(s).textContent));
        return out;
    }""")
    assert [t for t in texts if CJK.search(t)] == []
    assert page.evaluate("document.documentElement.lang") == "en"
    assert page.locator(".quiz-toggle").first.inner_text() == "Hide answer and explanation"
    assert page.page_errors == []


def test_slots_are_filled_literally(english_page):
    assert english_page.evaluate('t("toast_imported", { highlights: 2, notes: 1 })').startswith(
        "📥 Imported 2 highlights and 1 notes")
    assert english_page.evaluate('t("md_title", { title: "a $& {n} b" })') == "a $& {n} b · My notes and highlights"
