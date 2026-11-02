// ==========================================
// HIGHLIGHTS AND MARGIN NOTES
//
// An annotation is stored as { id, v, cIdx, start, end, text, prefix, suffix }:
//   cIdx         index of its block (p, li, dd, pre, ...) among all blocks in <main>
//   v            which version of the block list cIdx counts in (BLOCK_SELECTORS below)
//   start, end   character offsets into that block's text
//   text         the exact annotated text, with up to CONTEXT_CHARS of prefix/suffix
// Restoring trusts the offsets only while they still yield `text`; otherwise it
// searches every block for `text` and keeps the occurrence whose context matches best
// (the same idea as the W3C Web Annotation TextPosition + TextQuote selectors).
// The range may cross inline markup such as <strong> or term spans: every text node
// in it gets its own wrapper element, and all wrappers share the annotation's id.
// Records from older versions ({ cIdx, text } only) restore through the search path.
// ==========================================

// The elements an annotation can live in, by version. Adding a kind of block renumbers the
// blocks after it, so a record keeps the version it was made with and its cIdx is read in
// that version's list. Records without v are version 1.
const BLOCK_SELECTORS = {
    1: "p, li, td, th, div.quiz-q, div.quiz-a, figcaption, blockquote, h2, h3, h4",
    // the chapter spine and study cards (dt, dd) and code (pre; not a question's code, which
    // is redrawn on every render)
    2: "p, li, td, th, dt, dd, pre:not(.mcq-code), div.quiz-q, div.quiz-a, figcaption, blockquote, h2, h3, h4"
};
const BLOCK_VERSION = 2;
const BLOCK_SELECTOR = BLOCK_SELECTORS[BLOCK_VERSION];
const CONTEXT_CHARS = 32;
let selectedRange = null;
let activeHighlightEl = null;

document.addEventListener("selectionchange", handleSelection);
document.addEventListener("click", handleDocClick);

function getAllTextContainers(version) {
    const main = document.getElementById("main-content");
    return Array.from(main.querySelectorAll(BLOCK_SELECTORS[version || BLOCK_VERSION]));
}
