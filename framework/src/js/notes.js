// ==========================================
// IN-PAGE MARGIN NOTES (ANNOTATIONS) + STUDY DATA EXPORT/IMPORT
// ==========================================
let notesCache = [];
let editingNoteId = null;   // null => creating a brand-new note
let pendingNoteRange = null;

function loadNotes() {
    notesCache = readList(LS.notes);
}
function saveNotes() {
    const ok = writeList(LS.notes, notesCache);
    updateNoteCount();
    return ok;
}
function updateNoteCount() {
    const el = document.getElementById("note-count");
    if (el) el.textContent = notesCache.length;
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

// Called from the selection toolbar ("📝 批注" button)
function openNoteEditor() {
    if (!selectedRange || selectedRange.toString().trim() === "") {
        showToast("⚠️ 请先在正文中划选要批注的文字。");
        return;
    }
    editingNoteId = null;
    pendingNoteRange = selectedRange;
    document.getElementById("note-editor-text").value = "";
    document.getElementById("note-delete-btn").style.display = "none";
    document.getElementById("text-selection-toolbar").style.display = "none";
    showNoteEditorAt(pendingNoteRange.getBoundingClientRect());
}

// Called when clicking an existing 💬 anchor
function openExistingNote(noteId) {
    const n = notesCache.find(x => x.id === noteId);
    if (!n) return;
    editingNoteId = noteId;
    pendingNoteRange = null;
    document.getElementById("note-editor-text").value = n.note;
    document.getElementById("note-delete-btn").style.display = "";
    document.getElementById("text-selection-toolbar").style.display = "none";
    const anchor = document.querySelector(".note-anchor" + byId("data-note-id", noteId));
    if (anchor) showNoteEditorAt(anchor.getBoundingClientRect());
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

function closeNoteEditor() {
    const ed = document.getElementById("note-editor");
    if (ed) ed.style.display = "none";
    editingNoteId = null;
    pendingNoteRange = null;
}

function saveNote() {
    const noteText = document.getElementById("note-editor-text").value.trim();
    if (!noteText) { showToast("⚠️ 批注内容为空，未保存。"); return; }

    // Edit path: update in place, no DOM re-anchoring needed
    if (editingNoteId) {
        const n = notesCache.find(x => x.id === editingNoteId);
        if (n) {
            n.note = noteText;
            n.ts = Date.now();
            if (saveNotes()) showToast("💾 批注已更新！");
        }
        closeNoteEditor();
        return;
    }

    // Create path: anchor the selected text
    if (!pendingNoteRange) { closeNoteEditor(); return; }
    const res = anchorFromRange(pendingNoteRange);
    clearSelectionUI();
    if (res.error) {
        showToast(res.error === "unsupported" ? "⚠️ 该区域（如按钮/选项）暂不支持批注。" : "⚠️ 没有选中文字。");
        closeNoteEditor();
        return;
    }
    const id = newId("note");
    if (wrapNote(res.block, res.anchor.start, res.anchor.end, id).length) {
        notesCache.push(Object.assign({ id: id }, res.anchor, { note: noteText, ts: Date.now() }));
        if (saveNotes()) {
            showToast(res.clipped ? "📝 批注已保存（跨段落的选区只保留了第一段）" : "📝 批注已保存（请定期从左侧目录底部导出备份）！");
        }
    } else {
        showToast("⚠️ 没有可批注的文字。");
    }
    closeNoteEditor();
}

function deleteNote() {
    if (!editingNoteId) return;
    const id = editingNoteId;
    notesCache = notesCache.filter(n => n.id !== id);
    saveNotes();
    document.querySelectorAll(".note-flag" + byId("data-note-id", id)).forEach(f => f.remove());
    unwrapAll(".note-anchor" + byId("data-note-id", id));
    showToast("🗑️ 批注已删除！");
    closeNoteEditor();
}

function appendNoteFlag(span, noteId) {
    const flag = document.createElement("sup");
    flag.className = "note-flag";
    flag.textContent = "💬";
    flag.dataset.noteId = noteId;
    flag.title = "查看/编辑批注";
    span.appendChild(flag);
}

function restoreNotes() {
    restoreAnnotations(notesCache, "data-note-id", wrapNote);
}
