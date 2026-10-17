# Writing supplement: data science and programming

Read the general rules in [AGENTS.md](../../AGENTS.md) first. This file only covers what programming subjects do differently or more specifically.

## Core block order: concept → code → actual output → common errors → rewrite exercise

Open with an examinable statement as usual (for example, "slicing gives a new list; the original list is unchanged"), then follow this order. A section does not need all five steps, but a section that teaches syntax or a function has at least concept, code and actual output.

1. **Concept**: what the syntax or function does, and whether it changes state (variables, mutable objects). Use the slides' English terms.
2. **Code**: a minimal runnable snippet in `<pre><code>`, indented with 4 spaces. Prefer the slides' own code and say where it is from (for example "Lecture 3A, S11"). Escape `<`, `>` and `&` in the HTML.
3. **Actual output**: only output printed on the slides or produced by actually running the code, and say which ("the slides show…" / "running it prints…"). No output you have not run; no invented REPL sessions.
4. **Common errors**: the real exception type and the last line of its message (for example `IndexError: list index out of range`), why it happens and how to fix it. Error messages also come from the slides or a real run.
5. **Rewrite exercise**: a small change to make (different data, a different condition, turn it into a function, another way to write it), with the answer folded in a `quiz-card`. Do not publish answers to tutorials, assignments or live quizzes.

## Question types (in your coverage notes, never in the stem)

| Type | Tests |
|---|---|
| Predict output | tracing code to its output or a variable's final value |
| Find the bug | which line fails, with which error, and why |
| Rewrite | which rewrite is equivalent to the original, or fixes the bug |
| Discrimination | mutable vs immutable, return value vs side effect, `==` vs `is`, and similar |
| Data judgement | data formats, data quality, choosing how to read or write a file |

- Definition questions are at most 30%; reading code, finding bugs and rewriting make up at least half.
- Put a question's code in its `code` field; it is shown in a monospace block exactly as written. A multi-line option has line breaks (`\n`) in its string and is shown as code automatically. The demo's last question is an example.
- Distractors in predict-output questions come from real misunderstandings (off-by-one, thinking a string method changes the string in place, thinking `else` always runs). Run the code to check the correct output.

## Discipline lines

- Code output and error messages come from the slides or a real run, never invented.
- The lecture sets the scope; material from more advanced courses stays out of the body.
