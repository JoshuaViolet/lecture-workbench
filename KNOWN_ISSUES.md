# Known issues and roadmap

Fixed issues are recorded in [CHANGELOG.md](CHANGELOG.md). This file lists what is still open.

## Limitations

1. **An annotation stays inside one block.** A selection that runs from one paragraph into the next keeps only the part in the first paragraph (the page says so). Supporting multi-block annotations means storing a start and end block and wrapping across them.
2. **Restoring is O(blocks × annotations) when offsets are stale.** Fine for a lecture with hundreds of annotations; a very long page with thousands could be slow on first load after an edit.
3. **The UI comes in Simplified Chinese and English only.** Another language needs a table in `framework/ui_strings.json` with the same keys. Dates in the Markdown export follow the browser's locale, not the guide's language.
4. **The validator needs Node.js** for `node --check` and the term-card audit. Building does not.

## Structure

5. The CLI (`framework/cli.py`: `new`, `build`, `validate`) runs from a checkout, not as an installed package. Plan: package it with the template as package data and a console-script entry point.

## Roadmap

| Next | Goal |
|---|---|
| 0.3 | Publish the CLI as a package |
| later | Optional, pluggable study assistant (OpenAI-compatible endpoint or a local model), off by default so the offline core stays dependency-free |
