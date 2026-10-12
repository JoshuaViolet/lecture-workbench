import json
import os

import pytest

from conftest import DEMO, build_guide  # conftest also puts framework/ on sys.path

import cli  # noqa: E402


def test_new_scaffolds_a_subject_that_builds_and_passes_strict_validation(tmp_path, capsys):
    subject = tmp_path / "my-lecture"
    assert cli.main(["new", str(subject)]) == 0
    assert sorted(os.listdir(subject)) == ["config.json", "content.html", "data.json"]
    cfg = json.loads((subject / "config.json").read_text(encoding="utf-8"))
    assert {k: cfg[k] for k in ("doc_id", "app_id", "title", "output")} == {
        "doc_id": "my_lecture", "app_id": "my-lecture-guide", "title": "My Lecture", "output": "My_Lecture.html"}

    assert cli.main(["build", str(subject), "--validate", "--strict"]) == 0
    assert (subject / "My_Lecture.html").exists()
    capsys.readouterr()
    assert cli.main(["validate", str(subject), "--strict"]) == 0
    assert "VALIDATE OK" in capsys.readouterr().out


def test_new_uses_given_title_and_ids_and_escapes_the_title(tmp_path):
    subject = tmp_path / "线性代数"
    assert cli.main(["new", str(subject), "--title", "线性代数 <A&B>", "--doc-id", "linalg",
                     "--output", "Linalg.html"]) == 0
    cfg = json.loads((subject / "config.json").read_text(encoding="utf-8"))
    assert (cfg["doc_id"], cfg["output"], cfg["title"]) == ("linalg", "Linalg.html", "线性代数 <A&B>")
    assert "<h1>线性代数 &lt;A&amp;B&gt;</h1>" in cfg["header_html"]
    build_guide.build(str(subject))


@pytest.mark.parametrize("args, message", [
    (["--doc-id", "has space"], "may only contain letters"),
    (["--output", "../escape.html"], "must be a plain *.html file name"),
])
def test_new_rejects_bad_options_without_writing(tmp_path, capsys, args, message):
    subject = tmp_path / "lecture"
    assert cli.main(["new", str(subject), *args]) == 1
    assert message in capsys.readouterr().out
    assert not subject.exists()


def test_new_needs_ids_when_the_folder_name_has_no_latin_letters(tmp_path, capsys):
    assert cli.main(["new", str(tmp_path / "线性代数")]) == 1
    assert "pass --doc-id and --output" in capsys.readouterr().out


def test_new_refuses_a_non_empty_folder(tmp_path, capsys):
    subject = tmp_path / "lecture"
    subject.mkdir()
    (subject / "notes.txt").write_text("keep me", encoding="utf-8")
    assert cli.main(["new", str(subject)]) == 1
    assert "not empty" in capsys.readouterr().out
    assert os.listdir(subject) == ["notes.txt"]


def test_new_refuses_a_doc_id_another_subject_uses(tmp_path, capsys):
    assert cli.main(["new", str(tmp_path / "week-1")]) == 0
    assert cli.main(["new", str(tmp_path / "week-1-copy"), "--doc-id", "week_1"]) == 1
    assert "already used" in capsys.readouterr().out
    demo_id = json.loads(open(os.path.join(DEMO, "config.json"), encoding="utf-8").read())["doc_id"]
    assert cli.main(["new", str(tmp_path / "elsewhere"), "--doc-id", demo_id]) == 1


def test_build_reports_every_subject_and_fails_if_one_fails(make_subject, capsys):
    good = make_subject("good")
    bad = make_subject("bad", config={"doc_id": "has space"})
    assert cli.main(["build", str(bad), str(good)]) == 1
    out = capsys.readouterr().out
    assert "BUILD FAILED" in out and "1/2 subjects OK" in out
    assert (good / "Binary_Search_Demo.html").exists()


def test_build_needs_subjects_or_all(make_subject, capsys):
    assert cli.main(["build"]) == 2
    assert cli.main(["build", "--all", str(make_subject())]) == 2


def test_validate_accepts_a_guide_file(demo_guide, capsys):
    assert cli.main(["validate", demo_guide]) == 0
    assert "VALIDATE OK" in capsys.readouterr().out


def test_validate_explains_an_unbuilt_subject_or_missing_file(make_subject, tmp_path, capsys):
    subject = make_subject()
    assert cli.main(["validate", str(subject)]) == 1
    assert "has not been built yet" in capsys.readouterr().out
    assert cli.main(["validate", str(tmp_path / "nope.html")]) == 1
    assert "does not exist" in capsys.readouterr().out


def test_no_command_prints_help(capsys):
    assert cli.main([]) == 2
    assert "new" in capsys.readouterr().out


def test_build_strict_turns_lint_warnings_into_failures(make_subject):
    lexicon = json.loads(open(os.path.join(DEMO, "data.json"), encoding="utf-8").read())["termLexicon"]
    mcq = [{"q": f"q{i}", "opts": ["short", "the much longer and more careful answer", "tiny", "no"],
            "ans": 1, "exp": "e"} for i in range(5)]
    subject = str(make_subject(data={"mcqData": mcq, "termLexicon": lexicon}))
    assert cli.main(["build", subject, "--validate"]) == 0
    assert cli.main(["build", subject, "--validate", "--strict"]) == 1
