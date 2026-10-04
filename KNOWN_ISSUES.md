# Known issues and roadmap

Found during a review of the engine as it was used for real course guides. Each item names where the problem lives so it can be picked up as its own change, ideally with a failing test first.

## Bugs

1. **Highlights and notes that span inline markup are lost on reload.**
   Selecting text that fully contains a `<strong>` or a term `<span>` succeeds and reports "saved", but `highlightTextInElement` / `wrapNoteAnchorInElement` only search inside a single text node, so the stored record can never be re-anchored. Terms are wrapped in spans throughout the content, so this is common.
   Plan: store a text-position selector (character offsets within the container) plus a text-quote selector (exact text with a little prefix/suffix), as in the W3C Web Annotation model, and wrap a range that may cross nodes.

2. **MCQ options are rendered in authored order.**
   Any pattern in how questions were written (in the original guides, up to 91% of correct answers were option B, and the correct option was the longest one 83–92% of the time) is passed straight to the student.
   Plan: shuffle options per question in `initMCQ` and map `ans` through the permutation; the data contract stays the same.

3. **Placeholders are not escaped for their context.**
   `{{TITLE}}` and `{{SIDEBAR_TITLE}}` are inserted raw into HTML, and `{{SIDEBAR_TITLE}}` also into a JS string literal in `copyNotesAsMarkdown`. A `"` or `<` in a title breaks the page.
   Plan: `html.escape` for HTML positions, `json.dumps` for JS positions.

4. **Corrupted `localStorage` stops initialisation.**
   `restoreHighlights` and the export path call `JSON.parse` without a guard; one bad value halts `initApp` before notes and term cards are set up.

5. **JSON export may not download in some browsers.**
   `exportStudyData` revokes the object URL immediately after `a.click()`.

6. **Print answer key only has letters A–D.**
   A question with more than four options prints `undefined` as its letter.

## Tooling gaps

7. **`data.js` is parsed with a regex** that requires each array to close with exactly eight spaces before `];`. Plan: move to JSON with a schema check.
8. **`build_guide.py --all --validate` stops at the first failing subject**, so later subjects are neither built nor reported.
9. **The validator does not check teaching quality**: answer-position distribution, correct-option length bias, question count per lesson, or authoring labels leaking into student-facing text. These were the most impactful problems in practice and all passed validation.
10. **No automated tests or CI yet.**

## Structure

11. `framework/template.html` is a ~2,200-line single file holding all CSS and JS. Plan: split into modules under `src/` and concatenate at build time, keeping the output a single dependency-free file.
12. UI strings are hard-coded in Simplified Chinese; there is no i18n layer.

## Roadmap

| Phase | Goal |
|---|---|
| 1 | Test-first fixes for 1–2 (Playwright), then 3–6 |
| 2 | Restructure: `src/` modules, JSON data + schema, a small CLI (`new` / `build` / `validate`), teaching-quality checks (9) |
| 3 | Optional, pluggable study assistant (OpenAI-compatible endpoint or a local model), off by default, so the offline core stays dependency-free |
| 4 | CI, a live demo on GitHub Pages, architecture notes |
