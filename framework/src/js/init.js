// Initialize immediately — this <script> is at the end of <body>, so the DOM is already parsed.
// (window.onload would needlessly wait for all lazy-loaded slide images before restoring highlights.)
(function initApp() {
    wrapTables();
    updateFC();
    initMCQ();
    restoreHighlights();
    restoreNotes();
    updateNoteCount();
    initTermCards();
    initA11y();
    initScrollSpy();
    // On narrow screens the sidebar starts hidden — the pill should read "open", not "collapse"
    if (window.innerWidth <= 900) {
        const pillIcon = document.getElementById("sidebar-pill-icon");
        const pillText = document.getElementById("sidebar-pill-text");
        if (pillIcon && pillText) {
            pillIcon.textContent = "☰";
            pillText.textContent = UI.sidebar_short;
        }
    }
})();
