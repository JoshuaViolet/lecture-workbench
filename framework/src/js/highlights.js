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
    const noteTarget = e.target.closest("[data-note-id]");
    const hlEl = e.target.closest(".user-hl");

    // Clicking a note anchor/flag opens its editor popover
    if (noteTarget) {
        toolbar.style.display = "none";
        activeHighlightEl = null;
        openExistingNote(noteTarget.dataset.noteId);
        return;
    }
    // Clicking outside the editor (and not on the toolbar that opened it) closes it
    if (!e.target.closest("#note-editor") && !e.target.closest("#text-selection-toolbar")) {
        closeNoteEditor();
    }
    // Clicking outside the term card (and not on a lexicon term) closes it
    if (!e.target.closest("#term-card") && !e.target.closest("span.en") && !e.target.closest("strong.lexi")) {
        hideTermCard();
    }

    if (hlEl) {
        activeHighlightEl = hlEl;
        const rect = hlEl.getBoundingClientRect();
        document.getElementById("add-hl-btn").style.display = "none";
        document.getElementById("remove-hl-btn").style.display = "inline-flex";
        positionToolbar(toolbar, rect);
    } else if (!e.target.closest("#text-selection-toolbar")) {
        if (!window.getSelection() || window.getSelection().isCollapsed) {
            toolbar.style.display = "none";
            activeHighlightEl = null;
        }
    }
}

function positionToolbar(toolbar, rect) {
    toolbar.style.display = "flex";
    const top = window.scrollY + rect.top - 46;
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
    const saved = readList(LS.highlights);
    saved.push(Object.assign({ id: id }, res.anchor));
    if (writeList(LS.highlights, saved)) {
        showToast(res.clipped ? UI.toast_hl_clipped : UI.toast_hl_saved);
    }
}

function removeHighlightAtSelection() {
    if (!activeHighlightEl) return;
    const id = activeHighlightEl.dataset.hlId;
    unwrapAll("mark.user-hl" + byId("data-hl-id", id));
    writeList(LS.highlights, readList(LS.highlights).filter(h => h.id !== id));
    document.getElementById("text-selection-toolbar").style.display = "none";
    activeHighlightEl = null;
    showToast(UI.toast_hl_removed);
}

function restoreHighlights() {
    restoreAnnotations(readList(LS.highlights), "data-hl-id", wrapHighlight);
}
