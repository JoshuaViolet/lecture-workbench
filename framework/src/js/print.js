// ==========================================
// PRINT SHEET (beforeprint 生成自测清单 + 强制图片加载 + 展开折叠内容)
// ==========================================
// The self-test appendix lists the flashcards and the questions with their answers; a guide
// without either prints no appendix.
function buildPrintSheet() {
    document.querySelectorAll("#print-sheet").forEach(el => el.remove());
    if (!flashcards.length && !mcqData.length) return;
    let html = '<h2>' + escapeHtml(UI.print_title) + '</h2>';
    if (flashcards.length) {
        html += '<h3>' + escapeHtml(t("print_flashcards", { n: flashcards.length })) + '</h3><ol>';
        flashcards.forEach(c => {
            html += '<li style="margin-bottom:8px;"><strong>Q:</strong> ' + escapeHtml(c.front) + '<br><strong>A:</strong> ' + escapeHtml(c.back) + '</li>';
        });
        html += '</ol>';
    }
    if (mcqData.length) {
        html += '<h3>' + escapeHtml(t("print_mcq", { n: mcqData.length })) + '</h3><ol>';
        mcqData.forEach(m => {
            // options are shuffled on screen, so print the answer text rather than a letter
            const code = m.code ? '<pre class="mcq-code"><code>' + escapeHtml(m.code) + '</code></pre>' : '<br>';
            const fig = m.fig ? '<figure class="mcq-fig"><img src="' + escapeHtml(m.fig) + '" alt="' + escapeHtml(m.fig_alt || "") + '"></figure>' : '';
            html += '<li style="margin-bottom:8px;"><span style="white-space:pre-wrap;">' + escapeHtml(m.q) + '</span>' + fig + code
                + '<strong>✓</strong> <span style="white-space:pre-wrap;">' + escapeHtml(m.opts[m.ans]) + '</span><br><span style="color:#444;">' + m.exp + '</span></li>';
        });
        html += '</ol>';
    }
    const sheet = document.createElement("div");
    sheet.id = "print-sheet";
    sheet.className = "print-only";
    sheet.innerHTML = html;
    document.getElementById("main-content").appendChild(sheet);
}

// Collapsed <details> (a reading supplement, say) print open, like the answers of the
// inline checks; afterwards they close again.
function openDetailsForPrint() {
    document.querySelectorAll("#main-content details:not([open])").forEach(d => {
        d.open = true;
        d.dataset.printOpened = "";
    });
}
function closeDetailsAfterPrint() {
    document.querySelectorAll("#main-content details[data-print-opened]").forEach(d => {
        d.open = false;
        delete d.dataset.printOpened;
    });
}

window.addEventListener("beforeprint", () => {
    buildPrintSheet();
    openDetailsForPrint();
    // 懒加载图片在打印前全部强制加载，否则未滚动到的幻灯片会打印空白
    document.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = "eager"; });
});
window.addEventListener("afterprint", () => {
    const el = document.getElementById("print-sheet");
    if (el) el.remove();
    closeDetailsAfterPrint();
});
