// ==========================================
// HIGHLIGHTS AND MARGIN NOTES
//
// An annotation is stored as { id, cIdx, start, end, text, prefix, suffix }:
//   cIdx         index of its block (p, li, td, ...) among all blocks in <main>
//   start, end   character offsets into that block's text
//   text         the exact annotated text, with up to CONTEXT_CHARS of prefix/suffix
// Restoring trusts the offsets only while they still yield `text`; otherwise it
// searches every block for `text` and keeps the occurrence whose context matches best
// (the same idea as the W3C Web Annotation TextPosition + TextQuote selectors).
// The range may cross inline markup such as <strong> or term spans: every text node
// in it gets its own wrapper element, and all wrappers share the annotation's id.
// Records from older versions ({ cIdx, text } only) restore through the search path.
// ==========================================
const BLOCK_SELECTOR = "p, li, td, th, div.quiz-q, div.quiz-a, figcaption, blockquote, h2, h3, h4";
const CONTEXT_CHARS = 32;
let selectedRange = null;
let activeHighlightEl = null;

document.addEventListener("selectionchange", handleSelection);
document.addEventListener("click", handleDocClick);

function getAllTextContainers() {
    return Array.from(document.querySelectorAll("#main-content p, #main-content li, #main-content td, #main-content th, #main-content div.quiz-q, #main-content div.quiz-a, #main-content figcaption, #main-content blockquote, #main-content h2, #main-content h3, #main-content h4"));
}
