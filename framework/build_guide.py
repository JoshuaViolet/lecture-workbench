#!/usr/bin/env python3
"""
build_guide.py — 学习指南生成器
用法:
    python3 build_guide.py <subject_dir>            构建单个科目
    python3 build_guide.py --all                    构建 subjects/ 下全部科目
    python3 build_guide.py <subject_dir> --validate 构建后自动跑 validate_guide.py

输入:  framework/template.html + subjects/<name>/{config.json, content.html, data.js,
       subject_js.js, subject_css.css}
输出:  subjects/<name>/<config.output>  (单文件、零依赖、可直接双击使用)
契约:  输出中不得残留任何 {{PLACEHOLDER}} 或 @@ZONE@@ 标记。
"""
import re, os, sys, json, subprocess

DATA_ARRAYS = ["flashcards", "mcqData", "termLexicon"]

def load(path):
    return open(path, encoding="utf-8").read()

def build(subject_dir):
    fw_dir = os.path.dirname(os.path.abspath(__file__))
    tpl = load(os.path.join(fw_dir, "template.html"))
    cfg = json.load(open(os.path.join(subject_dir, "config.json"), encoding="utf-8"))

    # --- 简单占位符（允许同一占位符在模板中出现多次，全部替换）---
    simple = {
        "<title>{{TITLE}}</title>": "<title>" + cfg["title"] + "</title>",
        'const DOC_ID = "{{DOC_ID}}";': 'const DOC_ID = "' + cfg["doc_id"] + '";',
        'const APP_ID = "{{APP_ID}}";': 'const APP_ID = "' + cfg["app_id"] + '";',
        "<!-- @@ZONE:HEADER@@ -->": cfg["header_html"],
        "<!-- @@ZONE:NAV@@ -->": cfg.get("nav_html", ""),
        # 品牌与文案（科目可配，缺省从 title 派生或走通用兜底）
        "{{SIDEBAR_TITLE}}": cfg.get("sidebar_title", cfg["title"]),
        "{{SIDEBAR_META}}": cfg.get("sidebar_meta", ""),
        "{{SEARCH_PLACEHOLDER}}": cfg.get("search_placeholder", "🔍 实时搜索概念..."),
    }
    for old, new in simple.items():
        assert tpl.count(old) >= 1, f"占位符缺失: {old[:40]}"
        tpl = tpl.replace(old, new)

    # --- 文件区块 ---
    def zone(marker, filename, required=True):
        nonlocal tpl
        path = os.path.join(subject_dir, filename)
        if not os.path.exists(path):
            assert not required, f"缺少科目文件: {filename}"
            tpl = tpl.replace(marker, "")
            return
        content = load(path)
        assert tpl.count(marker) == 1, f"区块标记缺失: {marker}"
        tpl = tpl.replace(marker, content.strip("\n"), 1)

    zone("/* @@ZONE:EXTRA_CSS@@ */", "subject_css.css", required=False)
    zone("// @@ZONE:EXTRA_JS@@", "subject_js.js", required=False)

    # --- 数据数组（从 data.js 按 const 名提取）---
    data_js = load(os.path.join(subject_dir, "data.js"))
    for name in DATA_ARRAYS:
        m = re.search(r'const ' + name + r' = \[.*?\n        \];', data_js, re.S)
        assert m, f"data.js 中未找到 const {name}"
        marker = '// @@ZONE:DATA:' + name + '@@'
        assert tpl.count(marker) == 1, f"区块标记缺失: {marker}"
        tpl = tpl.replace(marker, m.group(0), 1)

    # --- main 正文 ---
    content = load(os.path.join(subject_dir, "content.html"))
    assert tpl.count("<!-- @@ZONE:CONTENT@@ -->") == 1
    tpl = tpl.replace("<!-- @@ZONE:CONTENT@@ -->", content, 1)

    # --- 完整性闸门 ---
    leftovers = re.findall(r'\{\{[^}]+\}\}|@@ZONE[^@]*@@', tpl)
    assert not leftovers, f"输出残留未填充占位符: {leftovers}"

    out_path = os.path.join(subject_dir, cfg["output"])
    header = "<!-- GENERATED FILE — 由 build_guide.py 生成，请勿手改；修改 subjects/ 源文件后重新构建 -->\n"
    open(out_path, "w", encoding="utf-8").write(header + tpl)
    print(f"BUILD OK -> {out_path} ({len(tpl)} 字符)")
    return out_path

def find_subject_dirs(subjects_root):
    found = []
    skip = {"_archive", "归档"}
    for dirpath, dirnames, filenames in os.walk(subjects_root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        if "config.json" in filenames:
            found.append(dirpath)
    return sorted(found)

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_validate = "--validate" in sys.argv
    if "--all" in sys.argv:
        subs = find_subject_dirs(os.path.join(root, "subjects"))
        assert subs, "subjects/ 下没有带 config.json 的科目"
    elif args:
        subs = [os.path.abspath(args[0])]
    else:
        sys.exit("用法: build_guide.py <subject_dir> | --all [--validate]")
    for subj in subs:
        out = build(subj)
        if do_validate:
            r = subprocess.run([sys.executable, os.path.join(here, "validate_guide.py"), out])
            if r.returncode != 0:
                sys.exit(r.returncode)

if __name__ == "__main__":
    main()
