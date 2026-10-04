import json
import os
import re
import subprocess
import sys

import pytest

from conftest import FRAMEWORK, build_guide

DEMO_DATA = json.loads(open(os.path.join(os.path.dirname(FRAMEWORK), "subjects", "demo-binary-search",
                                         "data.json"), encoding="utf-8").read())


def built(path):
    return open(path, encoding="utf-8").read()


def test_demo_builds_with_data_injected_as_json(make_subject):
    out = built(build_guide.build(str(make_subject())))
    assert not re.search(r"\{\{[A-Z_]+\}\}|@@ZONE", out)
    line = re.search(r"^\s*const mcqData = (\[.*\]);$", out, re.M).group(1)
    assert json.loads(line) == DEMO_DATA["mcqData"]


def test_titles_are_escaped_for_html_and_js(make_subject):
    nasty = 'Q&A "quoted" </title><script>alert(1)</script>'
    out = built(build_guide.build(str(make_subject(config={"title": nasty, "sidebar_title": nasty}))))
    assert "<title>Q&amp;A \"quoted\" &lt;/title&gt;&lt;script&gt;alert(1)&lt;/script&gt;</title>" in out
    outside_scripts = re.sub(r"<script>.*?</script>", "", out, flags=re.S)
    assert "alert(1)" not in outside_scripts.replace("&lt;script&gt;alert(1)", "")
    js = re.search(r"const GUIDE_TITLE = (.*);", out).group(1)
    assert "</" not in js and json.loads(js.replace("<\\/", "</")) == nasty


def test_data_strings_cannot_close_the_script_element(make_subject):
    data = {"flashcards": [{"front": "</script><b>x</b>", "back": "<!-- c -->"}]}
    out = built(build_guide.build(str(make_subject(data=data))))
    scripts = re.findall(r"<script>(.*?)</script>", out, re.S)
    assert len(scripts) == 1 and "<\\/script>" in scripts[0]


def test_content_text_is_never_treated_as_a_marker(make_subject):
    content = "<section id='s'><p>{{TITLE}} and <!-- @@ZONE:NAV@@ --> stay literal</p></section>"
    out = built(build_guide.build(str(make_subject(content=content))))
    assert "{{TITLE}} and <!-- @@ZONE:NAV@@ --> stay literal" in out


@pytest.mark.parametrize("data, message", [
    ({"mcqData": [{"q": "q", "opts": ["a", "b"], "ans": 2, "exp": "e"}]}, "mcqData[0].ans 2 is out of range"),
    ({"mcqData": [{"q": "q", "opts": ["a", "b"], "answer": 0, "exp": "e"}]}, "mcqData[0].answer is not a known field"),
    ({"mcqData": [{"q": "q", "opts": ["a"], "ans": 0, "exp": "e"}]}, "at least 2"),
    ({"flashcards": [{"front": "f"}]}, "flashcards[0].back is missing"),
    ({"termLexicon": [{"keys": [], "term": "t"}]}, "keys must be a non-empty list"),
    ({"psycDict": []}, "data.psycDict is not a known array"),
])
def test_invalid_data_is_rejected_with_its_location(make_subject, data, message):
    with pytest.raises(build_guide.BuildError, match=re.escape(message)):
        build_guide.build(str(make_subject(data=data)))


def test_every_problem_is_reported_at_once(make_subject):
    data = {"flashcards": [{"front": ""}], "mcqData": [{"q": "q", "opts": ["a", "b"], "ans": "1", "exp": "e"}]}
    with pytest.raises(build_guide.BuildError) as e:
        build_guide.build(str(make_subject(data=data, config={"doc_id": "has space"})))
    msg = str(e.value)
    for part in ("doc_id", "flashcards[0].front", "flashcards[0].back", "mcqData[0].ans must be int"):
        assert part in msg


def test_legacy_data_js_points_to_the_migration_script(make_subject):
    subject = make_subject()
    os.remove(subject / "data.json")
    (subject / "data.js").write_text("const flashcards = [];", encoding="utf-8")
    with pytest.raises(build_guide.BuildError, match="migrate_datajs.py"):
        build_guide.build(str(subject))


def test_build_all_continues_after_a_failure(make_subject, capsys):
    good = make_subject("good")
    bad = make_subject("bad", config={"output": "../escape.html"})
    assert build_guide.main([str(bad), str(good)]) == 1
    assert (good / "Binary_Search_Demo.html").exists()
    assert "1/2 subjects OK" in capsys.readouterr().out


def test_migrate_datajs_keeps_known_arrays_only(tmp_path):
    (tmp_path / "data.js").write_text(
        "        const flashcards = [{front:'f',back:'b'}];\n"
        "  const mcqData = [ {q:\"q\",opts:[\"a\",\"b\"],ans:1,exp:\"e\"} ];\n"
        "const termLexicon = [];\nconst psycDict = [{term:'old'}];\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(FRAMEWORK, "migrate_datajs.py"), str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "dropped: psycDict" in r.stdout
    data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert data == {"flashcards": [{"front": "f", "back": "b"}],
                    "mcqData": [{"q": "q", "opts": ["a", "b"], "ans": 1, "exp": "e"}], "termLexicon": []}
