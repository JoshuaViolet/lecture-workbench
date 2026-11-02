// ---------- Study Data Export / Import / Markdown ----------
function exportStudyData() {
    const data = {
        app: APP_ID,
        version: 2,
        exportedAt: new Date().toISOString(),
        highlights: exportableList(LS.highlights),
        notes: exportableList(LS.notes)
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = APP_ID + "_backup_" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // revoking right away can cancel the download in some browsers
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    showToast(UI.toast_exported);
}

function isAnnotation(x) {
    return x && typeof x === "object" && typeof x.id === "string" && typeof x.text === "string" && x.text;
}

// Importing asks what to do with what this browser already has: merge the backup into it
// (nothing is deleted; for a note in both, the newer edit wins) or replace it with the backup.
// With nothing here, there is nothing to choose and the backup is simply loaded.
let pendingImport = null;   // a checked backup waiting for the reader's choice

function importStudyData(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
        let data;
        try {
            data = JSON.parse(reader.result);
        } catch (e) {
            showToast(UI.toast_import_bad_json);
            return;
        }
        if (!data || (!Array.isArray(data.highlights) && !Array.isArray(data.notes))) {
            showToast(UI.toast_import_empty);
            return;
        }
        // records are checked one by one; a list the backup does not have is left alone
        const backup = {
            highlights: Array.isArray(data.highlights) ? data.highlights.filter(isAnnotation) : null,
            notes: Array.isArray(data.notes)
                ? data.notes.filter(n => isAnnotation(n) && typeof n.note === "string") : null
        };
        // backups carry the guide's app id; older backups without one are accepted
        const otherGuide = data.app && data.app !== APP_ID ? String(data.app) : null;
        const here = { highlights: readList(LS.highlights), notes: readList(LS.notes) };
        if (!here.highlights.length && !here.notes.length && !otherGuide) {
            finishImport("merge", backup);
            return;
        }
        pendingImport = backup;
        document.getElementById("import-dialog-summary").textContent = t("import_summary", {
            bh: (backup.highlights || []).length, bn: (backup.notes || []).length,
            lh: here.highlights.length, ln: here.notes.length
        });
        const warning = document.getElementById("import-dialog-warning");
        warning.textContent = otherGuide ? t("import_other_guide", { app: otherGuide }) : "";
        warning.style.display = otherGuide ? "" : "none";
        const dialog = document.getElementById("import-dialog");
        if (typeof dialog.showModal === "function") dialog.showModal();
        else dialog.setAttribute("open", "");
    };
    reader.readAsText(file);
}

// mode: "merge", "replace" or "cancel" (the dialog's buttons); backup: given when no dialog was shown
function finishImport(mode, backup) {
    backup = backup || pendingImport;
    pendingImport = null;
    const dialog = document.getElementById("import-dialog");
    if (typeof dialog.close === "function") { if (dialog.open) dialog.close(); }
    else dialog.removeAttribute("open");
    if (!backup || (mode !== "merge" && mode !== "replace")) return;

    const lists = [[LS.highlights, backup.highlights, true], [LS.notes, backup.notes, false]];
    const next = {}, changed = {};
    lists.forEach(([key, incoming, dedupe]) => {
        const current = readList(key);
        if (!incoming) {
            next[key] = current;
        } else if (mode === "replace") {
            // keep one copy of what is replaced, as with unreadable values, so a mistaken choice can be undone
            if (current.length) lsSet(key + "_before_import", JSON.stringify(current));
            next[key] = incoming;
        } else {
            const merged = mergeById(current, incoming, dedupe);
            next[key] = merged.list;
            changed[key] = merged.added + merged.updated;
        }
    });
    if (mode === "merge" && !changed[LS.highlights] && !changed[LS.notes]) {
        showToast(UI.toast_import_nothing_new);
        return;
    }
    if (!writeList(LS.highlights, next[LS.highlights]) || !writeList(LS.notes, next[LS.notes])) return;
    showToast(mode === "replace"
        ? t("toast_import_replaced", { highlights: next[LS.highlights].length, notes: next[LS.notes].length })
        : t("toast_imported", { highlights: changed[LS.highlights] || 0, notes: changed[LS.notes] || 0 }));
    setTimeout(() => location.reload(), 900);
}

function chapterTitleFor(el) {
    const sec = el ? el.closest("section") : null;
    const h2 = sec ? sec.querySelector("h2") : null;
    return h2 ? h2.textContent.trim() : null;
}

// Annotations in reading order, each with its first element on the page (null when its
// text is no longer in the guide; those go last, in the order they were made).
function inReadingOrder(list, attr) {
    return list.map((x, i) => ({ item: x, el: document.querySelector(byId(attr, x.id)), i: i }))
        .sort((a, b) => {
            if (a.el && b.el && a.el !== b.el) {
                return a.el.compareDocumentPosition(b.el) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
            }
            if (!a.el !== !b.el) return a.el ? -1 : 1;
            return a.i - b.i;
        });
}

function copyNotesAsMarkdown() {
    const notes = inReadingOrder(exportableList(LS.notes), "data-note-id");
    const hls = inReadingOrder(exportableList(LS.highlights), "data-hl-id");
    if (!notes.length && !hls.length) { showToast(UI.toast_nothing_to_copy); return; }

    let md = "# " + t("md_title", { title: GUIDE_TITLE }) + "\n\n";
    md += "> " + t("md_exported_at", { date: new Date().toLocaleString(UI.html_lang) }) + "\n\n";

    if (notes.length) {
        md += "## " + t("md_notes", { n: notes.length }) + "\n\n";
        notes.forEach(({ item: n, el }, i) => {
            const ch = chapterTitleFor(el);
            md += "### " + (ch ? t("md_note_in_chapter", { i: i + 1, chapter: ch }) : t("md_note", { i: i + 1 })) + "\n\n";
            md += "> " + t("md_quote", { text: n.text }) + "\n\n";
            md += n.note + "\n\n";
        });
    }
    if (hls.length) {
        md += "## " + t("md_highlights", { n: hls.length }) + "\n\n";
        hls.forEach(({ item: h }) => { md += "- " + h.text + "\n"; });
    }
    copyText(md, UI.toast_md_copied);
}

function copyText(text, okMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => showToast(okMsg), () => legacyCopy(text, okMsg));
    } else {
        legacyCopy(text, okMsg);
    }
}
function legacyCopy(text, okMsg) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { /* reported below */ }
    showToast(ok ? okMsg : UI.toast_copy_failed);
    document.body.removeChild(ta);
}
