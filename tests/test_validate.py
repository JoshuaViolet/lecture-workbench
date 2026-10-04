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
