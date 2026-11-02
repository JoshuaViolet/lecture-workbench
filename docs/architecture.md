# Architecture

lecture-workbench is a small static-site generator with a single target: one HTML file per lecture that a student can open from disk, with no network access, and that keeps their own annotations.

## Constraints that shaped the design

1. **One file, zero runtime dependencies.** The guide must work from `file://`, offline, years later, and it must still work when it is the only file a student has (emailed, downloaded, copied to a phone). No CDN, no framework, no web fonts, no math renderer. All CSS, JS and images are inlined.
2. **The student's data lives in their browser.** There is no account or server. Highlights and notes go into `localStorage`, so they must never be lost silently, and they must survive the author editing and rebuilding the guide.
3. **Authors make mistakes.** Course content is written by hand (or with AI help) and is long. The build has to reject malformed data before it reaches a student, and point at the exact problem.

## Build pipeline

```
config.json ─┐
content.html ├─► build_guide.py ──► <output>.html ──► validate_guide.py
data.json    │        ▲             (one file: CSS, JS
assets/* ────┘        │              and images inside)
                      └── framework/template.html + framework/src/{css,js}/*
```

The engine is split into a page skeleton and modules:

- `framework/template.html` is the HTML skeleton. It decides the order of everything: each CSS and JS module is pulled in by a marker on a line of its own, `/* @@INCLUDE:css/print.css@@ */` or `// @@INCLUDE:js/notes.js@@`.
- `framework/src/css/*.css` and `framework/src/js/*.js` are the modules, one per part of the page (sidebar, annotations, term cards, print, …). They are plain CSS and JS with no markers or placeholders, so they can be read and edited like ordinary source files.

The builder first pastes each module in place of its marker, indented like the marker, so the output is still one dependency-free file. A module that is missing, included twice or not included at all fails the build. Order matters: CSS later in the skeleton wins the cascade, and all JS modules share one script scope, so they call each other's functions directly.

All holes stay in `template.html`. It has two kinds:

- **Placeholders** `{{NAME}}` for short values from `config.json`. Each is escaped for the context it lands in: HTML text, an HTML attribute, or a JavaScript literal (`json.dumps`, plus `</` → `<\/` so a string can never close the `<script>` element).
- **Zones** `@@ZONE:NAME@@` for whole files: the content body, header and nav HTML, optional subject CSS/JS, and the three data arrays.

Interface strings are placeholders too: `{{UI:key}}` in the HTML is filled from `framework/ui_strings.json` in the language set by `config.lang` (Chinese by default), and the same table is injected as `const UI = {...}` for messages built at runtime. Placeholders are filled first. Zones are then filled in **one regex pass**, so text inserted from `content.html` or `data.json` is never scanned again. Previously the replacements ran one after another over the whole output: placeholder-like text inside `header_html` was substituted, and a lesson that mentioned `{{TITLE}}` was rejected by the leftover check.

Placeholders are filled in one regex pass as well, so a config value that happens to contain `{{TITLE}}` is inserted as written.

Data used to be JavaScript source (`data.js`) cut out with a regex that depended on exact indentation. It is now JSON, checked against a schema in `build_guide.py`. The checker collects **every** problem with its location (`mcqData[3].ans 4 is out of range for 4 options`) instead of stopping at the first one, which matters when an AI assistant generated forty questions at once.

### Images

A lesson refers to its images by relative path (`<img src="assets/s12.png">`), which is convenient to write but would make the guide depend on a folder next to it. The builder therefore embeds every local image as a `data:` URI: `<img src>` in `content.html`, `header_html` and `nav_html`, `url()` in `subject_css.css`, and `<img>` inside the HTML fields of the data (`mcqData[].exp`, `termLexicon[].parts`), which reach the page through `innerHTML`. Comments and the contents of `<script>`, `<style>` and `<textarea>` are left alone, so a commented-out figure does not need its file. A missing file, or a file that is not an image type browsers display, fails the build, with every problem listed at once. `"embed_images": false` in `config.json` keeps the links, for a guide that will always travel with its `assets/` folder.

Embedding costs about a third more bytes than the image files (base64). The build prints each guide's size and warns above 25 MB, which phones open slowly; a 30 MB test guide with 40 slides parses in about half a second in desktop Chromium. An image used twice is embedded twice.

The validator checks the result from the other side: it lists every URL the page would load by itself (`src`, `srcset`, `poster`, `<object data>`, the `href` of `<link>` and SVG `<image>`/`<use>`, CSS `url()` and `@import`, including in the data's HTML) A local file that does not exist fails. Anything from the network is a warning, not a failure, also under `--strict`: the guide still opens and works, but those resources are missing offline, and authors sometimes accept that (an embedded video, say). The same goes for local files the guide needs beside it. An `<a href>` is a link, not a load, so linking to online material raises nothing.

## Runtime

The engine is plain DOM code run once at the end of `<body>`:

| Part | What it does |
|---|---|
| storage | `lsGet` / `lsSet` / `readList` / `writeList`, and `changeList` / `mergeById` for annotation lists (below). Every `localStorage` access is guarded; all keys derive from `DOC_ID`, so many guides can share an origin |
| annotations | highlights and margin notes (below) |
| practice | flashcards, MCQ with per-render option shuffling, an optional code block and remembered results, collapsible inline checks |
| term cards | builds an index from `termLexicon` keys and attaches hover cards to `span.en` and `<strong>` text that matches |
| layout | sidebar collapse, colour theme, contents marker, progress bar, lightbox for figure images, a scrolling box around each table |
| print | `beforeprint` builds a self-test appendix and forces lazy images to load |

The theme is a setting with three values: follow the system (the default; nothing is stored), light or dark (stored under `<DOC_ID>_theme`). It is the one exception to "run once at the end of `<body>`": a few lines in `<head>` apply it before the first paint, because applying it at the end of `<body>` showed dark-mode readers a white page first. The main script then keeps following the system's `prefers-color-scheme` while the setting is "system", so a device that switches to dark in the evening takes an open guide with it.

### Anchoring annotations

The hard problem is putting a highlight back in the right place after a reload, when the selection may cross inline elements and the author may have edited the page since.

The first version stored only the selected text and, on reload, searched for it inside a single text node. Any selection that crossed a `<strong>` or a term `<span>` was saved but could never be restored. Because terms are wrapped in spans throughout the content, this happened to ordinary selections, and the toast still said "saved".

An annotation is now stored as

```js
{ id, cIdx, start, end, text, prefix, suffix }
```

- `cIdx`: which block (`p`, `li`, `td`, headings, …) it is in, by document order
- `start`, `end`: character offsets into that block's text
- `text`, `prefix`, `suffix`: the exact text plus 32 characters of context on each side

This combines the two most common selectors of the W3C Web Annotation model: a TextPosition selector (fast, exact, fragile) and a TextQuote selector (robust to edits). To restore:

1. If the block at `cIdx` still has `text` at `[start, end)`, use it.
2. Otherwise search every block for `text`, score each occurrence (+2 for a matching prefix, +2 for a matching suffix, +1 for being in the original block) and take the best.

To display it, walk the text nodes inside `[start, end)`, split the first and last one at the boundaries, and wrap **each piece** in its own `<mark>` (or note `<span>`). All pieces share one id, so they are clicked, removed and exported as one annotation. Wrapping piece by piece keeps the DOM valid; wrapping the whole range in one element (`Range.surroundContents`) throws as soon as the range partially contains an element.

The 💬 flag added after a note is excluded from the text model, so adding a note never shifts the offsets of other annotations. Records in the old `{ cIdx, text }` format still restore, through step 2.

Known trade-off: an annotation lives inside one block. A selection that runs into the next paragraph keeps the part in the first block and the toast says so.

### Not losing student data

- An unreadable `localStorage` value is copied to `<key>_unreadable` before anything overwrites it, and the page still starts.
- A failed write (storage full or blocked) is reported instead of ignored, and the page keeps its own copy of every annotation list, so an export still contains what could not be stored. (The message about a failed write tells the student to export; before, export read only from storage and exported nothing.)
- Every change re-reads the stored list, applies one change (add, edit or remove one record) and writes it back. Writing back a copy loaded at start-up, as notes once did, erased whatever another tab of the same guide had saved meanwhile.
- Importing a backup into a browser that already has annotations asks first, in a dialog that shows how many highlights and notes the backup and the browser each hold. **Merge** (the default button) matches records by id: nothing in the browser is removed, the more recently edited version of a note wins, and a highlight on the same text (same quote and context) is not added twice. **Replace** makes the browser hold exactly the backup, after keeping one copy of what it replaces under `<key>_before_import`. Import used to replace without asking, so a backup from one device wiped out the annotations made on another. A browser with nothing yet gets the backup without a question; a backup from another guide is always flagged in the dialog.
- Clicking outside the note editor saves a changed draft instead of discarding it; Cancel and Escape discard on purpose.
- Backups carry the guide's `app_id`; importing a backup from another guide asks first. Imported records are checked one by one.

### Remembered practice results

Each question's last result (right or wrong, with a time) is stored under `<DOC_ID>_mcq_results_v1`, keyed by a hash of the stem and the code, not by position: an author adding or reordering questions keeps the records, and editing a stem starts that question afresh. A question answered wrongly last time carries a badge, and a button narrows the set to those questions; the set is fixed while practising, so answering one correctly does not make it vanish mid-session. These results are a convenience: they are not part of the JSON backup, and a failed write is not reported.

### Why shuffle MCQ options at runtime

In the guides this tool was built for, the correct option was B in up to 91% of questions and the longest option in 83–92%: habits of whoever wrote the questions. Shuffling at build time would fix one order into the file; shuffling on every render means a student can't memorise positions even after several attempts. Buttons carry their authored index in `data-opt`, so scoring follows the answer, not the position. The validator separately warns when the correct option is usually the longest, because shuffling can't hide that.

## Testing

- `tests/test_build.py`, `tests/test_validate.py`: the builder and validator, including escaping, schema errors and lint.
- `tests/test_engine.py`, `tests/test_annotations.py`: Playwright opens the built demo from `file://` and drives it the way a student would: select text, click the toolbar, reload, remove, work in two tabs, export a backup and merge it into, or replace, another browser profile's annotations, answer questions and come back, open the guide after copying it alone into an empty folder. These include regression tests for each bug above; they fail on the previous engine.

CI runs both on Python 3.9 and 3.12. A second workflow publishes the demo to GitHub Pages.
