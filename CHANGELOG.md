# Changelog

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
