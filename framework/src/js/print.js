// ==========================================
// PRINT SHEET (beforeprint 生成自测清单 + 强制图片加载)
// ==========================================
function buildPrintSheet() {
    document.querySelectorAll("#print-sheet").forEach(el => el.remove());
    let html = '<h2>' + escapeHtml(UI.print_title) + '</h2>';
    html += '<h3>' + escapeHtml(t("print_flashcards", { n: flashcards.length })) + '</h3><ol>';
    flashcards.forEach(c => {
        html += '<li style="margin-bottom:8px;"><strong>Q:</strong> ' + escapeHtml(c.front) + '<br><strong>A:</strong> ' + escapeHtml(c.back) + '</li>';
    });
    html += '</ol><h3>' + escapeHtml(t("print_mcq", { n: mcqData.length })) + '</h3><ol>';
    mcqData.forEach(m => {
        // options are shuffled on screen, so print the answer text rather than a letter
        const code = m.code ? '<pre class="mcq-code"><code>' + escapeHtml(m.code) + '</code></pre>' : '<br>';
        html += '<li style="margin-bottom:8px;"><span style="white-space:pre-wrap;">' + escapeHtml(m.q) + '</span>' + code
            + '<strong>✓</strong> <span style="white-space:pre-wrap;">' + escapeHtml(m.opts[m.ans]) + '</span><br><span style="color:#444;">' + m.exp + '</span></li>';
    });
    html += '</ol>';
    const sheet = document.createElement("div");
    sheet.id = "print-sheet";
    sheet.className = "print-only";
    sheet.innerHTML = html;
    document.getElementById("main-content").appendChild(sheet);
}

window.addEventListener("beforeprint", () => {
    buildPrintSheet();
    // 懒加载图片在打印前全部强制加载，否则未滚动到的幻灯片会打印空白
    document.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = "eager"; });
});
window.addEventListener("afterprint", () => {
    const el = document.getElementById("print-sheet");
    if (el) el.remove();
});
