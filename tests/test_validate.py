import json
import os
import subprocess
import sys

from conftest import DEMO, FRAMEWORK, build_guide

VALIDATE = os.path.join(FRAMEWORK, "validate_guide.py")
with open(os.path.join(DEMO, "data.json"), encoding="utf-8") as f:
    LEXICON = json.load(f)["termLexicon"]


def validate(path, *flags):
    r = subprocess.run([sys.executable, VALIDATE, path, *flags], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_demo_passes(demo_guide):
    code, out = validate(demo_guide, "--strict")
    assert code == 0, out
    assert "VALIDATE OK" in out


def test_answer_by_length_pattern_is_a_warning_and_fails_strict(make_subject):
    mcq = [{"q": f"q{i}", "opts": ["short", "the much longer and more careful answer", "tiny", "no"],
            "ans": 1, "exp": "e"} for i in range(5)]
    out_path = build_guide.build(str(make_subject(data={"mcqData": mcq, "termLexicon": LEXICON})))
    code, out = validate(out_path)
    assert code == 0 and "longest one in 5/5" in out
    code, _ = validate(out_path, "--strict")
    assert code == 1


def test_fixed_order_questions_with_clustered_answers_warn(make_subject):
    mcq = [{"q": f"q{i}", "opts": ["aaa", "bbb", "ccc", "ddd"], "ans": 1, "exp": "e", "shuffle": False}
           for i in range(4)]
    code, out = validate(build_guide.build(str(make_subject(data={"mcqData": mcq, "termLexicon": LEXICON}))))
    assert code == 0 and "have option B as the answer" in out


def test_english_term_without_card_fails(make_subject):
    content = ('<section id="s"><p><span class="term"><span class="en">Interpolation search</span>'
               ' <span class="zh">(插值查找)</span></span></p></section>')
    code, out = validate(build_guide.build(str(make_subject(content=content))))
    assert code == 1 and "no card for: Interpolation search" in out


def test_allowlisted_term_passes(make_subject):
    content = '<section id="s"><p><strong>Interpolation search</strong></p></section>'
    subject = make_subject(content=content)
    (subject / "lexicon_allowlist.txt").write_text("# not covered yet\nInterpolation\n", encoding="utf-8")
    code, out = validate(build_guide.build(str(subject)))
    assert code == 0, out


def test_broken_anchor_fails(make_subject):
    content = '<section id="s"><p><a href="#nowhere">x</a></p></section>'
    code, out = validate(build_guide.build(str(make_subject(content=content))))
    assert code == 1 and "nowhere" in out


def lint(make_subject, mcq, *flags, name="subject"):
    data = {"mcqData": mcq, "termLexicon": LEXICON}
    return validate(build_guide.build(str(make_subject(name=name, data=data))), *flags)


def test_longest_answer_warns_above_forty_percent(make_subject):
    even = ["one", "two", "six", "ten"]
    mcq = [{"q": f"q{i}", "opts": ["short", "the longest option", "tiny", "no"], "ans": 1, "exp": "e"}
           for i in range(2)]
    mcq += [{"q": f"r{i}", "opts": even, "ans": 0, "exp": "e"} for i in range(3)]
    code, out = lint(make_subject, mcq)          # 2/5 = 40%: at the limit
    assert code == 0 and "longest one in" not in out
    code, out = lint(make_subject, mcq[:4], name="four")  # 2/4 = 50%
    assert "longest one in 2/4 questions (limit 40%)" in out


def test_question_type_tags_in_stems_warn(make_subject):
    stems = ["Mechanism: why does the loop stop?", "T01-Q02｜辨析｜哪一项正确？", "[Transfer] A new case",
             "Recall that the list is sorted. What next?"]
    mcq = [{"q": q, "opts": ["aaa", "bbb", "ccc", "ddd"], "ans": i, "exp": "e"} for i, q in enumerate(stems)]
    code, out = lint(make_subject, mcq)
    assert code == 0 and "3 question stem(s) carry a question-type tag" in out
    assert "Q1 'Mechanism" in out and "Q4" not in out


def test_letter_references_in_explanations_warn_unless_order_is_fixed(make_subject):
    exps = ["Option B reverses the direction.", "<b>(C)</b> misreads it.", "选项B把方向弄反了。",
            "P(A) is a probability; lo = mid + 1 shrinks the range."]
    mcq = [{"q": f"q{i}", "opts": ["aaa", "bbb", "ccc", "ddd"], "ans": i, "exp": e} for i, e in enumerate(exps)]
    mcq.append({"q": "fixed", "opts": ["aaa", "bbb", "All of the above"], "ans": 2, "exp": "C covers both.",
                "shuffle": False})
    code, out = lint(make_subject, mcq)
    assert code == 0 and "3 explanation(s) refer to options by letter" in out
    assert "Q1, Q2, Q3" in out and "Q4" not in out and "Q5" not in out
    code, _ = lint(make_subject, mcq, "--strict", name="strict")
    assert code == 1


def test_anything_loaded_from_the_network_fails(make_subject):
    content = ('<section id="s"><p><a href="https://example.com/reading">a link is fine</a></p>'
               '<p><img src="https://example.com/slide.png" alt=""></p>'
               '<script src="https://cdn.example.com/mathjax.js"></script>'
               '<div style="background: url(//cdn.example.com/bg.png)"></div></section>')
    code, out = validate(build_guide.build(str(make_subject(content=content))))
    assert code == 1 and "✗ loads nothing from the network" in out
    for url in ("https://example.com/slide.png", "https://cdn.example.com/mathjax.js", "//cdn.example.com/bg.png"):
        assert url in out
    assert "example.com/reading" not in out


def test_files_beside_the_guide_warn_and_missing_ones_fail(make_subject):
    subject = make_subject(config={"embed_images": False})
    code, out = validate(build_guide.build(str(subject)))
    assert code == 0 and "not a single file: keep 1 file(s) next to the guide: assets/trace-42.svg" in out
    os.remove(subject / "assets" / "trace-42.svg")
    code, out = validate(str(subject / "Binary_Search_Demo.html"))
    assert code == 1 and "missing: assets/trace-42.svg" in out


def test_the_demo_guide_embeds_its_figure(demo_guide):
    code, out = validate(demo_guide)
    assert code == 0 and "✓ files it points to exist  (1 embedded)" in out and "not a single file" not in out


def test_money_and_code_are_not_mistaken_for_latex(make_subject):
    content = ('<section id="s"><p>The price rose from $5 to $10, and revenue was $1,000 against a $800 cost;'
               ' a range of $5-$10, or 价格从$5涨到$10。</p>'
               '<pre><code>mean(df$age + df$height)\necho "$HOME/$USER"</code></pre></section>')
    data = {"termLexicon": LEXICON, "mcqData": [
        {"q": "A ticket costs $5 and a meal $12. Which is cheaper?", "opts": ["the ticket", "the meal"],
         "ans": 0, "exp": "$5 is less than $12; in R, <code>df$price</code> holds them."},
        {"q": "What prints?", "code": "cat(df$a$b)", "opts": ["x$a$\n1", "2"], "ans": 1, "exp": "e"}]}
    code, out = validate(build_guide.build(str(make_subject(content=content, data=data))))
    assert code == 0, out


def test_raw_latex_in_prose_or_data_fails(make_subject):
    content = '<section id="s"><p>The multiplier is $\\frac{1}{1-c}$, so $Y = C + I$.</p></section>'
    code, out = validate(build_guide.build(str(make_subject(content=content))))
    assert code == 1 and "✗ no raw LaTeX in visible text" in out and "$Y = C + I$" in out
    data = {"termLexicon": LEXICON, "flashcards": [{"front": "Define $x^2$", "back": "$$a + b$$"}]}
    code, out = validate(build_guide.build(str(make_subject(name="data", data=data))))
    assert code == 1 and "✗ no raw LaTeX in data" in out and "$x^2$" in out


def test_without_node_the_node_checks_are_skipped_not_crashed(demo_guide):
    env = dict(os.environ, PATH=os.pathsep.join(p for p in os.environ["PATH"].split(os.pathsep)
                                                  if not os.path.exists(os.path.join(p, "node"))))
    r = subprocess.run([sys.executable, VALIDATE, demo_guide], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "VALIDATE OK with 2 check(s) skipped: Node.js not found" in r.stdout and "Traceback" not in r.stderr


def test_single_quoted_ids_and_anchors_are_checked(make_subject):
    content = "<section id='s'><p><a href='#s'>top</a> <a href='#nowhere'>x</a></p></section>"
    code, out = validate(build_guide.build(str(make_subject(content=content))))
    assert code == 1 and "['nowhere']" in out


def test_unknown_options_and_missing_files_are_reported(demo_guide, tmp_path):
    assert validate(demo_guide, "--strcit")[0] == 2
    code, out = validate(str(tmp_path / "nope.html"))
    assert code == 1 and "cannot read" in out and "Traceback" not in out
