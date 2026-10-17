# Writing supplement: psychology

Read the general rules in [AGENTS.md](../../AGENTS.md) first. This file only covers what psychology does differently or more specifically.

## Core block order: phenomenon → evidence → limitation

1. **Phenomenon / examinable statement**: what we observe, in the sentence a student can repeat with the book closed.
2. **Evidence**: the study design (the key manipulation or comparison) and the main result. Read the trend of a figure; never read numbers off a figure with no scale.
3. **Explanation**: which mechanism accounts for the result.
4. **Limitation (one)**: what the result does not show, and which alternative explanations remain.
5. When needed: **discrimination** (what it is most easily confused with) and **transfer** (does the mechanism still hold in a new situation).

A section does not need all five, but every core point has at least phenomenon, evidence and limitation. Do not make the history of models the default storyline; bring in a model only to explain a phenomenon or to compare evidence.

Suggested structure, with the components from [examples/](../../examples/):

```html
<h3 class="section-title" id="ch1-x">1.x Hierarchical networks (S5–7)</h3>
<h4>Phenomenon: what do we observe?</h4>
<h4>Evidence: how was it tested?</h4>
<h4>Explanation: what does the result tell us?</h4>
<h4>Limitation: what does it not tell us?</h4>
<h4>Discrimination: what is it most easily confused with?</h4>
```

## Classic studies

- A full study goes in an `article.study-card`: research question, key manipulation or comparison, main result, the explanation it supports, and what cannot be concluded.
- A study's boundary appears once, preferably in the card's "what cannot be concluded" field. When the card already states it, the body text gets no second `.limitation-block` saying the same.
- Brief evidence goes in an `evidence-block`. Do not nest evidence blocks and study cards.

Bad: open with "the timing is unverified, n = 30 is not the whole sample, correlation is not causation…" before getting to the office study.
Good: open with "schema expectations correlated with recall; the 'books' intrusion was the most common error". End the section with one line: "a correlation, not proof of how encoding works; timings not verified, so not given."

## Sources

- The lecture sets scope and exam priority. Assigned readings check definitions and background. Original studies check design, results and causal limits. Supplementary or optional readings never become course requirements on their own.
- Where you can, keep a trace from the lecture slide to the reading, the study, the guide section and the question ids. Mark anything you have not traced back to a source as unverified in your notes.
- Material only a reading covers goes in the reading supplement, not at the top of a chapter.
- Procedure details the lecture does not give (waiting times, verbatim instructions, answers to in-class activities) are left out.

## Question types (in your coverage notes, never in the stem)

| Type | Tests |
|---|---|
| Recall | definitions and terms |
| Discrimination | the difference between neighbouring concepts |
| Mechanism | how a mechanism produces the result |
| Evidence | reading a study's design and result |
| Limitation | a study's boundary; only points students actually get wrong (the lowest cell in a table, values on an unscaled figure, the direction of an effect) |
| Transfer | a new situation that the text does not contain word for word |

For each core point, aim for one discrimination, one mechanism and one transfer question. Study questions separate "the explanation it supports" from "what cannot be concluded".

## Discipline lines

- A correlation is not written as a cause. A brain region's involvement is not written as necessary or sufficient.
- No percentages read off a figure with no scale.
- Etymology follows standard linguistics, not folk etymology.
