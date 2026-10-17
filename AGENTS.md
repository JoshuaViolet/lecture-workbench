# Writing a study guide

Rules for whoever writes a subject's `content.html` and `data.json`, a person or an AI assistant. For changes to the engine itself, see [docs/architecture.md](docs/architecture.md).

A guide is a handout for preparing for and following a lecture, not an audit report. These rules apply to every subject. Each discipline adds a supplement that sets the order in which a core block unfolds and the question types it uses; where the two disagree, the supplement wins on order and question types.

## Discipline supplements

Read this file first, then the supplement for your subject.

| Discipline | Supplement | Core block order |
|---|---|---|
| Psychology | [docs/writing/psychology.md](docs/writing/psychology.md) | phenomenon → evidence → limitation (plus discrimination or transfer when needed) |
| Economics | [docs/writing/economics.md](docs/writing/economics.md) | assumptions → derivation → worked numbers → curve shifts → policy → model limitation |
| Data science and programming | [docs/writing/data-science.md](docs/writing/data-science.md) | concept → code → actual output → common errors → rewrite exercise |

For a new discipline, start from the closest supplement. If it differs a lot, add `docs/writing/<discipline>.md` and list it in the table above.

## Each core block

1. One examinable statement, the sentence a student can repeat with the book closed. It is always the first paragraph.
2. The body, in the order the supplement sets.
3. One limitation or boundary: what cannot be concluded, where the model breaks, where the code fails.
4. A discrimination (what it is most often confused with) or a transfer (a new situation), only when needed.

Do not open every subsection with a pile of caveats ("unverified", "cannot conclude", "not causal") before getting to the topic. Do not wrap every `h3` in a `limitation-block` to make coverage look thorough. State each boundary once: if a study card or a model-limitation block already says it, the body text does not repeat it.

## Headings

- `h2` is a chapter and `h3` a subsection. These are HTML heading levels, not new components.
- The visible text of every `h2` and `h3` carries its slide reference, e.g. `4.2 Hierarchical networks (S5–7)`.
- A question-style subtitle is fine, but it does not replace the slide reference.

## What goes in the guide, and what stays out

Only in `content.html`: explanation, evidence or derivation, figures, code, one limitation, and the English terms needed to follow the lecture.

Keep out of the built page, in your own notes next to the subject: coverage tables, long citation lists, lists of numbers or samples you have not verified, generation logs. Never embed a coverage table or a source index in the guide.

## Scope

- The lecture slides set the main line and the exam priority.
- Assigned readings go in a "Reading supplement" section, on its own or collapsed. They do not open a chapter.
- Do not write details the lecture does not have, and do not spend half a page explaining why something is left out.

## Questions

These apply to `mcqData` in `data.json`.

- 12–24 questions per lecture. Favour the core learning outcomes: discrimination, mechanism, transfer. Definition questions are at most 30%. Each supplement lists its question types.
- Not three questions per slide line. Limitation questions only target points students actually get wrong.
- Question types are tracked in your coverage notes, never in the stem: no tags such as `Mechanism:` or `[Transfer]`. A question id prefix such as `T01-Q01｜` is fine.
- Distractors come from real misconceptions and are as long and as specific as the correct option. The correct option may be the only longest one in at most 40% of questions (chance is about 25% with four options); above that, students can score by picking the longest without reading the stem.
- Options are shuffled every time the page renders. In `exp`, refer to an option by its content, never as A/B/C/D. A question whose order must stay fixed (for example "all of the above") sets `"shuffle": false`.
- Put the code a question is about in its `code` field; it is shown in a monospace block exactly as written. A multi-line option is written with line breaks (`\n`) in the string and is shown as code.
- The validator warns about the last three rules (longest option, type tags in stems, letters in explanations). Fix the warnings before you hand the guide over, or explain why they stay.

## Never

Invent numbers, code output or study details you have not checked; write a correlation as a cause; read values off a chart that has no scale. Each supplement adds its own lines.
