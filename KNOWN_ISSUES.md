# Known issues and roadmap

Fixed issues are recorded in [CHANGELOG.md](CHANGELOG.md). This file lists what is still open.

## Limitations

1. **An annotation stays inside one block.** A selection that runs from one paragraph into the next keeps only the part in the first paragraph (the page says so). Supporting multi-block annotations means storing a start and end block and wrapping across them.
2. **Restoring is O(blocks × annotations) when offsets are stale.** Fine for a lecture with hundreds of annotations; a very long page with thousands could be slow on first load after an edit.
3. **The UI is Simplified Chinese only.** Strings are hard-coded in `template.html`; there is no i18n layer yet.
4. **The validator needs Node.js** for `node --check` and the term-card audit. Building does not.

## Structure

5. `framework/template.html` is a ~2,300-line single file holding all CSS and JS. Plan: split it into modules under `src/` and concatenate at build time, keeping the output one dependency-free file.
6. The build is a script, not an installable tool. Plan: a small CLI (`new`, `build`, `validate`) published as a package.

## Roadmap

| Next | Goal |
|---|---|
| 0.2 | Split the template into modules; CLI; `new` command that scaffolds a subject |
| 0.3 | UI string table with English and Chinese |
| later | Optional, pluggable study assistant (OpenAI-compatible endpoint or a local model), off by default so the offline core stays dependency-free |
