# lecture-workbench

[![CI](https://github.com/JoshuaViolet/lecture-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/JoshuaViolet/lecture-workbench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Turn lecture notes into a **single, self-contained HTML study guide** that works offline. Double-click the file and you get highlights, margin notes, term cards, flashcards and practice questions: no server, no CDN, no install.

**[Live demo](https://joshuaviolet.github.io/lecture-workbench/)** · [架构说明 / Architecture](docs/architecture.md) · [中文说明](README.zh-CN.md)

![A demo guide with a highlight across bold text, a margin note and a term card](docs/screenshot.png)

> Status: **v0.2, early**. I built this for my own university courses and extracted it into a reusable tool. The page interface comes in Simplified Chinese (default) or English. Open problems are listed in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Features

- **Highlights and margin notes** that survive reloads, even when the selection crosses bold text or other inline markup. Stored per guide in `localStorage`; export/import as JSON, or copy as Markdown.
- **Term cards** on hover: IPA, stressed syllables, etymology, a memory hook, and pronunciation through the Web Speech API.
- **Flashcards** and **multiple-choice questions** with explanations. Options are shuffled on every render so the position of the answer can't be learned instead of the content.
- **Teaching components** for structuring a lesson: chapter spine, evidence / limitation / misconception / transfer blocks, study cards.
- **Print mode** that forces a light theme and appends a self-test sheet with the answer key.
- Dark mode, collapsible sidebar, reading progress, keyboard support, `prefers-reduced-motion`.

## Quick start

Requires Python 3.9+ and Node.js (the validator uses Node to syntax-check the page and audit term cards).

```bash
git clone https://github.com/JoshuaViolet/lecture-workbench.git
cd lecture-workbench
python3 framework/cli.py build --all --validate
open subjects/demo-binary-search/Binary_Search_Demo.html
```

## Commands

`framework/cli.py` has three subcommands:

```bash
python3 framework/cli.py new subjects/my-lecture --title "My Lecture"   # scaffold a subject
python3 framework/cli.py build subjects/my-lecture --validate           # build, then check the page
python3 framework/cli.py validate subjects/my-lecture --strict          # check an already built page
```

| Command | Does |
|---|---|
| `new <dir> [--title T] [--doc-id ID] [--output NAME.html]` | Creates `config.json`, `content.html` and `data.json` with one example of each part (section, term card, flashcard, question). The result builds and passes `--strict` as is. Ids and the output name come from the folder name unless given; `new` refuses a folder that is not empty and a `doc_id` another subject under the same parent or `subjects/` already uses. |
| `build (<dir>... \| --all) [--validate] [--strict]` | Builds each subject into its single-file guide and keeps going after a failure. `--all` builds every folder with a `config.json` under `subjects/`. |
| `validate (<dir> \| <guide.html>) [--strict]` | Runs the checks below on a built guide. Given a subject folder, it checks the file named by `config.output`. |

Every command exits non-zero on failure, so they work in CI. `framework/build_guide.py` and `framework/validate_guide.py` still run on their own with the same flags.

## Writing a subject

A subject is a folder under `subjects/` (`cli.py new` creates one):

```
subjects/my-lecture/
  config.json      identity, titles, header and table-of-contents HTML, output file name
  content.html     the lesson body: <section>s with your text, figures and components
  data.json        flashcards, mcqData, termLexicon
  assets/          images referenced from content.html (optional)
```

`config.json`:

```json
{
  "doc_id": "my_lecture",
  "app_id": "my-lecture-guide",
  "title": "My Lecture",
  "output": "My_Lecture.html",
  "lang": "en",
  "header_html": "<header class=\"doc-header\"><h1>My Lecture</h1></header>",
  "nav_html": "<li><a href=\"#intro\">Introduction</a></li>"
}
```

`doc_id` namespaces everything the guide stores, so it must be unique across your guides and must not change after you start using a guide.

`lang` sets the language of the page's own interface (toolbar, sidebar, messages, print sheet): `"zh"` for Simplified Chinese (the default) or `"en"` for English. Your lesson content is written in whatever language you like. The strings live in [`framework/ui_strings.json`](framework/ui_strings.json); to add a language, add a table with the same keys.

`data.json` (checked at build time; errors point at the exact item and field):

```json
{
  "flashcards":  [{ "front": "…", "back": "…" }],
  "mcqData":     [{ "q": "…", "opts": ["…", "…", "…", "…"], "ans": 2, "exp": "…" }],
  "termLexicon": [{ "keys": ["binary search"], "term": "Binary search 二分查找",
                    "ipa": "/ˈbaɪnəri sɜːtʃ/", "chunks": "BI-na-ry SEARCH",
                    "parts": "…", "hook": "…" }]
}
```

`ans` is the 0-based index of the correct option in `opts`. Add `"shuffle": false` to a question whose options must stay in order. A term in `content.html` gets a hover card when it is written as

```html
<span class="term"><span class="en">Binary search</span> <span class="zh">(二分查找)</span></span>
```

or as `<strong>…</strong>` text that matches one of the `keys`. Copy-paste snippets for the teaching components are in [examples/](examples/).

Coming from the older `data.js` format: `python3 framework/migrate_datajs.py subjects/<name>`.

## Validation

`cli.py build --validate` (or `cli.py validate`) checks the generated page:

| Check | Catches |
|---|---|
| structure | broken `#anchors`, `getElementById` targets that don't exist, undefined inline handlers, unbalanced tags, unfilled placeholders, script syntax errors |
| content | raw LaTeX (there is no math renderer), missing images, English terms with no term card |
| teaching-quality lint | the correct option being the longest one in most questions, answers clustered on one letter, duplicate questions |

Lint findings are warnings; `--strict` turns them into failures.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium   # or set PW_CHANNEL=chrome to use an installed Chrome
.venv/bin/pytest
```

The suite has unit tests for the builder and validator, and Playwright tests that open the built demo from `file://` and drive it like a student: select text, click the toolbar, reload, export and import a backup.

## License

[MIT](LICENSE)

## Acknowledgments

Developed with AI assistance (Claude).
