# Changelog

## Unreleased

### Added
- A question can show the diagram it is about: `"fig"` (an image in the subject's `assets/` folder) and `"fig_alt"` in `mcqData`. The build embeds the image; it appears under the stem, opens full size (also from the keyboard) and is printed with the answer key. A missing image, or a figure without `fig_alt`, fails the build.

### Changed
- The button of an inline check keeps the label its author wrote ("Hint", "Worked answer") and reads "Hide" (收起) while its answer is open. Before, the first click replaced every label with the same text, so a card with several steps could not tell them apart.

### Fixed
- The validator took questions with the same stem but different code ("What does this print?") for duplicates, which failed `--strict`. A duplicate is now the same stem, code and figure.

## 0.3.1

### Added
- The Release workflow can be started from the Actions page (**Run workflow** on `main`, with the version), so a release needs no git and can be made from a phone. It tags the head of `main` and publishes that version's changelog section.
- Where scripts do not run (some mail and file previews), the page says so, shows the answers to the inline checks and hides the controls that would do nothing. Before, it looked like a guide whose buttons were broken.

### Changed
- CI, the Pages deploy and the Release workflow use the versions of GitHub's own actions that run on Node 24 (checkout v7, setup-python v7, setup-node v7, configure-pages v6, upload-pages-artifact v5, deploy-pages v5), so runs no longer warn that Node 20 is deprecated.
- Printing opens collapsed `<details>` sections and closes them again afterwards, as it already showed the answers of the inline checks. A guide with neither flashcards nor questions prints no self-test sheet (it printed one saying "0 cards, 0 questions").
- Reading a term aloud reads only its English words: "Binary search", not "Binary search 二分查找".
- A saved highlight or note records `v`, the version of the list of block kinds its `cIdx` counts in, so that adding a kind of block (as this release does) moves no saved annotation. Records without it are read as version 1.

### Fixed
- Publishing a release by hand on the Releases page made the Release workflow fail and send a failure email: the release's new tag started the workflow, which then found the release already there. The workflow now leaves an existing release as it is.
- The chapter spine, study cards (`dt`, `dd`) and code blocks (`pre`) could not be highlighted or annotated: the page said the area was not supported.
- A highlight on a term could not be removed: clicking it opened only the term card. The highlight's toolbar now shows too, and the card makes room for it.
- A note whose text ended inside a term could not be opened: its 💬 flag opened the term card.
- In a guide with the English interface, the validator took bold text for terms, so emphasis such as `<strong>Remember this:</strong>` failed validation unless allow-listed. There, only text marked `span.en` needs a card.
- A source file saved with a UTF-8 byte-order mark, as some Windows editors do, failed the build ("Unexpected UTF-8 BOM"); one in another encoding, such as GBK, stopped it with a Python traceback, and stopped `build --all` there. A byte-order mark is now fine, and another encoding is reported with the line to look at while the other subjects still build.
- The message shown after saving covered the buttons under it for a few seconds; clicks now go through it.

### Upgrading
- Rebuild your subjects. Students' highlights and notes stay where they were, including short ones such as a single table cell.

## 0.3.0

### Added
- Local images are embedded in the built page as `data:` URIs, so a guide with figures is still one file that works when copied on its own. A missing image fails the build; `"embed_images": false` keeps the links. The build reports each guide's size and warns above 25 MB.
- An offline section in the validator: local files the page points to must exist; anything it would load from the network (CDN script, web font, hotlinked image, iframe) and files it needs beside it are reported as warnings, which `--strict` does not turn into failures.
- Figure images open full size in the lightbox (click or Enter). The demo has a figure of its search trace.
- Each question's last result is remembered in the browser; questions answered wrongly last time carry a badge, and a button narrows practice to them.
- The contents list marks the section being read.
- `cli.py new --lang en` writes an English starter subject.
- Ctrl/⌘+Enter saves a note.
- Pushing a `v*` tag publishes a GitHub release whose notes are that version's section of this changelog.

### Changed
- Importing a backup asks whether to **merge** it with what the browser already has (nothing is deleted, the newer edit of a note wins, and the page says when a backup holds nothing new) or **replace** it, showing how many highlights and notes each side has. A browser with nothing yet is not asked. Replacing keeps one copy of what it replaced under `<key>_before_import`. A backup from another guide is flagged in the same dialog instead of a separate confirm.
- The dark-mode button is now a theme setting in the sidebar: **follow the system** (the default, also when the system switches while the guide is open), light or dark. A reader who picked light or dark can go back to following the system. The theme is applied before the first paint, so dark-mode readers no longer see a white page first.
- On phones, tables scroll sideways inside their own box and the page uses less padding.
- Reading a term aloud picks an installed English voice (Australian first, as before) instead of leaving a non-English default voice to read it.
- The Markdown export lists notes and highlights in reading order and dates them in the guide's language.
- Without Node.js, the validator skips its two Node checks and says so, instead of crashing.
- CI and the Pages deploy use Node 24 (Node 20 is past end of life). CI's Python 3.9 job runs on Ubuntu 24.04, because `ubuntu-latest` is now Ubuntu 26.04, which has no Python 3.9.

### Fixed
- Importing a backup erased the annotations already in the browser, without asking.
- With the guide open in two tabs, saving a note in one erased notes saved in the other.
- Clicking outside the note editor threw away what had been typed.
- When storage writes failed, the export the message recommended contained nothing.
- A highlight inside a note could not be removed, and the toolbar's note button could annotate an earlier, abandoned selection.
- The validator took money ("$5 to $10") and code (R's `df$col`, `$HOME`) for raw LaTeX, failing economics and data-science guides; it missed `$x^2$` in the data.
- A term card showed "undefined" for a term without an etymology, and empty rows for other missing fields.
- Ctrl/⌘+[ (Back in macOS browsers) toggled the sidebar.
- Pasting into the contents filter did not filter.
- Printed highlights kept their background instead of turning into underlines.
- A config value containing `{{TITLE}}` or another placeholder name failed the build.
- ids and anchors in single quotes were not checked; mistyped options were silently ignored.

### Upgrading
- Rebuild your subjects. They build unchanged, except that every image `content.html` refers to is now embedded: built guides get bigger, and a missing image fails the build instead of showing up broken. Add `"embed_images": false` to `config.json` to keep the old links.
- A guide that loads something from the network (a CDN script, a web font, a hotlinked image) now gets a validator warning. It is not a failure, also with `--strict`.
- Students keep everything: highlights, notes and the theme use the same storage keys as before. A student who never chose a theme now follows the system; one who chose light or dark keeps that choice.

## 0.2.1

### Added
- Optional `code` field for multiple-choice questions: a monospace block under the stem, shown exactly as written. Options with a line break are shown as code. The print sheet includes the code.
- Writing rules for subject authors and AI assistants: [AGENTS.md](AGENTS.md), with supplements for psychology, economics and data science under `docs/writing/`.
- Validator warnings for question-type tags in stems and for explanations that refer to shuffled options by letter.

### Changed
- The validator now warns when the correct option is the only longest one in more than 40% of questions (was 50%). Picking the longest option scores about 25% by chance with four options.
- The demo has a predict-the-output question that uses `code`, and one answer was shortened so the demo stays under the new limit.

## 0.2.0

### Added
- English interface. Set `"lang": "en"` in a subject's `config.json`; the default stays Simplified Chinese. Interface strings moved out of `template.html` into `framework/ui_strings.json`, and the build checks that every language defines the same strings.
- `framework/cli.py` with `new` (scaffold a subject that builds and validates as is), `build` and `validate` subcommands.
- `build_guide.py --validate --strict` passes `--strict` on to the validator.

### Changed
- `framework/template.html` is now a page skeleton; the engine's CSS and JS live in modules under `framework/src/` and are inlined at build time. Built guides are unchanged, byte for byte.

## 0.1.0

First public version, extracted from a personal study-guide project.

### Changed
- The page no longer redirects `file://` opens to a local assistant server; guides work fully offline. The assistant and the unused local "AI engine" were removed.
- Subject data moved from `data.js` to `data.json`, validated against a schema at build time. `framework/migrate_datajs.py` converts old subjects.
- Flashcard and MCQ widgets are optional in `content.html`.

### Fixed
- Highlights and notes that crossed inline markup were reported as saved but lost on reload. Annotations are now anchored by text position plus quote with context.
- MCQ options were shown in authored order, so patterns such as "the answer is usually B" reached students. Options are now shuffled on every render.
- Titles were inserted unescaped into HTML and a JS string.
- An unreadable `localStorage` value stopped the page from initialising.
- The JSON export revoked its download URL immediately, which can cancel the download in some browsers.
- The print answer key showed `undefined` for questions with more than four options.
- `build_guide.py --all --validate` stopped at the first failing subject.

### Added
- Teaching-quality lint in the validator, with `--strict`.
- pytest + Playwright test suite, CI on Python 3.9 and 3.12, and a GitHub Pages deploy of the demo.
