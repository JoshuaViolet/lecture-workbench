#!/usr/bin/env python3
"""
validate_guide.py — 学习指南三合一验证器
用法: python3 validate_guide.py <target.html>
检查: 静态回归(锚点/LaTeX/图片/id交叉/处理函数/HTML配对/占位符/JS语法)
      + 术语卡覆盖审计
退出码: 0 = 全绿; 1 = 有失败项
"""
import re, os, sys, subprocess, tempfile, json

VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

def run_node(js_source):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js_source)
        tmp = f.name
    r = subprocess.run(["node", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    return r.returncode == 0, (r.stdout + r.stderr).strip()

def main():
    if len(sys.argv) < 2:
        sys.exit("用法: validate_guide.py <target.html>")
    target = sys.argv[1]
    base = os.path.dirname(os.path.abspath(target))
    html = open(target, encoding="utf-8").read()
    fails = 0
    def check(label, ok, detail=""):
        nonlocal fails
        print(("  ✓ " if ok else "  ✗ ") + label + ("  — " + detail if detail and not ok else (f"  ({detail})" if detail else "")))
        if not ok: fails += 1

    print(f"VALIDATE: {target}\n--- 静态回归 ---")

    anchors = sorted(set(re.findall(r'href="#([\w-]+)"', html)))
    ids = set(re.findall(r'id="([\w-]+)"', html))
    broken = [a for a in anchors if a not in ids]
    check("锚点完整性", not broken, str(broken) if broken else f"{len(anchors)} 个锚点")

    visible = re.sub(r'<script>.*</script>', '', html, flags=re.S)
    tex = re.findall(r'\$[^$\n]{1,80}\$', visible)
    check("可见区无 LaTeX 残留", not tex, str(tex[:3]))

    # 数据/脚本区 LaTeX 扫描（可见区检查剥离 <script> 的盲区补充：
    # data.js 数组渲染后同样面向用户）
    sm_raw = re.search(r'<script>(.*)</script>', html, re.S)
    script_src = sm_raw.group(1) if sm_raw else ""
    script_tex = re.findall(r'\$(?!\d|\{)[^$\n]{1,60}\$', script_src)
    script_tex += re.findall(r'\\(?:Delta|alpha|beta|lambda|Sigma|sigma|rightarrow|leftarrow|text|frac|sqrt|pm|times|cdot|theta|mu|infty|geq|leq|neq|approx|sum)\b\{?', script_src)
    script_tex += re.findall(r'ightarrow', script_src)
    check("数据/脚本区无 LaTeX 残留", not script_tex, str(script_tex[:3]))

    refs = sorted(set(re.findall(r'assets/[\w./-]+\.(?:jpg|jpeg|png|webp)', html)))
    missing = [r for r in refs if not os.path.exists(os.path.join(base, r))]
    check("图片资源完整", not missing, str(missing) if missing else f"{len(refs)} 处引用")

    want = set(re.findall(r'getElementById\("([\w-]+)"\)', html))
    noelem = [w for w in want if w not in ids and not w.startswith("mcq-") and w != "print-sheet"]
    check("getElementById ↔ 静态 id", not noelem, str(noelem))

    handlers = set(re.findall(r'on(?:click|change|keydown)="(\w+)\(', html))
    defined = set(re.findall(r'function (\w+)\(', html))
    undef = [h for h in handlers if h not in defined]
    check("事件处理函数均有定义", not undef, str(undef))

    from html.parser import HTMLParser
    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True); self.stack=[]; self.errs=[]
        def handle_starttag(self,tag,attrs):
            if tag not in VOID: self.stack.append(tag)
        def handle_endtag(self,tag):
            if tag in VOID: return
            if self.stack and self.stack[-1]==tag: self.stack.pop()
            else: self.errs.append(tag)
    p = P(); p.feed(html)
    check("HTML 标签配对", not p.errs and not p.stack, str(p.errs[:3] + p.stack[:3]))

    leftovers = re.findall(r'\{\{[^}]+\}\}|@@ZONE[^@]*@@', html)
    check("无残留模板占位符", not leftovers, str(leftovers))

    check("DOC_ID/LS 存储命名空间存在", 'const DOC_ID = "' in html and "const LS = {" in html)

    sm = re.search(r'<script>(.*)</script>', html, re.S)
    # 只做语法检查：页面脚本依赖 DOM，不能直接用 node 执行
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(sm.group(1)); tmp = f.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    check("JS 语法 (node --check)", r.returncode == 0, r.stderr.strip()[:200])

    print("--- 术语卡覆盖审计 ---")
    if "const termLexicon" in html:
        lex = re.search(r'(const termLexicon = \[.*?\n        \];)', sm.group(1), re.S).group(1)
        funcs = re.search(r'(function lexiNorm.*?function showTermCard)', sm.group(1), re.S).group(1).replace("function showTermCard", "")
        main_m = re.search(r'<main id="main-content">(.*)</main>', visible, re.S)
        texts = set()
        for m2 in re.findall(r'<span class="en">(.*?)</span>|<strong>(.*?)</strong>', main_m.group(1), re.S):
            t = re.sub(r'<[^>]+>', '', m2[0] or m2[1]).strip()
            if t: texts.add(t)
        audit_js = lex + "\n" + funcs + "\nbuildLexiconIndex();\nconst texts = " + json.dumps(sorted(texts), ensure_ascii=False) + ";\nlet hit=0, miss=[]; for (const t of texts) { if (lookupTerm(t)) hit++; else miss.push(t); } console.log('HITS ' + hit + '/' + texts.length);\n"
        # 科目级放行清单（lexicon_allowlist.txt，与目标文件同目录）
        allow = []
        allow_path = os.path.join(base, "lexicon_allowlist.txt")
        if os.path.exists(allow_path):
            allow += [ln.strip() for ln in open(allow_path, encoding="utf-8")
                      if ln.strip() and not ln.startswith("#")]
        audit_js += "const allow = " + json.dumps(allow, ensure_ascii=False) + ";\n"
        audit_js += "const realMiss = miss.filter(t => /[A-Za-z]{4,}/.test(t) && !allow.some(a => t.includes(a)));\n"
        audit_js += "if (realMiss.length) { console.log('SUSPECT MISS:'); realMiss.forEach(t => console.log('  ' + t)); process.exit(1); } console.log('可疑漏配: 无');\n"
        ok, out = run_node(audit_js)
        print("  " + out.replace("\n", "\n  "))
        check("术语卡覆盖率（无可疑漏配）", ok)
    else:
        print("  (跳过：无 termLexicon)")

    print("\n" + ("VALIDATE FAILED: " + str(fails) + " 项" if fails else "VALIDATE ALL GREEN ✓"))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
