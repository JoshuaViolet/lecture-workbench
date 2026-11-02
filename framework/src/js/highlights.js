// ---------- selection toolbar ----------
function handleSelection() {
    const selection = window.getSelection();
    const toolbar = document.getElementById("text-selection-toolbar");
    const addBtn = document.getElementById("add-hl-btn");
    const removeBtn = document.getElementById("remove-hl-btn");

    if (!selection || selection.isCollapsed || selection.toString().trim() === "") {
        if (!activeHighlightEl) {
            toolbar.style.display = "none";
        }
        return;
    }

    const range = selection.getRangeAt(0);
    const container = range.commonAncestorContainer;

    if (!document.getElementById("main-content").contains(container)) {
        toolbar.style.display = "none";
        return;
    }

    // copy it: the selection's own range changes as soon as focus moves to the note editor
    selectedRange = range.cloneRange();
    activeHighlightEl = null;
    addBtn.style.display = "inline-flex";
    removeBtn.style.display = "none";

    const rect = range.getBoundingClientRect();
    positionToolbar(toolbar, rect);
}

function handleDocClick(e) {
    const toolbar = document.getElementById("text-selection-toolbar");
    const term = e.target.closest(".lexi");
    // Clicking outside the term card (and not on a lexicon term) closes it
    if (!e.target.closest("#term-card") && !term) {
        hideTermCard();
    }
    if (e.target.closest("#note-editor") || e.target.closest("#text-selection-toolbar")) return;

    const flag = e.target.closest(".note-flag");
    const hlEl = e.target.closest(".user-hl");
    const noteAnchor = e.target.closest(".note-anchor");
    // Looking a term up (its own handler shows the card) leaves an open note editor alone;
    // a click on the reader's own highlight or note inside a term goes on below.
    if (term && !flag && !hlEl && !noteAnchor) return;

    // Any other click ends an open note editor; what was typed into it is kept, not thrown away
    dismissNoteEditor();

    // The 💬 flag always opens its note. Highlighted text shows the highlight toolbar even
    // inside a note, so the highlight can still be removed; other noted text opens the note.
    if (flag || (noteAnchor && !hlEl)) {
        toolbar.style.display = "none";
        activeHighlightEl = null;
        openExistingNote((flag || noteAnchor).dataset.noteId);
    } else if (hlEl) {
        showHighlightToolbar(hlEl);
    } else if (!window.getSelection() || window.getSelection().isCollapsed) {
        toolbar.style.display = "none";
        activeHighlightEl = null;
    }
}

// The toolbar for an existing highlight: remove it, or add a note to exactly its text.
function showHighlightToolbar(hlEl) {
    const pieces = document.querySelectorAll("mark.user-hl" + byId("data-hl-id", hlEl.dataset.hlId));
    activeHighlightEl = hlEl;
    selectedRange = document.createRange();
    selectedRange.setStartBefore(pieces[0]);
    selectedRange.setEndAfter(pieces[pieces.length - 1]);
    document.getElementById("add-hl-btn").style.display = "none";
    document.getElementById("remove-hl-btn").style.display = "inline-flex";
    positionToolbar(document.getElementById("text-selection-toolbar"), hlEl.getBoundingClientRect());
}

const TOOLBAR_ROOM = 46;   // the toolbar sits this far above the text it acts on

function positionToolbar(toolbar, rect) {
    toolbar.style.display = "flex";
    const top = window.scrollY + rect.top - TOOLBAR_ROOM;
    const left = window.scrollX + rect.left + (rect.width / 2) - (toolbar.offsetWidth / 2);
    const maxLeft = window.scrollX + document.documentElement.clientWidth - toolbar.offsetWidth - 10;
    toolbar.style.top = Math.max(10, top) + "px";
    toolbar.style.left = Math.min(Math.max(10, left), Math.max(10, maxLeft)) + "px";
}

function clearSelectionUI() {
    const sel = window.getSelection();
    if (sel) sel.removeAllRanges();
    document.getElementById("text-selection-toolbar").style.display = "none";
    selectedRange = null;
    activeHighlightEl = null;
}

// ---------- highlights ----------
function wrapHighlight(block, start, end, id) {
    return wrapTextRange(block, start, end, () => {
        const mark = document.createElement("mark");
        mark.className = "user-hl";
        mark.dataset.hlId = id;
        return mark;
    });
}

function applyHighlight() {
    if (!selectedRange) return;
    const res = anchorFromRange(selectedRange);
    clearSelectionUI();
    if (res.error) {
        showToast(res.error === "unsupported" ? UI.toast_hl_unsupported : UI.toast_no_selection);
        return;
    }
    const id = newId("hl");
    if (!wrapHighlight(res.block, res.anchor.start, res.anchor.end, id).length) {
        showToast(UI.toast_hl_nothing);
        return;
    }
    const record = Object.assign({ id: id }, res.anchor, { ts: Date.now() });
    if (changeList(LS.highlights, list => list.concat([record]))) {
        showToast(res.clipped ? UI.toast_hl_clipped : UI.toast_hl_saved);
    }
}

function removeHighlightAtSelection() {
    if (!activeHighlightEl) return;
    const id = activeHighlightEl.dataset.hlId;
    unwrapAll("mark.user-hl" + byId("data-hl-id", id));
    clearSelectionUI();
    if (changeList(LS.highlights, list => list.filter(h => h.id !== id))) {
        showToast(UI.toast_hl_removed);
    }
}

function restoreHighlights() {
    restoreAnnotations(loadList(LS.highlights), "data-hl-id", wrapHighlight);
}
