#!/usr/bin/env python3
"""
validate_guide.py: check a generated study guide.

Usage:
    python3 framework/validate_guide.py <guide.html> [--strict]

Checks (any failure exits 1):
  structure   anchors resolve, getElementById targets exist, inline handlers are defined,
              tags are balanced, no unfilled placeholders, every <script> passes `node --check`
  offline     nothing is loaded from the network (scripts, styles, fonts, images, frames);
              any local file the page still points to exists (a warning says which files
              must be kept next to the guide; built guides normally embed their images)
  content     no raw LaTeX in prose or data (the page has no math renderer; code and money
              amounts such as "$5 to $10" are not LaTeX), every English term in span.en /
              <strong> has a term card (or is allow-listed)
Without Node.js the two checks that need it are skipped, and the report says so.
Teaching-quality lint (warnings; failures with --strict):
              the correct option is the longest one in more than 40% of questions, question-type
              tags in stems, explanations that name options by letter although options are
              shuffled, answer positions cluster in questions that opt out of shuffling,
              duplicate question stems
"""
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}
# ids the engine creates at runtime, or looks up only if the subject includes that widget
RUNTIME_IDS = ("print-sheet", "flashcard-element", "fc-type", "fc-front", "fc-sub", "fc-counter")
RUNTIME_ID_PREFIXES = ("mcq-",)

# Picking the longest option scores about 25% on four options by chance; above this share of
# questions, students can score by length without reading the stem.
MCQ_LONGEST_LIMIT = 0.4
_TYPE_EN = (r"Recall|Definition|Discrimination|Mechanism|Evidence|Limitation|Transfer|Application"
            r"|Calculation|Derivation|Graph|Policy|Prediction|Predict output|Debug|Rewrite")
_TYPE_ZH = r"基础|定义|辨析|机制|证据|限制|迁移|应用|读图|推导|计算|代码|政策|局限|预测输出|找错|改写"
# a question-type label in a stem ("Mechanism: …", "[Transfer] …", "T01-Q01｜辨析｜…") hints at the answer
TYPE_TAG_RE = re.compile(
    r"自编\s*[·・]"
    r"|[｜|]\s*(?:" + _TYPE_ZH + r")[^｜|]{0,6}[｜|]"
    r"|^\s*(?:[\w-]+\s*[｜|:：]\s*)?[\[【(（]?\s*(?:(?i:" + _TYPE_EN + r")|" + _TYPE_ZH + r")\s*[\]】)）:：]")
# "option B", "(C)", "B is wrong", "选项 B", "A 项错" no longer match what the student saw once options are shuffled
LETTER_REF_RE = re.compile(
    r"(?i:\b(?:option|choice|answer)s?\s+(?:is\s+)?)\(?[A-E]\b"
    r"|(?<![A-Za-z])[（(][A-E][)）]"
    r"|\b[A-E]\s+(?:is|was)\s+(?:(?:not\s+)?(?:wrong|right|correct|incorrect)|the answer)\b"
    r"|选项\s*[A-E](?![A-Za-z])"
    r"|(?<![A-Za-z])[A-E]\s*(?:项|错|对|是正确|不对)")


# Resources a page loads by itself. An <a href> is only a link and loads nothing until clicked.
TAG_RE = re.compile(r"""<([A-Za-z][\w-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>""")
LOAD_ATTR_RE = re.compile(r"""(?<![\w-])(src|srcset|poster|data|href|style)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))""",
                          re.I)
HREF_LOADS = {"link", "image", "use", "feimage"}
CSS_REF_RE = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)"'\s]+))\s*\)|@import\s+(?:"([^"]*)"|'([^']*)')""", re.I)
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")   # C:\slides\s1.png is a Windows path, not a URL scheme


def css_refs(css):
    return [next(g for g in m.groups() if g is not None) for m in CSS_REF_RE.finditer(css)]


def loaded_urls(page_html):
    """Every URL the page would fetch on its own: src, srcset, poster, <object data>, the href of
    <link> and SVG <image>/<use>, and url() / @import in CSS. Scripts and comments are skipped."""
    page_html = re.sub(r"<!--.*?-->", "", page_html, flags=re.S)
    page_html = re.sub(r"(<script\b[^>]*>).*?</script>", r"\1", page_html, flags=re.S | re.I)   # keep src=
    urls = []
    for css in re.findall(r"<style\b[^>]*>(.*?)</style>", page_html, flags=re.S | re.I):
        urls += css_refs(css)
    page_html = re.sub(r"<style\b[^>]*>.*?</style>", "", page_html, flags=re.S | re.I)
    for tag, attrs in TAG_RE.findall(page_html):
        tag = tag.lower()
        for m in LOAD_ATTR_RE.finditer(attrs):
            name, value = m.group(1).lower(), htmllib.unescape(next(g for g in m.groups()[1:] if g is not None))
            if name == "style":
                urls += css_refs(value)
            elif name == "srcset":
                urls += [c.split()[0] for c in value.split(",") if c.strip()]
            elif (name != "href" or tag in HREF_LOADS) and (name != "data" or tag == "object"):
                urls.append(value)
    return urls


def classify_url(url, base):
    """('remote', url), ('local', path) or None for URLs that load nothing from outside the page."""
    url = url.strip()
    if not url or url.startswith("#") or url.lower().startswith(("data:", "blob:", "javascript:", "about:")):
        return None
    if DRIVE_RE.match(url):
        return ("local", os.path.normpath(url))
    if url.startswith("//") or (SCHEME_RE.match(url) and not url.lower().startswith("file:")):
        return ("remote", url)
    if url.lower().startswith("file:"):
        return ("local", url2pathname(urlsplit(url).path))
    return ("local", os.path.normpath(os.path.join(base, unquote(urlsplit(url).path))))


# Raw LaTeX that would reach the reader as source. Inline math follows pandoc's rule: the opening $
# has a non-space after it, the closing $ a non-space before it and no digit after it, so money
# ("$5 to $10", "$5-$10") is not math. Code is removed first: R's df$col and shell's $HOME are code.
TEX_RE = re.compile(r"\$\$(?=\S)[^$]{1,200}?\$\$"
                    r"|(?<![\\$])\$(?![\s$])[^$\n]{1,80}?(?<![\s\\$])\$(?![\d$])"
                    r"|\\(?:frac|sqrt|alpha|beta|Delta|sigma|times|cdot|leq|geq|neq|rightarrow)\b")
# Fields of the data arrays that hold prose (code and IPA are left out).
PROSE_FIELDS = {"flashcards": ("front", "back"), "mcqData": ("q", "opts", "exp"),
                "termLexicon": ("term", "parts", "hook")}


def raw_tex(markup):
    """LaTeX fragments in HTML or plain text, ignoring <pre>, <code>, <script> and <style>."""
    text = re.sub(r"<(pre|code|script|style)\b[^>]*>.*?</\1\s*>", "", markup, flags=re.S | re.I)
    text = re.sub(r"<[^>]*>", "", text)
    return [m.group(0)[:40] for m in TEX_RE.finditer(text)]


NODE = shutil.which("node")


def relative(path, base):
    try:
        return os.path.relpath(path, base)
    except ValueError:   # another drive on Windows
        return path


def run_node(js_source, *args):
    """(ok, output), or (None, reason) when Node.js is not installed."""
    if not NODE:
        return None, "Node.js is not installed (https://nodejs.org), so this check was skipped"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js_source)
        tmp = f.name
    try:
        r = subprocess.run([NODE, *args, tmp], capture_output=True, text=True)
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
    """Return warnings about patterns students can exploit without knowing the material."""
    warnings = []
    n = len(mcq)
    if n >= 4:
        longest = sum(1 for m in mcq
                      if len(m["opts"][m["ans"]]) > max(len(o) for i, o in enumerate(m["opts"]) if i != m["ans"]))
        if longest / n > MCQ_LONGEST_LIMIT:
            warnings.append(f"the correct option is the strictly longest one in {longest}/{n} questions "
                            f"(limit {MCQ_LONGEST_LIMIT:.0%}); students can guess by length "
                            "(make distractors as specific as the answer, or trim the answer)")
    tagged = [i for i, m in enumerate(mcq) if TYPE_TAG_RE.search(m["q"])]
    if tagged:
        warnings.append(f"{len(tagged)} question stem(s) carry a question-type tag, which hints at the answer; "
                        "keep types out of the stem: " + question_list(tagged, mcq))
    lettered = [i for i, m in enumerate(mcq)
                if m.get("shuffle") is not False and LETTER_REF_RE.search(re.sub(r"<[^>]+>", "", m["exp"]))]
    if lettered:
        warnings.append(f"{len(lettered)} explanation(s) refer to options by letter, but options are shuffled; "
                        "name the option by its content: " + question_list(lettered))
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


def question_list(indexes, mcq=None, limit=6):
    """'Q2, Q5' (1-based), with the start of each stem when mcq is given."""
    parts = [f"Q{i + 1}" + (f" {mcq[i]['q'].strip()[:24]!r}" if mcq else "") for i in indexes[:limit]]
    return ", ".join(parts) + (", …" if len(indexes) > limit else "")


def main(argv):
    paths = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    unknown = [a for a in argv if a.startswith("--") and a != "--strict"]
    if len(paths) != 1 or unknown:
        print((f"unknown option {unknown[0]}\n" if unknown else "") + __doc__.strip().split("\n\n")[1])
        return 2
    target = paths[0]
    base = os.path.dirname(os.path.abspath(target))
    try:
        with open(target, encoding="utf-8") as f:
            html = f.read()
    except OSError as e:
        print(f"VALIDATE FAILED\n  cannot read {target}: {e.strerror}")
        return 1

    failures, warnings, skipped = [], [], []

    def check(label, ok, detail=""):
        print(("  ✓ " if ok else "  ✗ ") + label + (f"  ({detail})" if detail else ""))
        if not ok:
            failures.append(label)

    print(f"VALIDATE {target}\n--- structure ---")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    script = "\n".join(scripts)
    visible = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    ids = set(re.findall(r"""\bid\s*=\s*["']([^"'\s]+)["']""", html))

    anchors = sorted(set(htmllib.unescape(a) for a in re.findall(r"""\bhref\s*=\s*["']#([^"'\s]+)["']""", html)))
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
        if ok is None:
            skipped.append("scripts parse (node --check)")
            print(f"  - scripts parse (node --check): {out}")
            break
        if not ok:
            syntax_errors.append(f"script {i + 1}: " + out.splitlines()[-1][:160] if out else f"script {i + 1}")
    else:
        check("scripts parse (node --check)", not syntax_errors, "; ".join(syntax_errors))

    print("--- offline ---")
    data = {name: extract_array(script, name) for name in ("flashcards", "mcqData", "termLexicon")}
    page_urls = loaded_urls(html)
    # HTML in the data arrays (explanations, etymologies) is inserted into the page at runtime
    for item in (data["mcqData"] or []) + (data["termLexicon"] or []):
        for field in ("exp", "parts"):
            if isinstance(item.get(field), str):
                page_urls += loaded_urls(item[field])
    found = [c for c in (classify_url(u, base) for u in page_urls) if c]
    remote = sorted({u for kind, u in found if kind == "remote"})
    local = sorted({p for kind, p in found if kind == "local"})
    missing = [p for p in local if not os.path.isfile(p)]
    embedded = sum(1 for u in page_urls if u.strip().lower().startswith("data:"))
    check("loads nothing from the network", not remote,
          "breaks offline: " + ", ".join(u[:80] for u in remote[:5])
          + " (link to it with <a href>, or save the file locally so the build embeds it)" if remote else "")
    check("files it points to exist", not missing,
          "missing: " + ", ".join(relative(p, base) for p in missing[:5]) if missing
          else (f"{embedded} embedded" if embedded else ""))
    beside = [p for p in local if p not in missing]
    if beside:
        print(f"  ! not a single file: keep {len(beside)} file(s) next to the guide: "
              + ", ".join(relative(p, base) for p in beside[:5]) + (", …" if len(beside) > 5 else "")
              + " (images are embedded unless config.embed_images is false)")

    print("--- content ---")
    tex = raw_tex(visible)
    check("no raw LaTeX in visible text", not tex, str(tex[:3]) if tex else "")

    data_tex = []
    for name, fields in PROSE_FIELDS.items():
        for item in data[name] or []:
            for field in fields:
                values = item.get(field) if isinstance(item.get(field), list) else [item.get(field)]
                # an option with a line break is shown as code
                data_tex += [t for v in values if isinstance(v, str) and not (field == "opts" and "\n" in v)
                             for t in raw_tex(v)]
    check("no raw LaTeX in data", not data_tex, str(data_tex[:3]) if data_tex else "")

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
        if ok is None:
            skipped.append("English terms have term cards")
            print(f"  - English terms have term cards: {out}")
        else:
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

    notes = ([f"{len(warnings)} warning(s)"] if warnings else []) \
        + ([f"{len(skipped)} check(s) skipped: Node.js not found"] if skipped else [])
    print("\n" + (f"VALIDATE FAILED: {len(failures)} check(s)" if failures else
                  "VALIDATE OK" + (f" with {', '.join(notes)}" if notes else "")))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
