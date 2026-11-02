import base64
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
    assert not re.search(r"\{\{[A-Z_]+\}\}|@@ZONE|@@INCLUDE", out)
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
    # the template's two scripts (theme in <head>, engine at the end of <body>), and no more
    assert len(scripts) == 2 and "<\\/script>" in scripts[1]


def test_content_text_is_never_treated_as_a_marker(make_subject):
    content = "<section id='s'><p>{{TITLE}} and <!-- @@ZONE:NAV@@ --> stay literal</p></section>"
    out = built(build_guide.build(str(make_subject(content=content))))
    assert "{{TITLE}} and <!-- @@ZONE:NAV@@ --> stay literal" in out


def make_framework(tmp_path, template, modules):
    fw = tmp_path / "framework"
    for name, text in modules.items():
        (fw / "src" / name).parent.mkdir(parents=True, exist_ok=True)
        (fw / "src" / name).write_text(text, encoding="utf-8")
    (fw / "template.html").write_text(template, encoding="utf-8")
    return str(fw)


def test_modules_are_pasted_at_their_marker_indent(tmp_path):
    fw = make_framework(tmp_path, "<style>\n    /* @@INCLUDE:css/a.css@@ */\n</style>\n"
                                  "<script>\n  // @@INCLUDE:js/b.js@@\n</script>\n",
                        {"css/a.css": "a {\n    color: red;\n}\n\nb {}\n", "js/b.js": "let x = 1;\n"})
    assert build_guide.assemble_template(fw) == ("<style>\n    a {\n        color: red;\n    }\n\n    b {}\n"
                                                 "</style>\n<script>\n  let x = 1;\n</script>\n")


def test_include_problems_are_all_reported(tmp_path):
    fw = make_framework(tmp_path, "/* @@INCLUDE:css/missing.css@@ */\n// @@INCLUDE:../escape.js@@\n"
                                  "// @@INCLUDE:js/holey.js@@\n",
                        {"css/unused.css": "a {}\n", "js/holey.js": "const t = {{TITLE}};\n"})
    with pytest.raises(build_guide.BuildError) as e:
        build_guide.assemble_template(fw)
    msg = str(e.value)
    for part in ("css/missing.css, which is not", "../escape.js, which is not",
                 "src/js/holey.js contains a marker", "src/css/unused.css is not included"):
        assert part in msg


@pytest.mark.parametrize("data, message", [
    ({"mcqData": [{"q": "q", "opts": ["a", "b"], "ans": 2, "exp": "e"}]}, "mcqData[0].ans 2 is out of range"),
    ({"mcqData": [{"q": "q", "opts": ["a", "b"], "answer": 0, "exp": "e"}]}, "mcqData[0].answer is not a known field"),
    ({"mcqData": [{"q": "q", "opts": ["a"], "ans": 0, "exp": "e"}]}, "at least 2"),
    ({"mcqData": [{"q": "q", "opts": ["a", "b"], "ans": 0, "exp": "e", "code": ["x = 1"]}]},
     "mcqData[0].code must be str"),
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


def test_sources_saved_with_a_byte_order_mark_and_windows_newlines_build(make_subject):
    subject = make_subject()
    for name in ("config.json", "data.json", "content.html"):
        path = subject / name
        path.write_bytes(path.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8-sig"))
    out = built(build_guide.build(str(subject)))
    assert "\ufeff" not in out and "\r" not in out


def test_a_source_in_another_encoding_is_reported_and_the_rest_still_build(make_subject, capsys):
    bad, good = make_subject("bad"), make_subject("good")
    content = (bad / "content.html").read_text(encoding="utf-8")
    (bad / "content.html").write_bytes(content.encode("gb18030"))   # GBK, as some Chinese editors save
    assert build_guide.build_many([str(bad), str(good)]) == 1
    out = capsys.readouterr().out
    line = next(i for i, text in enumerate(content.split("\n"), 1) if not text.isascii())
    assert f"content.html is not UTF-8 text (line {line} has bytes" in out and "save it as UTF-8" in out
    assert (good / "Binary_Search_Demo.html").exists() and "1/2 subjects OK" in out


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


PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def subject_with_images(make_subject, name="subject", config=None, content=None, data=None):
    subject = make_subject(name=name, config=config, data=data, content=content or (
        '<section id="s"><figure class="slide-fig"><img alt="a" src="assets/dot.png"></figure>'
        "<p><img src='assets/two%20words.png' alt=\"b\"> and <img src=\"https://example.com/remote.png\"></p>"
        '<!-- <img src="assets/old-figure-not-there.png"> -->'
        '<pre><code>&lt;img src="assets/escaped.png"&gt;</code></pre></section>'))
    (subject / "assets").mkdir(exist_ok=True)
    (subject / "assets" / "dot.png").write_bytes(PNG)
    (subject / "assets" / "two words.png").write_bytes(PNG)
    return subject


def test_local_images_are_embedded_so_the_guide_is_one_file(make_subject):
    subject = subject_with_images(make_subject)
    (subject / "subject_css.css").write_text(".x { background: url('assets/dot.png'); }", encoding="utf-8")
    out = built(build_guide.build(str(subject)))
    uri = "data:image/png;base64," + base64.b64encode(PNG).decode()
    assert out.count(f'src="{uri}"') == 2 and f'url("{uri}")' in out
    assert "assets/dot.png" not in out and "two%20words" not in out
    # what is not a local image in the page stays as written
    assert 'src="https://example.com/remote.png"' in out
    assert '<!-- <img src="assets/old-figure-not-there.png"> -->' in out
    assert '&lt;img src="assets/escaped.png"&gt;' in out


def test_images_in_question_explanations_are_embedded(make_subject):
    subject = subject_with_images(make_subject, data={"mcqData": [
        {"q": "q", "opts": ["a", "b"], "ans": 0, "exp": 'see <img src="assets/dot.png" alt="">'}]})
    out = built(build_guide.build(str(subject)))
    exp = json.loads(re.search(r"^\s*const mcqData = (\[.*\]);$", out, re.M).group(1))[0]["exp"]
    assert exp.startswith('see <img src="data:image/png;base64,')


def test_missing_and_unsupported_images_are_all_reported(make_subject):
    content = '<section id="s"><img src="assets/nope.png"><img src="assets/notes.pdf"></section>'
    subject = subject_with_images(make_subject, content=content)
    (subject / "assets" / "notes.pdf").write_bytes(b"%PDF-1.4")
    with pytest.raises(build_guide.BuildError) as e:
        build_guide.build(str(subject))
    msg = str(e.value)
    assert "content.html: image 'assets/nope.png' not found" in msg
    assert "content.html: cannot embed 'assets/notes.pdf'" in msg


def test_embed_images_false_keeps_the_links(make_subject):
    out = built(build_guide.build(str(subject_with_images(make_subject, config={"embed_images": False}))))
    assert 'src="assets/dot.png"' in out and 'src="data:' not in out


def test_embed_images_must_be_true_or_false(make_subject):
    with pytest.raises(build_guide.BuildError, match="config.embed_images must be true or false"):
        build_guide.build(str(make_subject(config={"embed_images": "yes"})))


def test_config_values_are_never_read_as_placeholders(make_subject):
    title = "Templates: {{TITLE}} and {{DOC_ID_JSON}}"
    out = built(build_guide.build(str(make_subject(config={"title": title, "sidebar_title": title}))))
    assert f"<title>{title}</title>" in out
    assert json.loads(re.search(r"const GUIDE_TITLE = (.*);", out).group(1)) == title


def test_build_reports_the_guide_size(make_subject, capsys):
    assert build_guide.main([str(make_subject())]) == 0
    assert re.search(r"BUILD OK .* -> Binary_Search_Demo\.html \(\d+ KB\)", capsys.readouterr().out)


def test_unknown_options_are_rejected(make_subject, capsys):
    assert build_guide.main([str(make_subject()), "--validte"]) == 2
    assert "unknown option --validte" in capsys.readouterr().out
