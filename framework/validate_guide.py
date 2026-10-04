#!/usr/bin/env python3
"""
validate_guide.py: check a generated study guide.

Usage:
    python3 framework/validate_guide.py <guide.html> [--strict]

Checks (any failure exits 1):
  structure   anchors resolve, getElementById targets exist, inline handlers are defined,
              tags are balanced, no unfilled placeholders, every <script> passes `node --check`
  content     no raw LaTeX (the page has no math renderer), every assets/ image exists,
              every English term in span.en / <strong> has a term card (or is allow-listed)
Teaching-quality lint (warnings; failures with --strict):
              the correct option is the longest one too often, answer positions cluster in
              questions that opt out of shuffling, duplicate question stems
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}
# ids the engine creates at runtime, or looks up only if the subject includes that widget
RUNTIME_IDS = ("print-sheet", "flashcard-element", "fc-type", "fc-front", "fc-sub", "fc-counter")
RUNTIME_ID_PREFIXES = ("mcq-",)


def run_node(js_source, *args):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js_source)
        tmp = f.name
    try:
        r = subprocess.run(["node", *args, tmp], capture_output=True, text=True)
    finally:
        os.unlink(tmp)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def extract_array(script, name):
    """Data arrays are injected by build_guide.py as one line of JSON: `const NAME = [...];`."""
    m = re.search(r"^\s*const " + name + r" = (\[.*\]);$", script, re.M)
    if not m:
        return None
    return json.loads(m.group(1).replace("<\\!--", "<!--"))


class TagBalance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"</{tag}> after <{self.stack[-1] if self.stack else '-'}>")


def lint_mcq(mcq):
    """Return warnings about answer patterns students can exploit without knowing the material."""
    warnings = []
    n = len(mcq)
    if n >= 4:
        longest = sum(1 for m in mcq
                      if len(m["opts"][m["ans"]]) > max(len(o) for i, o in enumerate(m["opts"]) if i != m["ans"]))
        if longest / n > 0.5:
            warnings.append(f"the correct option is the strictly longest one in {longest}/{n} questions; "
                            "students can guess by length (make distractors as specific as the answer)")
    fixed = [m for m in mcq if m.get("shuffle") is False]
    if len(fixed) >= 4:
        counts = {}
        for m in fixed:
            counts[m["ans"]] = counts.get(m["ans"], 0) + 1
        pos, top = max(counts.items(), key=lambda kv: kv[1])
        if top / len(fixed) > 0.5:
            warnings.append(f"{top}/{len(fixed)} questions with shuffle=false have option "
                            f"{chr(65 + pos)} as the answer")
    seen, dupes = set(), set()
    for m in mcq:
        (dupes if m["q"] in seen else seen).add(m["q"])
    if dupes:
        warnings.append(f"{len(dupes)} duplicate question stem(s), e.g. {sorted(dupes)[0][:40]!r}")
    return warnings


def main(argv):
    paths = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    if len(paths) != 1:
        print(__doc__.strip().split("\n\n")[1])
        return 2
    target = paths[0]
    base = os.path.dirname(os.path.abspath(target))
    with open(target, encoding="utf-8") as f:
        html = f.read()

    failures, warnings = [], []

    def check(label, ok, detail=""):
        print(("  ✓ " if ok else "  ✗ ") + label + (f"  ({detail})" if detail else ""))
        if not ok:
            failures.append(label)

    print(f"VALIDATE {target}\n--- structure ---")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    script = "\n".join(scripts)
    visible = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    ids = set(re.findall(r'\bid="([\w-]+)"', html))

    anchors = sorted(set(re.findall(r'href="#([\w-]+)"', html)))
    broken = [a for a in anchors if a not in ids]
    check("anchors resolve", not broken, str(broken) if broken else f"{len(anchors)} anchors")

    wanted = set(re.findall(r"""getElementById\(\s*["']([\w-]+)["']\s*\)""", html))
    missing_ids = sorted(w for w in wanted if w not in ids and w not in RUNTIME_IDS
                         and not w.startswith(RUNTIME_ID_PREFIXES))
    check("getElementById targets exist", not missing_ids, str(missing_ids) if missing_ids else "")

    handlers = set(re.findall(r'\bon(?:click|change|keydown|keyup|input)="(\w+)\(', html))
    defined = set(re.findall(r"function (\w+)\(", script))
    undefined = sorted(handlers - defined)
    check("inline handlers are defined", not undefined, str(undefined) if undefined else "")

    parser = TagBalance()
    parser.feed(html)
    check("tags are balanced", not parser.errors and not parser.stack,
          str(parser.errors[:3] + [f"unclosed <{t}>" for t in parser.stack[:3]]) if parser.errors or parser.stack else "")

    leftovers = re.findall(r"\{\{[A-Z_]+\}\}|@@ZONE[^@]*@@", html)
    check("no unfilled placeholders", not leftovers, str(leftovers[:3]) if leftovers else "")

    syntax_errors = []
    for i, src in enumerate(scripts):
        ok, out = run_node(src, "--check")
        if not ok:
            syntax_errors.append(f"script {i + 1}: " + out.splitlines()[-1][:160] if out else f"script {i + 1}")
    check("scripts parse (node --check)", not syntax_errors, "; ".join(syntax_errors))

    print("--- content ---")
    tex = re.findall(r"\$[^$\n]{1,80}\$", visible)
    tex += re.findall(r"\\(?:frac|sqrt|alpha|beta|Delta|sigma|times|cdot|leq|geq|neq|rightarrow)\b", visible)
    check("no raw LaTeX in visible text", not tex, str(tex[:3]) if tex else "")

    data = {name: extract_array(script, name) for name in ("flashcards", "mcqData", "termLexicon")}
    data_text = json.dumps({k: v for k, v in data.items() if v}, ensure_ascii=False)
    data_tex = re.findall(r"\\\\(?:frac|sqrt|alpha|beta|Delta|sigma|times|cdot|leq|geq|neq|rightarrow)\b", data_text)
    check("no raw LaTeX in data", not data_tex, str(data_tex[:3]) if data_tex else "")

    refs = sorted(set(re.findall(r"assets/[\w./-]+\.(?:jpg|jpeg|png|webp|gif|svg)", html)))
    missing = [r for r in refs if not os.path.exists(os.path.join(base, r))]
    check("referenced images exist", not missing, str(missing) if missing else f"{len(refs)} references")

    lexicon = data["termLexicon"]
    main_m = re.search(r'<main id="main-content">(.*)</main>', visible, re.S)
    funcs = re.search(r"(function lexiNorm.*?)function showTermCard", script, re.S)
    if lexicon is not None and main_m and funcs:
        texts = set()
        for en, strong in re.findall(r'<span class="en">(.*?)</span>|<strong(?:\s[^>]*)?>(.*?)</strong>',
                                     main_m.group(1), re.S):
            t = re.sub(r"<[^>]+>", "", en or strong).strip()
            if t:
                texts.add(t)
        allow = []
        allow_path = os.path.join(base, "lexicon_allowlist.txt")
        if os.path.exists(allow_path):
            with open(allow_path, encoding="utf-8") as f:
                allow = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        audit = ("const termLexicon = " + json.dumps(lexicon, ensure_ascii=False) + ";\n"
                 + funcs.group(1)
                 + "\nbuildLexiconIndex();\n"
                 + "const texts = " + json.dumps(sorted(texts), ensure_ascii=False) + ";\n"
                 + "const allow = " + json.dumps(allow, ensure_ascii=False) + ";\n"
                 + "const miss = texts.filter(t => !lookupTerm(t) && /[A-Za-z]{4,}/.test(t)"
                 + " && !allow.some(a => t.includes(a)));\n"
                 + "console.log(JSON.stringify({hits: texts.length - texts.filter(t => !lookupTerm(t)).length,"
                 + " total: texts.length, miss}));\n")
        ok, out = run_node(audit)
        result = json.loads(out) if ok else {"miss": [out[:200]], "hits": 0, "total": 0}
        check("English terms have term cards", ok and not result["miss"],
              f"{result['hits']} terms have cards" if not result["miss"]
              else "no card for: " + ", ".join(result["miss"][:8])
              + " (add a termLexicon key or a line in lexicon_allowlist.txt)")
    else:
        print("  - term-card audit skipped (no termLexicon)")

    print("--- teaching-quality lint ---")
    mcq = data["mcqData"] or []
    warnings += lint_mcq(mcq)
    for w in warnings:
        print(f"  ! {w}")
    if not warnings:
        print(f"  ✓ no answer patterns found ({len(mcq)} questions)")
    if strict and warnings:
        failures.append("teaching-quality lint (--strict)")

    print("\n" + (f"VALIDATE FAILED: {len(failures)} check(s)" if failures else
                  "VALIDATE OK" + (f" with {len(warnings)} warning(s)" if warnings else "")))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
