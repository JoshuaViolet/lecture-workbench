import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMEWORK = os.path.join(ROOT, "framework")
DEMO = os.path.join(ROOT, "subjects", "demo-binary-search")
sys.path.insert(0, FRAMEWORK)

import build_guide  # noqa: E402


@pytest.fixture
def make_subject(tmp_path):
    """Copy the demo subject into a temp dir, optionally overriding config/data/content."""

    def make(name="subject", config=None, data=None, content=None):
        dst = tmp_path / name
        shutil.copytree(DEMO, dst, ignore=shutil.ignore_patterns("*.html"))
        shutil.copy(os.path.join(DEMO, "content.html"), dst / "content.html")
        cfg = json.loads((dst / "config.json").read_text(encoding="utf-8"))
        if content is not None:
            cfg["nav_html"] = ""  # the demo's table of contents points into the demo content
        cfg.update(config or {})
        (dst / "config.json").write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        if data is not None:
            (dst / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        if content is not None:
            (dst / "content.html").write_text(content, encoding="utf-8")
        return dst

    return make


@pytest.fixture(scope="session")
def demo_guide(tmp_path_factory):
    """Build the demo once per test session and return the path of the generated HTML."""
    dst = tmp_path_factory.mktemp("demo") / "demo-binary-search"
    shutil.copytree(DEMO, dst, ignore=shutil.ignore_patterns("*_Demo.html"))
    return build_guide.build(str(dst))


@pytest.fixture(scope="session")
def browser():
    sync_api = pytest.importorskip("playwright.sync_api")
    # PW_CHANNEL=chrome uses an installed Google Chrome instead of Playwright's bundled Chromium.
    channel = os.environ.get("PW_CHANNEL") or None
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch(channel=channel)
        yield b
        b.close()


@pytest.fixture
def page(browser, demo_guide):
    """A fresh browser context (so localStorage starts empty) with the demo guide loaded."""
    context = browser.new_context(accept_downloads=True)
    pg = context.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + demo_guide)
    pg.page_errors = errors
    yield pg
    context.close()
