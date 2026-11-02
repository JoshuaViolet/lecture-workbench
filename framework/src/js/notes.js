// ==========================================
// IN-PAGE MARGIN NOTES
// ==========================================
let editingNoteId = null;   // null => creating a brand-new note
let pendingNoteRange = null;
let noteDraftStart = "";    // the editor's text when it opened, to tell whether anything was typed

function noteList() {
    return pageList(LS.notes);
}
function updateNoteCount() {
    const el = document.getElementById("note-count");
    if (el) el.textContent = noteList().length;
}
function changeNotes(change) {
    const ok = changeList(LS.notes, change);
    updateNoteCount();
    return ok;
}

function wrapNote(block, start, end, id) {
    const pieces = wrapTextRange(block, start, end, () => {
        const span = document.createElement("span");
        span.className = "note-anchor";
        span.dataset.noteId = id;
        return span;
    });
    if (pieces.length) appendNoteFlag(pieces[pieces.length - 1], id);
    return pieces;
}

// Called from the selection toolbar (note button)
function openNoteEditor() {
    if (!selectedRange || selectedRange.toString().trim() === "") {
        showToast(UI.toast_note_select_first);
        return;
    }
    const range = selectedRange;
    dismissNoteEditor();
    editingNoteId = null;
    pendingNoteRange = range;
    setNoteEditorText("");
    document.getElementById("note-delete-btn").style.display = "none";
    document.getElementById("text-selection-toolbar").style.display = "none";
    showNoteEditorAt(pendingNoteRange.getBoundingClientRect());
}

// Called when clicking an existing note
function openExistingNote(noteId) {
    dismissNoteEditor();
    const n = noteList().find(x => x.id === noteId);
    if (!n) return;
    editingNoteId = noteId;
    pendingNoteRange = null;
    setNoteEditorText(n.note);
    document.getElementById("note-delete-btn").style.display = "";
    document.getElementById("text-selection-toolbar").style.display = "none";
    const anchor = document.querySelector(".note-anchor" + byId("data-note-id", noteId));
    if (anchor) showNoteEditorAt(anchor.getBoundingClientRect());
}

function setNoteEditorText(text) {
    document.getElementById("note-editor-text").value = text;
    noteDraftStart = text;
}

function showNoteEditorAt(rect) {
    const ed = document.getElementById("note-editor");
    ed.style.display = "block";
    const top = window.scrollY + rect.bottom + 8;
    const left = window.scrollX + rect.left;
    const maxLeft = window.scrollX + document.documentElement.clientWidth - ed.offsetWidth - 10;
    ed.style.top = Math.max(10, top) + "px";
    ed.style.left = Math.min(Math.max(10, left), Math.max(10, maxLeft)) + "px";
    setTimeout(() => document.getElementById("note-editor-text").focus(), 30);
}

// Cancel / Escape: close and discard what was typed.
function closeNoteEditor() {
    const ed = document.getElementById("note-editor");
    if (ed) ed.style.display = "none";
    editingNoteId = null;
    pendingNoteRange = null;
}

// A click elsewhere: close, but save anything that was typed rather than lose it.
function dismissNoteEditor() {
    const ed = document.getElementById("note-editor");
    if (!ed || ed.style.display !== "block") return;
    const text = document.getElementById("note-editor-text").value;
    if (text.trim() && text !== noteDraftStart) saveNote(true);
    else closeNoteEditor();
}

// keepSelection: when saving because of a click elsewhere, leave the page's new selection alone.
function saveNote(keepSelection) {
    const noteText = document.getElementById("note-editor-text").value.trim();
    if (!noteText) { showToast(UI.toast_note_empty); return; }
    const ts = Date.now();

    // Edit path: update in place, no DOM re-anchoring needed
    if (editingNoteId) {
        const id = editingNoteId;
        const mine = noteList().find(x => x.id === id);
        const edited = n => Object.assign({}, n, { note: noteText, ts: ts });
        // if another tab deleted this note meanwhile, the edit brings it back rather than vanishing
        const edit = list => list.some(n => n.id === id)
            ? list.map(n => (n.id === id ? edited(n) : n))
            : list.concat(mine ? [edited(mine)] : []);
        if (changeNotes(edit)) showToast(UI.toast_note_updated);
        closeNoteEditor();
        return;
    }

    // Create path: anchor the selected text
    if (!pendingNoteRange) { closeNoteEditor(); return; }
    const res = anchorFromRange(pendingNoteRange);
    if (keepSelection !== true) clearSelectionUI();
    if (res.error) {
        showToast(res.error === "unsupported" ? UI.toast_note_unsupported : UI.toast_no_selection);
        closeNoteEditor();
        return;
    }
    const id = newId("note");
    if (wrapNote(res.block, res.anchor.start, res.anchor.end, id).length) {
        const record = Object.assign({ id: id }, res.anchor, { note: noteText, ts: ts });
        if (changeNotes(list => list.concat([record]))) {
            showToast(res.clipped ? UI.toast_note_clipped : UI.toast_note_saved);
        }
    } else {
        showToast(UI.toast_note_nothing);
    }
    closeNoteEditor();
}

function deleteNote() {
    if (!editingNoteId) return;
    const id = editingNoteId;
    document.querySelectorAll(".note-flag" + byId("data-note-id", id)).forEach(f => f.remove());
    unwrapAll(".note-anchor" + byId("data-note-id", id));
    closeNoteEditor();
    if (changeNotes(list => list.filter(n => n.id !== id))) showToast(UI.toast_note_deleted);
}

function appendNoteFlag(span, noteId) {
    const flag = document.createElement("sup");
    flag.className = "note-flag";
    flag.textContent = "💬";
    flag.dataset.noteId = noteId;
    flag.title = UI.note_flag_title;
    span.appendChild(flag);
}

function restoreNotes() {
    restoreAnnotations(loadList(LS.notes), "data-note-id", wrapNote);
}

// Ctrl+Enter / ⌘+Enter saves from the keyboard
document.getElementById("note-editor-text").addEventListener("keydown", e => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        saveNote();
    }
});
