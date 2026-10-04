# lecture-workbench

Turn lecture notes into a **single, self-contained HTML study guide** that works offline: double-click the file and you get highlights, margin notes, term cards, flashcards and practice questions, with no server, no CDN and no install.

> Status: **early alpha**. I built this for my own university courses and am now extracting it into a reusable tool. The page UI is currently in Simplified Chinese. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for what is still broken and what is planned.

## What you get

A subject folder (`config.json` + `content.html` + `data.js`) builds into one `.html` file with:

- **Highlighter and margin notes** anchored to the text, saved in `localStorage`, exportable/importable as JSON and copyable as Markdown
- **Term cards** on hover: IPA, stressed syllable chunks, etymology, a memory hook, and pronunciation through the Web Speech API
- **Flashcards** (keyboard: Space / ← / →) and **multiple-choice questions** with explanations
- **Teaching components** for structuring a lesson: chapter spine, evidence / limitation / misconception / transfer blocks, study cards
- **Print mode** that forces a light theme and appends a self-test sheet (flashcards + MCQ answer key)
- Dark mode, collapsible sidebar, reading progress, `focus-visible` and `prefers-reduced-motion` support

Each guide derives all of its `localStorage` keys from a per-subject `doc_id`, so many guides can be opened from the same origin without overwriting each other's notes.

## Quick start

Requirements: Python 3.9+ and Node.js (the validator uses `node --check` and runs the term-card audit in Node).

```bash
git clone https://github.com/JoshuaViolet/lecture-workbench.git
cd lecture-workbench
python3 framework/build_guide.py --all --validate
open subjects/demo-binary-search/Binary_Search_Demo.html
```

To build one subject:

```bash
python3 framework/build_guide.py subjects/demo-binary-search --validate
```

## How it works

```
framework/
  template.html        engine: all CSS, all runtime JS, HTML skeleton with {{PLACEHOLDERS}} and @@ZONE@@ markers
  build_guide.py       fills the template from a subject folder and writes one HTML file
  validate_guide.py    checks the generated file (see below)
examples/
  teaching-components.html   copy-paste snippets for the teaching blocks
subjects/
  demo-binary-search/  an original demo subject
    config.json        doc_id, app_id, title, sidebar text, header_html, nav_html, output
    content.html       the lesson body (<section>s inside <main>)
    data.js            flashcards, mcqData, termLexicon
```

The build fails if any placeholder is left unfilled. The validator then checks the output:

- every `href="#…"` anchor has a target, every `getElementById` has a static element, every inline handler has a function
- HTML tags are balanced and the page script passes `node --check`
- no raw LaTeX in visible text or data (the page has no math renderer)
- every referenced image under `assets/` exists
- every English term in `span.en` / `<strong>` has a term card, unless it is listed in the subject's `lexicon_allowlist.txt`

## Writing a subject

Data shapes in `data.js` (field names are a fixed contract):

```js
flashcards  : [{ front, back }]
mcqData     : [{ q, opts[], ans, exp }]       // ans = 0-based index of the correct option
termLexicon : [{ keys[], term, ipa, chunks, parts, hook }]
```

Bilingual terms in `content.html` get a hover card when written as:

```html
<span class="term"><span class="en">Binary search</span> <span class="zh">(二分查找)</span></span>
```

Pick a `doc_id` that is unique across all your guides and never change it afterwards: it namespaces the stored highlights and notes.

## License

[MIT](LICENSE)

---

中文简介：把讲义变成离线可用的单文件交互式学习页（高亮、批注、术语卡、抽认卡、选择题、打印自测）。目前处于早期版本，界面为简体中文。
