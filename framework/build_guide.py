#!/usr/bin/env python3
"""
build_guide.py: build a single-file, offline study guide from a subject folder.

Usage:
    python3 framework/build_guide.py <subject_dir> [--validate]
    python3 framework/build_guide.py --all [--validate]     every subject under subjects/

Input:   framework/template.html
         <subject_dir>/config.json     identity, titles, header/nav HTML, output file name
         <subject_dir>/content.html    the lesson body
         <subject_dir>/data.json       flashcards, mcqData, termLexicon
         <subject_dir>/subject_css.css, subject_js.js   (optional)
Output:  <subject_dir>/<config.output>

The template is filled in two passes. Placeholders ({{NAME}}) are replaced first,
each escaped for where it appears; then zones (@@ZONE:...@@) are filled in a single
regex pass, so text inside content.html or data.json is never re-read as a marker.
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DATA_ARRAYS = ("flashcards", "mcqData", "termLexicon")
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
OUTPUT_RE = re.compile(r"^[A-Za-z0-9_.-]+\.html$")

CONFIG_FIELDS = {
    # name: (required, description)
    "doc_id": (True, "storage namespace; letters, digits, '_' or '-'; never change once published"),
    "app_id": (True, "fingerprint written into exported backups"),
    "title": (True, "browser tab title"),
    "output": (True, "generated file name, e.g. My_Guide.html"),
    "sidebar_title": (False, "sidebar heading (defaults to title)"),
    "sidebar_meta": (False, "small text under the sidebar heading"),
    "search_placeholder": (False, "placeholder of the sidebar search box"),
    "header_html": (False, "raw HTML inserted at the top of <main>"),
    "nav_html": (False, "raw <li> items for the sidebar table of contents"),
}

# field: (type, required)
SCHEMA = {
    "flashcards": {"front": (str, True), "back": (str, True), "type": (str, False)},
    "mcqData": {"q": (str, True), "opts": (list, True), "ans": (int, True), "exp": (str, True),
                "shuffle": (bool, False)},
    "termLexicon": {"keys": (list, True), "term": (str, True), "ipa": (str, False),
                    "chunks": (str, False), "parts": (str, False), "hook": (str, False)},
}


class BuildError(Exception):
    pass


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def js_literal(value):
    """JSON is valid JS; additionally keep '</script>' and '<!--' from closing the script element."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def check_config(cfg):
    errors, warnings = [], []
    if not isinstance(cfg, dict):
        raise BuildError("config.json must contain a JSON object")
    for name, (required, desc) in CONFIG_FIELDS.items():
        if required and not cfg.get(name):
            errors.append(f"config.{name} is required ({desc})")
        elif name in cfg and not isinstance(cfg[name], str):
            errors.append(f"config.{name} must be a string")
    for name in ("doc_id", "app_id"):
        if isinstance(cfg.get(name), str) and cfg[name] and not ID_RE.match(cfg[name]):
            errors.append(f"config.{name} {cfg[name]!r} may only contain letters, digits, '_' and '-'")
    out = cfg.get("output")
    if isinstance(out, str) and out and (not OUTPUT_RE.match(out) or out == "content.html"):
        errors.append(f"config.output {out!r} must be a plain *.html file name other than content.html")
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
            if name == "termLexicon" and isinstance(item.get("keys"), list):
                if not item["keys"] or not all(isinstance(k, str) and k.strip() for k in item["keys"]):
                    errors.append(f"{where}.keys must be a non-empty list of strings")
    return errors


def build(subject_dir):
    """Build one subject and return the output path. Raises BuildError listing every problem found."""
    subject_dir = os.path.abspath(subject_dir)
    tpl = read(os.path.join(HERE, "template.html"))

    try:
        cfg = json.loads(read(os.path.join(subject_dir, "config.json")))
    except FileNotFoundError:
        raise BuildError("missing config.json")
    except json.JSONDecodeError as e:
        raise BuildError(f"config.json is not valid JSON: {e}")
    errors, warnings = check_config(cfg)

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
    title = cfg["title"]
    sidebar_title = cfg.get("sidebar_title") or title
    placeholders = {
        "{{TITLE}}": html.escape(title, quote=False),
        "{{SIDEBAR_TITLE}}": html.escape(sidebar_title, quote=False),
        "{{SIDEBAR_META}}": html.escape(cfg.get("sidebar_meta", ""), quote=False),
        "{{SEARCH_PLACEHOLDER}}": html.escape(cfg.get("search_placeholder") or "🔍 搜索目录…", quote=True),
        "{{DOC_ID_JSON}}": js_literal(cfg["doc_id"]),
        "{{APP_ID_JSON}}": js_literal(cfg["app_id"]),
        "{{GUIDE_TITLE_JSON}}": js_literal(sidebar_title),
    }
    for token, value in placeholders.items():
        if token not in tpl:
            raise BuildError(f"template.html is missing placeholder {token}")
        tpl = tpl.replace(token, value)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    if leftover:
        raise BuildError(f"template.html has placeholders the builder does not fill: {sorted(set(leftover))}")

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
    for name in DATA_ARRAYS:
        zones["DATA:" + name] = f"const {name} = {js_literal(data.get(name, []))};"

    zone_re = re.compile(r"<!-- @@ZONE:([\w:]+)@@ -->|/\* @@ZONE:([\w:]+)@@ \*/|// @@ZONE:([\w:]+)@@")
    found = [next(g for g in m.groups() if g) for m in zone_re.finditer(tpl)]
    if sorted(found) != sorted(zones):
        raise BuildError(f"template zones {sorted(found)} do not match the builder's {sorted(zones)}")
    tpl = zone_re.sub(lambda m: zones[next(g for g in m.groups() if g)], tpl)

    out_path = os.path.join(subject_dir, cfg["output"])
    header = "<!-- GENERATED by lecture-workbench build_guide.py; edit the subject sources and rebuild -->\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + tpl)
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
    do_validate = "--validate" in argv
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

    failed = []
    for subject in subjects:
        label = os.path.relpath(os.path.abspath(subject), os.getcwd())
        try:
            out = build(subject)
        except BuildError as e:
            print(f"BUILD FAILED  {label}\n  " + str(e).replace("\n", "\n  "), flush=True)
            failed.append(label)
            continue
        print(f"BUILD OK      {label} -> {os.path.basename(out)}", flush=True)
        if do_validate:
            r = subprocess.run([sys.executable, os.path.join(HERE, "validate_guide.py"), out])
            if r.returncode != 0:
                failed.append(label)

    if len(subjects) > 1:
        print(f"\n{len(subjects) - len(failed)}/{len(subjects)} subjects OK"
              + ("" if not failed else "; failed: " + ", ".join(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
