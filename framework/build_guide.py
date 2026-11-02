#!/usr/bin/env python3
"""
build_guide.py: build a single-file, offline study guide from a subject folder.

Usage:
    python3 framework/build_guide.py <subject_dir> [--validate [--strict]]
    python3 framework/build_guide.py --all [--validate [--strict]]     every subject under subjects/

Input:   framework/template.html      page skeleton; pulls in framework/src/css/*.css and src/js/*.js
         framework/ui_strings.json     interface strings, one table per language
         <subject_dir>/config.json     identity, titles, header/nav HTML, output file name
         <subject_dir>/content.html    the lesson body
         <subject_dir>/data.json       flashcards, mcqData, termLexicon
         <subject_dir>/subject_css.css, subject_js.js   (optional)
         images the lesson references, e.g. <subject_dir>/assets/*.png
Output:  <subject_dir>/<config.output>, one file that needs nothing else

The engine's CSS and JS live in modules under framework/src/. Each module is pasted
in place of its @@INCLUDE:...@@ marker in template.html, indented to match the marker,
so the result is still one self-contained file. Local images (<img src> in the HTML,
url() in subject_css.css) are embedded as data: URIs for the same reason, unless
config.embed_images is false.

The template is then filled in two passes. Placeholders ({{NAME}}, and {{UI:key}} for interface
strings in the subject's language) are replaced first, each escaped for where it appears;
then zones (@@ZONE:...@@) are filled. Each pass is a single regex pass, so text inserted
from config.json, content.html or data.json is never re-read as a marker.
"""
import base64
import html
import json
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODULE_EXTS = (".css", ".js")
INCLUDE_RE = re.compile(r"^([ \t]*)(?:/\* @@INCLUDE:([\w./-]+)@@ \*/|// @@INCLUDE:([\w./-]+)@@)[ \t]*$", re.M)
HOLE_RE = re.compile(r"@@(?:INCLUDE|ZONE):|\{\{[A-Z_]+\}\}")

DATA_ARRAYS = ("flashcards", "mcqData", "termLexicon")
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
OUTPUT_RE = re.compile(r"^[A-Za-z0-9_.-]+\.html$")
UI_STRINGS = os.path.join(HERE, "ui_strings.json")
DEFAULT_LANG = "zh"
UI_SLOT_RE = re.compile(r"\{(\w+)\}")

CONFIG_FIELDS = {
    # name: (required, type, description)
    "doc_id": (True, str, "storage namespace; letters, digits, '_' or '-'; never change once published"),
    "app_id": (True, str, "fingerprint written into exported backups"),
    "title": (True, str, "browser tab title"),
    "output": (True, str, "generated file name, e.g. My_Guide.html"),
    "lang": (False, str, "interface language, 'zh' (default) or 'en'"),
    "sidebar_title": (False, str, "sidebar heading (defaults to title)"),
    "sidebar_meta": (False, str, "small text under the sidebar heading"),
    "search_placeholder": (False, str, "placeholder of the sidebar search box"),
    "header_html": (False, str, "raw HTML inserted at the top of <main>"),
    "nav_html": (False, str, "raw <li> items for the sidebar table of contents"),
    "embed_images": (False, bool, "put local images inside the page so it stays one file (default true)"),
}

# Image types browsers display, by extension; these are the files embedding accepts.
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".webp": "image/webp", ".avif": "image/avif", ".svg": "image/svg+xml", ".bmp": "image/bmp",
               ".ico": "image/x-icon"}
# Where an <img> in raw HTML is not really an image: comments, and elements whose content is raw text.
NOT_MARKUP_RE = re.compile(r"<!--.*?-->|<(script|style|textarea)\b.*?</\1\s*>", re.S | re.I)
IMG_TAG_RE = re.compile(r"""<img\b(?:[^>"']|"[^"]*"|'[^']*')*>""", re.I)
SRC_ATTR_RE = re.compile(r"""(?<![\w-])(src\s*=\s*)(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)"'\s]+))\s*\)""", re.I)
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")   # C:\slides\s1.png is a Windows path, not a URL scheme
# Above this size a guide still works, but phones open it slowly.
LARGE_GUIDE_BYTES = 25 * 1024 * 1024

# field: (type, required)
SCHEMA = {
    "flashcards": {"front": (str, True), "back": (str, True), "type": (str, False)},
    "mcqData": {"q": (str, True), "opts": (list, True), "ans": (int, True), "exp": (str, True),
                "code": (str, False), "fig": (str, False), "fig_alt": (str, False), "shuffle": (bool, False)},
    "termLexicon": {"keys": (list, True), "term": (str, True), "ipa": (str, False),
                    "chunks": (str, False), "parts": (str, False), "hook": (str, False)},
}


class BuildError(Exception):
    pass


def read(path):
    """A source file's text, with newlines as "\\n". A UTF-8 byte-order mark (some Windows editors
    write one) is dropped; a file in another encoding (GBK, say) is a BuildError saying where."""
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        line = data.count(b"\n", 0, e.start) + 1
        raise BuildError(f"{os.path.basename(path)} is not UTF-8 text (line {line} has bytes that are not "
                         "UTF-8); save it as UTF-8 in your editor")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def js_literal(value):
    """JSON is valid JS; additionally keep '</script>' and '<!--' from closing the script element."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def load_ui_strings():
    """Return {lang: {key: text}}. Every language must define the same keys with the same {slots}."""
    try:
        tables = json.loads(read(UI_STRINGS))
    except (OSError, json.JSONDecodeError) as e:
        raise BuildError(f"cannot read {os.path.relpath(UI_STRINGS, ROOT)}: {e}")
    base = tables.get(DEFAULT_LANG)
    if not isinstance(base, dict):
        raise BuildError(f"ui_strings.json has no {DEFAULT_LANG!r} table")
    errors = []
    for lang, table in sorted(tables.items()):
        if not isinstance(table, dict) or not all(isinstance(v, str) for v in table.values()):
            errors.append(f"ui_strings.{lang} must map keys to strings")
            continue
        for key in sorted(set(base) - set(table)):
            errors.append(f"ui_strings.{lang} is missing {key!r}")
        for key in sorted(set(table) - set(base)):
            errors.append(f"ui_strings.{lang}.{key} is not in the {DEFAULT_LANG!r} table")
        for key in sorted(set(base) & set(table)):
            if set(UI_SLOT_RE.findall(table[key])) != set(UI_SLOT_RE.findall(base[key])):
                errors.append(f"ui_strings.{lang}.{key} must use the same {{slots}} as {DEFAULT_LANG!r}")
    if errors:
        raise BuildError("\n".join(errors))
    return tables


def check_config(cfg, languages=(DEFAULT_LANG,)):
    errors, warnings = [], []
    if not isinstance(cfg, dict):
        raise BuildError("config.json must contain a JSON object")
    for name, (required, typ, desc) in CONFIG_FIELDS.items():
        if required and not cfg.get(name):
            errors.append(f"config.{name} is required ({desc})")
        elif name in cfg and not isinstance(cfg[name], typ):
            errors.append(f"config.{name} must be " + ("true or false" if typ is bool else "a string"))
    for name in ("doc_id", "app_id"):
        if isinstance(cfg.get(name), str) and cfg[name] and not ID_RE.match(cfg[name]):
            errors.append(f"config.{name} {cfg[name]!r} may only contain letters, digits, '_' and '-'")
    out = cfg.get("output")
    if isinstance(out, str) and out and (not OUTPUT_RE.match(out) or out == "content.html"):
        errors.append(f"config.output {out!r} must be a plain *.html file name other than content.html")
    lang = cfg.get("lang")
    if isinstance(lang, str) and lang not in languages:
        errors.append(f"config.lang {lang!r} is not supported (expected one of {', '.join(sorted(languages))})")
    for name in sorted(set(cfg) - set(CONFIG_FIELDS)):
        warnings.append(f"config.{name} is not used by the framework and is ignored")
    return errors, warnings


def check_data(data):
    errors = []
    if not isinstance(data, dict):
        return ["data.json must contain a JSON object"]
    for name in sorted(set(data) - set(DATA_ARRAYS)):
        errors.append(f"data.{name} is not a known array (expected {', '.join(DATA_ARRAYS)})")
    for name in DATA_ARRAYS:
        items = data.get(name, [])
        if not isinstance(items, list):
            errors.append(f"data.{name} must be an array")
            continue
        fields = SCHEMA[name]
        for i, item in enumerate(items):
            where = f"{name}[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{where} must be an object")
                continue
            for field in sorted(set(item) - set(fields)):
                errors.append(f"{where}.{field} is not a known field (expected {', '.join(fields)})")
            for field, (typ, required) in fields.items():
                if field not in item:
                    if required:
                        errors.append(f"{where}.{field} is missing")
                    continue
                value = item[field]
                if (typ is int and isinstance(value, bool)) or not isinstance(value, typ):
                    errors.append(f"{where}.{field} must be {typ.__name__}")
                elif typ is str and required and not value.strip():
                    errors.append(f"{where}.{field} must not be empty")
            if name == "mcqData" and isinstance(item.get("opts"), list):
                opts = item["opts"]
                if len(opts) < 2 or not all(isinstance(o, str) and o.strip() for o in opts):
                    errors.append(f"{where}.opts must have at least 2 non-empty strings")
                ans = item.get("ans")
                if isinstance(ans, int) and not isinstance(ans, bool) and not 0 <= ans < len(opts):
                    errors.append(f"{where}.ans {ans} is out of range for {len(opts)} options")
            if name == "mcqData" and isinstance(item.get("fig"), str):
                # the figure is shown with the question, so it needs a text alternative like any figure
                if not item["fig"].strip():
                    errors.append(f"{where}.fig must be the path of an image file, e.g. assets/q1.svg")
                elif not (isinstance(item.get("fig_alt"), str) and item["fig_alt"].strip()):
                    errors.append(f"{where}.fig_alt is missing: describe what the figure shows")
            if name == "termLexicon" and isinstance(item.get("keys"), list):
                if not item["keys"] or not all(isinstance(k, str) and k.strip() for k in item["keys"]):
                    errors.append(f"{where}.keys must be a non-empty list of strings")
    return errors


def local_path(ref, base_dir):
    """The file on disk a URL in the page points to, or None if it is not a local file
    (data:, http:, //host, #fragment, ...). Relative URLs resolve against base_dir."""
    ref = html.unescape(ref).strip()
    if not ref or ref.startswith(("#", "//")):
        return None
    if DRIVE_RE.match(ref):
        return os.path.normpath(ref)
    if SCHEME_RE.match(ref):
        return url2pathname(urlsplit(ref).path) if ref[:5].lower() == "file:" else None
    return os.path.normpath(os.path.join(base_dir, unquote(urlsplit(ref).path)))


class ImageEmbedder:
    """Replaces references to local image files with data: URIs, collecting every problem."""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.errors = []
        self.cache = {}

    def uri(self, ref, where):
        path = local_path(ref, self.base_dir)
        if path is None:
            return None
        if path not in self.cache:
            mime = IMAGE_TYPES.get(os.path.splitext(path)[1].lower())
            if not mime:
                self.errors.append(f"{where}: cannot embed {ref!r}: not an image type browsers show "
                                   f"({', '.join(sorted(IMAGE_TYPES))})")
                return None
            try:
                with open(path, "rb") as f:
                    self.cache[path] = f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")
            except OSError:
                self.errors.append(f"{where}: image {ref!r} not found (looked for {path})")
                return None
        return self.cache[path]

    def html(self, text, where):
        """<img src> outside comments, <script>, <style> and <textarea>."""
        def img(m):
            def attr(a):
                uri = self.uri(next(g for g in a.groups()[1:] if g is not None), where)
                return a.group(0) if uri is None else f'{a.group(1)}"{uri}"'
            return SRC_ATTR_RE.sub(attr, m.group(0), count=1)

        out, pos = [], 0
        for skip in NOT_MARKUP_RE.finditer(text):
            out += [IMG_TAG_RE.sub(img, text[pos:skip.start()]), skip.group(0)]
            pos = skip.end()
        out.append(IMG_TAG_RE.sub(img, text[pos:]))
        return "".join(out)

    def css(self, text, where):
        def url(m):
            uri = self.uri(next(g for g in m.groups() if g is not None), where)
            return m.group(0) if uri is None else f'url("{uri}")'
        return CSS_URL_RE.sub(url, text)


def human_size(n):
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{max(1, round(n / 1024))} KB"


def assemble_template(framework_dir=HERE):
    """Return template.html with every @@INCLUDE@@ marker replaced by its module from src/.

    Each module line is indented like its marker. Every module under src/ must be included
    exactly once, and modules hold no markers of their own: all holes stay in template.html.
    """
    src = os.path.join(framework_dir, "src")
    tpl = read(os.path.join(framework_dir, "template.html"))
    errors, used = [], []

    def include(m):
        indent, name = m.group(1), m.group(2) or m.group(3)
        path = os.path.normpath(os.path.join(src, name))
        if not name.endswith(MODULE_EXTS) or not path.startswith(src + os.sep) or not os.path.isfile(path):
            errors.append(f"template.html includes {name}, which is not a .css or .js file under src/")
            return ""
        if name in used:
            errors.append(f"template.html includes {name} more than once")
        used.append(name)
        text = read(path)
        if HOLE_RE.search(text):
            errors.append(f"src/{name} contains a marker or placeholder; keep those in template.html")
        return "\n".join(indent + line if line else line for line in text.rstrip("\n").split("\n"))

    tpl = INCLUDE_RE.sub(include, tpl)
    for dirpath, _, filenames in os.walk(src):
        for f in sorted(filenames):
            name = os.path.relpath(os.path.join(dirpath, f), src).replace(os.sep, "/")
            if f.endswith(MODULE_EXTS) and name not in used:
                errors.append(f"src/{name} is not included by template.html")
    if "@@INCLUDE:" in tpl:
        errors.append("template.html has an @@INCLUDE@@ marker that is not on a line of its own")
    if errors:
        raise BuildError("\n".join(errors))
    return tpl


def build(subject_dir):
    """Build one subject and return the output path. Raises BuildError listing every problem found."""
    subject_dir = os.path.abspath(subject_dir)
    tpl = assemble_template()
    ui_tables = load_ui_strings()

    try:
        cfg = json.loads(read(os.path.join(subject_dir, "config.json")))
    except FileNotFoundError:
        raise BuildError("missing config.json")
    except json.JSONDecodeError as e:
        raise BuildError(f"config.json is not valid JSON: {e}")
    errors, warnings = check_config(cfg, tuple(ui_tables))

    data_path = os.path.join(subject_dir, "data.json")
    data = {}  # a guide without practice widgets is allowed
    if os.path.exists(data_path):
        try:
            data = json.loads(read(data_path))
        except json.JSONDecodeError as e:
            raise BuildError(f"data.json is not valid JSON: {e}")
        errors += check_data(data)
    elif os.path.exists(os.path.join(subject_dir, "data.js")):
        errors.append("data.js is no longer read; convert it with framework/migrate_datajs.py")

    if not os.path.exists(os.path.join(subject_dir, "content.html")):
        errors.append("missing content.html")
    if errors:
        raise BuildError("\n".join(errors))
    for w in warnings:
        print(f"  warning: {w}")

    # --- pass 1: placeholders, escaped for their context ---
    # Interface strings go first, so text from config.json is never read as a {{UI:key}}.
    ui = ui_tables[cfg.get("lang") or DEFAULT_LANG]
    unknown = sorted({k for k in re.findall(r"\{\{UI:(\w+)\}\}", tpl) if k not in ui})
    if unknown:
        raise BuildError(f"template.html uses interface strings missing from ui_strings.json: {unknown}")
    tpl = re.sub(r"\{\{UI:(\w+)\}\}", lambda m: html.escape(ui[m.group(1)], quote=True), tpl)

    title = cfg["title"]
    sidebar_title = cfg.get("sidebar_title") or title
    placeholders = {
        "{{TITLE}}": html.escape(title, quote=False),
        "{{SIDEBAR_TITLE}}": html.escape(sidebar_title, quote=False),
        "{{SIDEBAR_META}}": html.escape(cfg.get("sidebar_meta", ""), quote=False),
        "{{SEARCH_PLACEHOLDER}}": html.escape(cfg.get("search_placeholder") or ui["search_placeholder"], quote=True),
        "{{DOC_ID_JSON}}": js_literal(cfg["doc_id"]),
        "{{APP_ID_JSON}}": js_literal(cfg["app_id"]),
        "{{GUIDE_TITLE_JSON}}": js_literal(sidebar_title),
        "{{UI_STRINGS_JSON}}": js_literal(ui),
    }
    found = set(re.findall(r"\{\{[A-Z_]+\}\}", tpl))
    if found != set(placeholders):
        missing, extra = sorted(set(placeholders) - found), sorted(found - set(placeholders))
        raise BuildError("template.html placeholders do not match the builder's: "
                         + "; ".join(([f"missing {missing}"] if missing else [])
                                     + ([f"not filled by the builder {extra}"] if extra else [])))
    # one pass, so a config value that happens to contain {{NAME}} is inserted as it is
    tpl = re.sub(r"\{\{[A-Z_]+\}\}", lambda m: placeholders[m.group(0)], tpl)

    # --- pass 2: zones, filled in one pass so inserted text is never rescanned ---
    def optional_file(name):
        path = os.path.join(subject_dir, name)
        return read(path).strip("\n") if os.path.exists(path) else ""

    zones = {
        "HEADER": cfg.get("header_html", ""),
        "NAV": cfg.get("nav_html", ""),
        "CONTENT": read(os.path.join(subject_dir, "content.html")),
        "EXTRA_CSS": optional_file("subject_css.css"),
        "EXTRA_JS": optional_file("subject_js.js"),
    }
    if cfg.get("embed_images", True):
        # local images go inside the page, so the guide still works when it is the only file copied
        embed = ImageEmbedder(subject_dir)
        for zone, where in (("HEADER", "config.header_html"), ("NAV", "config.nav_html"),
                            ("CONTENT", "content.html")):
            zones[zone] = embed.html(zones[zone], where)
        zones["EXTRA_CSS"] = embed.css(zones["EXTRA_CSS"], "subject_css.css")
        # HTML fields of the data arrays are inserted with innerHTML at runtime
        for name, fields in (("mcqData", ("exp",)), ("termLexicon", ("parts",))):
            for i, item in enumerate(data.get(name, [])):
                for field in fields:
                    if isinstance(item.get(field), str):
                        item[field] = embed.html(item[field], f"{name}[{i}].{field}")
        # a question's figure is a path, not HTML
        for i, item in enumerate(data.get("mcqData", [])):
            if isinstance(item.get("fig"), str):
                item["fig"] = embed.uri(item["fig"], f"mcqData[{i}].fig") or item["fig"]
        if embed.errors:
            raise BuildError("\n".join(embed.errors))
    for name in DATA_ARRAYS:
        zones["DATA:" + name] = f"const {name} = {js_literal(data.get(name, []))};"

    zone_re = re.compile(r"<!-- @@ZONE:([\w:]+)@@ -->|/\* @@ZONE:([\w:]+)@@ \*/|// @@ZONE:([\w:]+)@@")
    found = [next(g for g in m.groups() if g) for m in zone_re.finditer(tpl)]
    if sorted(found) != sorted(zones):
        raise BuildError(f"template zones {sorted(found)} do not match the builder's {sorted(zones)}")
    tpl = zone_re.sub(lambda m: zones[next(g for g in m.groups() if g)], tpl)

    out_path = os.path.join(subject_dir, cfg["output"])
    header = "<!-- GENERATED by lecture-workbench build_guide.py; edit the subject sources and rebuild -->\n"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header + tpl)
    except OSError as e:   # e.g. the file is open in a program that locks it, or the folder is read-only
        raise BuildError(f"cannot write {cfg['output']}: {e.strerror or e}")
    return out_path


def find_subject_dirs(subjects_root):
    found = []
    for dirpath, dirnames, filenames in os.walk(subjects_root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith((".", "_")))
        if "config.json" in filenames:
            found.append(dirpath)
    return sorted(found)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    paths = [a for a in argv if not a.startswith("--")]
    unknown = [a for a in argv if a.startswith("--") and a not in ("--all", "--validate", "--strict")]
    if unknown:
        print(f"unknown option {unknown[0]}\n" + __doc__.strip().split("\n\n")[1])
        return 2
    if "--all" in argv:
        subjects = find_subject_dirs(os.path.join(ROOT, "subjects"))
        if not subjects:
            print("no subjects (folders with config.json) under subjects/")
            return 1
    elif paths:
        subjects = paths
    else:
        print(__doc__.strip().split("\n\n")[1])
        return 2
    return build_many(subjects, validate="--validate" in argv, strict="--strict" in argv)


def build_many(subjects, validate=False, strict=False):
    """Build every subject, validating each output if asked; keep going after a failure. Returns an exit code."""
    failed = []
    for subject in subjects:
        label = os.path.relpath(os.path.abspath(subject), os.getcwd())
        try:
            out = build(subject)
        except BuildError as e:
            print(f"BUILD FAILED  {label}\n  " + str(e).replace("\n", "\n  "), flush=True)
            failed.append(label)
            continue
        size = os.path.getsize(out)
        print(f"BUILD OK      {label} -> {os.path.basename(out)} ({human_size(size)})", flush=True)
        if size > LARGE_GUIDE_BYTES:
            print(f"  warning: the guide is {human_size(size)}; phones open files this large slowly "
                  "(shrink or compress the images, e.g. JPEG or WebP for photos and slides)", flush=True)
        if validate:
            r = subprocess.run([sys.executable, os.path.join(HERE, "validate_guide.py"), out]
                               + (["--strict"] if strict else []))
            if r.returncode != 0:
                failed.append(label)

    if len(subjects) > 1:
        print(f"\n{len(subjects) - len(failed)}/{len(subjects)} subjects OK"
              + ("" if not failed else "; failed: " + ", ".join(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
