#!/usr/bin/env python3
"""
cli.py: one entry point for scaffolding, building and checking study guides.

Usage:
    python3 framework/cli.py new <subject_dir> [--title T] [--doc-id ID] [--output NAME.html]
    python3 framework/cli.py build (<subject_dir>... | --all) [--validate] [--strict]
    python3 framework/cli.py validate (<subject_dir> | <guide.html>) [--strict]

`new` writes a config.json, content.html and data.json that build and validate as they are.
`build` and `validate` run build_guide.py and validate_guide.py.
"""
import argparse
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_guide  # noqa: E402
import validate_guide  # noqa: E402

CONTENT_TEMPLATE = """\
<!-- The lesson body: one <section> per chapter. Each section id needs a matching link in
     config.json nav_html. Teaching components to copy from: examples/teaching-components.html -->
<section id="intro">
<h2 class="chapter-title">1.0 本讲主线</h2>
<p>在这里写正文。英文术语写成 <span class="term"><span class="en">Example term</span> <span class="zh">(示例术语)</span></span>，悬停即可看到 data.json 里 termLexicon 的术语卡。</p>
</section>

<!-- Flashcards come from data.json flashcards. Delete this section if the guide has none. -->
<section id="flashcards">
<h2 class="chapter-title">1.1 抽认卡</h2>
<div class="flashcard-wrapper">
<div class="flashcard" id="flashcard-element" onclick="flipCard()" tabindex="0" role="button" aria-label="翻转抽认卡"><div class="flashcard-type" id="fc-type"></div><div class="flashcard-text" id="fc-front"></div><div class="flashcard-sub" id="fc-sub"></div></div>
<div class="flashcard-controls"><button class="fc-btn fc-btn-sec" onclick="prevCard()">上一张</button><span id="fc-counter"></span><button class="fc-btn fc-btn-sec" onclick="nextCard()">下一张</button><button class="fc-btn fc-btn-sec" onclick="shuffleCards()">随机</button></div>
</div>
</section>

<!-- Questions come from data.json mcqData. Delete this section if the guide has none. -->
<section id="practice">
<h2 class="chapter-title">1.2 选择题</h2>
<p>已答 <b id="mcq-done">0</b> 题，正确 <b id="mcq-score">0</b> 题。<button class="fc-btn fc-btn-sec" onclick="resetMCQ()">重新作答</button></p>
<div id="mcq-app" class="mcq-container"></div>
</section>
"""

NAV_HTML = ('<li><a href="#intro">1.0 本讲主线</a></li>\n'
            '<li><a href="#flashcards">1.1 抽认卡</a></li>\n'
            '<li><a href="#practice">1.2 选择题</a></li>\n')

STARTER_DATA = {
    "flashcards": [{"front": "示例问题：这一讲要解释的机制是什么？", "back": "用自己的话写出答案。"}],
    "mcqData": [{"q": "示例题：ans 字段表示什么？",
                 "opts": ["正确选项在 opts 中的下标（从 0 开始）", "正确选项的文字",
                          "这道题的分值", "选项的数量"],
                 "ans": 0, "exp": "ans 是正确选项在 opts 中的下标，从 0 开始计数；页面每次渲染都会打乱选项顺序。"}],
    "termLexicon": [{"keys": ["example term"], "term": "Example term 示例术语",
                     "ipa": "/ɪɡˈzɑːmpəl tɜːm/", "chunks": "ex-AM-ple TERM",
                     "parts": "替换成词源或构词拆解。", "hook": "替换成一句记忆提示。"}],
}


def words(name):
    return [w for w in re.split(r"[^A-Za-z0-9]+", name) if w]


def new_subject(subject_dir, title=None, doc_id=None, output=None):
    """Create a subject folder that builds and validates as is. Returns the created folder."""
    subject_dir = os.path.abspath(subject_dir)
    if os.path.isdir(subject_dir) and os.listdir(subject_dir):
        raise build_guide.BuildError(f"{subject_dir} already exists and is not empty")
    if os.path.exists(subject_dir) and not os.path.isdir(subject_dir):
        raise build_guide.BuildError(f"{subject_dir} exists and is not a folder")

    parts = words(os.path.basename(subject_dir))
    if not (doc_id and output) and not parts:
        raise build_guide.BuildError("cannot derive an id from the folder name; pass --doc-id and --output")
    slug = "-".join(p.lower() for p in parts)
    doc_id = doc_id or slug.replace("-", "_")
    cfg = {
        "doc_id": doc_id,
        "app_id": (slug or doc_id.replace("_", "-")) + "-guide",
        "title": title or " ".join(p.capitalize() for p in parts) or doc_id,
        "output": output or "_".join(p.capitalize() for p in parts) + ".html",
    }
    cfg["header_html"] = f'<header class="doc-header"><h1>{html.escape(cfg["title"])}</h1></header>'
    cfg["nav_html"] = NAV_HTML
    errors, _ = build_guide.check_config(cfg)
    if errors:
        raise build_guide.BuildError("\n".join(errors))

    # doc_id namespaces localStorage, and every file:// guide shares one origin.
    roots = {os.path.dirname(subject_dir), os.path.join(build_guide.ROOT, "subjects")}
    others = {d for r in roots if os.path.isdir(r) for d in build_guide.find_subject_dirs(r)}
    for other in sorted(others):
        try:
            with open(os.path.join(other, "config.json"), encoding="utf-8") as f:
                taken = json.load(f).get("doc_id")
        except (OSError, ValueError, AttributeError):
            continue
        if taken == doc_id:
            raise build_guide.BuildError(f"doc_id {doc_id!r} is already used by {other}; pass --doc-id")

    os.makedirs(subject_dir, exist_ok=True)
    for name, text in (("config.json", json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"),
                       ("content.html", CONTENT_TEMPLATE),
                       ("data.json", json.dumps(STARTER_DATA, ensure_ascii=False, indent=2) + "\n")):
        with open(os.path.join(subject_dir, name), "w", encoding="utf-8") as f:
            f.write(text)
    return subject_dir


def guide_path(target):
    """A subject folder resolves to its built guide; anything else is taken as the guide itself."""
    if not os.path.isdir(target):
        return target
    try:
        with open(os.path.join(target, "config.json"), encoding="utf-8") as f:
            output = json.load(f)["output"]
    except (OSError, ValueError, KeyError, TypeError):
        raise build_guide.BuildError(f"{target} has no readable config.json with an output name")
    path = os.path.join(target, output)
    if not os.path.exists(path):
        raise build_guide.BuildError(f"{path} has not been built yet; run: build {target}")
    return path


def cmd_new(args):
    try:
        path = new_subject(args.subject_dir, args.title, args.doc_id, args.output)
    except build_guide.BuildError as e:
        print("NEW FAILED\n  " + str(e).replace("\n", "\n  "))
        return 1
    try:
        label = os.path.relpath(path)
    except ValueError:  # another drive on Windows
        label = path
    label = path if label.startswith("..") else label
    print(f"NEW OK        {label}\n"
          f"  edit config.json, content.html and data.json, then run:\n"
          f"  python3 framework/cli.py build {label} --validate")
    return 0


def cmd_build(args):
    if args.all:
        if args.subject_dirs:
            print("build: give subject folders or --all, not both")
            return 2
        return build_guide.main(["--all"] + (["--validate"] if args.validate else [])
                                + (["--strict"] if args.strict else []))
    if not args.subject_dirs:
        print("build: give one or more subject folders, or --all")
        return 2
    return build_guide.build_many(args.subject_dirs, validate=args.validate, strict=args.strict)


def cmd_validate(args):
    try:
        path = guide_path(args.target)
    except build_guide.BuildError as e:
        print(f"VALIDATE FAILED\n  {e}")
        return 1
    if not os.path.exists(path):
        print(f"VALIDATE FAILED\n  {path} does not exist")
        return 1
    return validate_guide.main([path] + (["--strict"] if args.strict else []))


def parser():
    p = argparse.ArgumentParser(prog="cli.py", description="Scaffold, build and validate offline study guides.")
    sub = p.add_subparsers(dest="command", metavar="{new,build,validate}")

    new = sub.add_parser("new", help="create a subject folder with config.json, content.html and data.json")
    new.add_argument("subject_dir", help="folder to create, e.g. subjects/my-lecture")
    new.add_argument("--title", help="page title (default: from the folder name)")
    new.add_argument("--doc-id", help="storage namespace, unique per guide (default: from the folder name)")
    new.add_argument("--output", help="generated file name (default: from the folder name)")
    new.set_defaults(func=cmd_new)

    build = sub.add_parser("build", help="build subject folders into single-file guides")
    build.add_argument("subject_dirs", nargs="*", metavar="subject_dir")
    build.add_argument("--all", action="store_true", help="every subject under subjects/")
    build.add_argument("--validate", action="store_true", help="validate each guide after building it")
    build.add_argument("--strict", action="store_true", help="with --validate, fail on teaching-quality warnings")
    build.set_defaults(func=cmd_build)

    validate = sub.add_parser("validate", help="check a built guide")
    validate.add_argument("target", help="a subject folder (its built guide is checked) or a guide .html file")
    validate.add_argument("--strict", action="store_true", help="fail on teaching-quality warnings")
    validate.set_defaults(func=cmd_validate)
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    if not args.command:
        p.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
