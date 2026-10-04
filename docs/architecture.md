# Architecture

lecture-workbench is a small static-site generator with a single target: one HTML file per lecture that a student can open from disk, with no network access, and that keeps their own annotations.

## Constraints that shaped the design

1. **One file, zero runtime dependencies.** The guide must work from `file://`, offline, years later. No CDN, no framework, no web fonts, no math renderer. All CSS and JS are inlined.
2. **The student's data lives in their browser.** There is no account or server. Highlights and notes go into `localStorage`, so they must never be lost silently, and they must survive the author editing and rebuilding the guide.
3. **Authors make mistakes.** Course content is written by hand (or with AI help) and is long. The build has to reject malformed data before it reaches a student, and point at the exact problem.

## Build pipeline

```
config.json ─┐
content.html ├─► build_guide.py ──► <output>.html ──► validate_guide.py
data.json ───┘        ▲
                      └── framework/template.html
```

`template.html` holds the whole engine: CSS, runtime JS and the HTML skeleton. It has two kinds of holes:

- **Placeholders** `{{NAME}}` for short values from `config.json`. Each is escaped for the context it lands in: HTML text, an HTML attribute, or a JavaScript literal (`json.dumps`, plus `</` → `<\/` so a string can never close the `<script>` element).
- **Zones** `@@ZONE:NAME@@` for whole files: the content body, header and nav HTML, optional subject CSS/JS, and the three data arrays.

Placeholders are filled first. Zones are then filled in **one regex pass**, so text inserted from `content.html` or `data.json` is never scanned again. Previously the replacements ran one after another over the whole output: placeholder-like text inside `header_html` was substituted, and a lesson that mentioned `{{TITLE}}` was rejected by the leftover check.

Data used to be JavaScript source (`data.js`) cut out with a regex that depended on exact indentation. It is now JSON, checked against a schema in `build_guide.py`. The checker collects **every** problem with its location (`mcqData[3].ans 4 is out of range for 4 options`) instead of stopping at the first one, which matters when an AI assistant generated forty questions at once.

## Runtime

The engine is plain DOM code run once at the end of `<body>`:

| Part | What it does |
|---|---|
| storage | `lsGet` / `lsSet` / `readList` / `writeList`. Every `localStorage` access is guarded; all keys derive from `DOC_ID`, so many guides can share an origin |
| annotations | highlights and margin notes (below) |
| practice | flashcards, MCQ with per-render option shuffling, collapsible inline checks |
| term cards | builds an index from `termLexicon` keys and attaches hover cards to `span.en` and `<strong>` text that matches |
| layout | sidebar collapse, dark mode, progress bar, lightbox |
| print | `beforeprint` builds a self-test appendix and forces lazy images to load |

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
- A failed write (storage full or blocked) is reported instead of ignored.
- Backups carry the guide's `app_id`; importing a backup from another guide asks first. Imported records are checked one by one.

### Why shuffle MCQ options at runtime

In the guides this tool was built for, the correct option was B in up to 91% of questions and the longest option in 83–92%: habits of whoever wrote the questions. Shuffling at build time would fix one order into the file; shuffling on every render means a student can't memorise positions even after several attempts. Buttons carry their authored index in `data-opt`, so scoring follows the answer, not the position. The validator separately warns when the correct option is usually the longest, because shuffling can't hide that.

## Testing

- `tests/test_build.py`, `tests/test_validate.py`: the builder and validator, including escaping, schema errors and lint.
- `tests/test_engine.py`, `tests/test_annotations.py`: Playwright opens the built demo from `file://` and drives it the way a student would: select text, click the toolbar, reload, remove, export a backup and import it into a fresh browser profile. These include regression tests for each bug above; they fail on the previous engine.

CI runs both on Python 3.9 and 3.12. A second workflow publishes the demo to GitHub Pages.
