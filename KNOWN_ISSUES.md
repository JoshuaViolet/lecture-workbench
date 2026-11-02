# Known issues and roadmap

Fixed issues are recorded in [CHANGELOG.md](CHANGELOG.md). This file lists what is still open.

## Limitations

1. **An annotation stays inside one block.** A selection that runs from one paragraph into the next keeps only the part in the first paragraph (the page says so). Supporting multi-block annotations means storing a start and end block and wrapping across them.
2. **Restoring is O(blocks × annotations) when offsets are stale.** Fine for a lecture with hundreds of annotations; a very long page with thousands could be slow on first load after an edit.
3. **The UI comes in Simplified Chinese and English only.** Another language needs a table in `framework/ui_strings.json` with the same keys, and `cli.py new --lang` gives it the English starter text.
4. **Two validator checks need Node.js**: `node --check` and the term-card audit. Without Node they are skipped and the report says so; a syntax error in a subject's own `subject_js.js` then goes unnoticed until the page is opened. Building does not need Node.
5. **Embedding is per reference.** An image used twice is embedded twice. `srcset` candidates, `<video>`, `<audio>` and CSS `url()` written in `content.html` itself (a `style` attribute or a `<style>` element; `subject_css.css` is embedded) are not; the validator lists a local one as a file the guide needs beside it.
6. **Practice results stay in one browser.** Which questions were answered wrongly is not part of the JSON backup, so it does not move to another device.
7. **Term cards open on hover or click, not from the keyboard.** The terms are not focusable, so keyboard and screen-reader users don't reach the cards.
8. **The browser tests run in Chromium only.** Firefox and Safari, on the desktop and on phones, are not tested automatically.

## Structure

9. The CLI (`framework/cli.py`: `new`, `build`, `validate`) runs from a checkout, not as an installed package. Plan: package it with the template as package data and a console-script entry point.

## Roadmap

| Next | Goal |
|---|---|
| 0.4 | Publish the CLI as a package |
| later | Optional, pluggable study assistant (OpenAI-compatible endpoint or a local model), off by default so the offline core stays dependency-free |
