// ---------- Study Data Export / Import / Markdown ----------
function exportStudyData() {
    const data = {
        app: APP_ID,
        version: 2,
        exportedAt: new Date().toISOString(),
        highlights: readList(LS.highlights),
        notes: readList(LS.notes)
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
    showToast("📤 已导出高亮与批注备份文件！");
}

function isAnnotation(x) {
    return x && typeof x === "object" && typeof x.id === "string" && typeof x.text === "string" && x.text;
}

function importStudyData(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
        let data;
        try {
            data = JSON.parse(reader.result);
        } catch (e) {
            showToast("⚠️ 导入失败：文件不是有效的 JSON。");
            return;
        }
        if (!data || (!Array.isArray(data.highlights) && !Array.isArray(data.notes))) {
            showToast("⚠️ 导入失败：文件里没有高亮或批注。");
            return;
        }
        // backups carry the guide's app id; older backups without one are accepted
        if (data.app && data.app !== APP_ID) {
            if (!confirm("⚠️ 这份备份来自另一个文档（" + data.app + "）。\n导入它可能导致高亮/批注错位。\n仍要继续吗？")) return;
        }
        const hls = (data.highlights || []).filter(isAnnotation);
        const notes = (data.notes || []).filter(n => isAnnotation(n) && typeof n.note === "string");
        const ok = (!Array.isArray(data.highlights) || writeList(LS.highlights, hls))
            && (!Array.isArray(data.notes) || writeList(LS.notes, notes));
        if (!ok) return;
        showToast("📥 已导入 " + hls.length + " 条高亮、" + notes.length + " 条批注，正在刷新页面...");
        setTimeout(() => location.reload(), 900);
    };
    reader.readAsText(file);
}

function chapterTitleFor(selector) {
    const el = document.querySelector(selector);
    const sec = el ? el.closest("section") : null;
    const h2 = sec ? sec.querySelector("h2") : null;
    return h2 ? h2.textContent.trim() : null;
}

function copyNotesAsMarkdown() {
    const notes = readList(LS.notes);
    const hls = readList(LS.highlights);
    if (!notes.length && !hls.length) { showToast("⚠️ 还没有任何批注或高亮。"); return; }

    let md = "# " + GUIDE_TITLE + " · 我的批注与高亮\n\n";
    md += "> 导出于 " + new Date().toLocaleString() + "\n\n";

    if (notes.length) {
        md += "## 📝 我的批注（" + notes.length + " 条）\n\n";
        notes.forEach((n, i) => {
            const ch = chapterTitleFor(".note-anchor" + byId("data-note-id", n.id));
            md += "### 批注 " + (i + 1) + (ch ? "｜" + ch : "") + "\n\n";
            md += "> 原文：" + n.text + "\n\n";
            md += n.note + "\n\n";
        });
    }
    if (hls.length) {
        md += "## 🖍️ 高亮摘记（" + hls.length + " 条）\n\n";
        hls.forEach(h => { md += "- " + h.text + "\n"; });
    }
    copyText(md, "📋 已复制 Markdown！");
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
    try { document.execCommand("copy"); showToast(okMsg); }
    catch (e) { showToast("⚠️ 复制失败，请手动选择复制。"); }
    document.body.removeChild(ta);
}
