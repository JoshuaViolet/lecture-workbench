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

// Importing merges a backup into what this browser already has; it never deletes anything,
// so a backup from another device cannot wipe out the annotations made here.
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
        // backups carry the guide's app id; older backups without one are accepted
        if (data.app && data.app !== APP_ID) {
            if (!confirm(t("confirm_import_other", { app: data.app }))) return;
        }
        const hls = mergeById(readList(LS.highlights), (data.highlights || []).filter(isAnnotation), true);
        const notes = mergeById(readList(LS.notes),
            (data.notes || []).filter(n => isAnnotation(n) && typeof n.note === "string"));
        const changed = { highlights: hls.added + hls.updated, notes: notes.added + notes.updated };
        if (!changed.highlights && !changed.notes) {
            showToast(UI.toast_import_nothing_new);
            return;
        }
        if (!writeList(LS.highlights, hls.list) || !writeList(LS.notes, notes.list)) return;
        showToast(t("toast_imported", changed));
        setTimeout(() => location.reload(), 900);
    };
    reader.readAsText(file);
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
